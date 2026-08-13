import concurrent.futures
import time
from threading import Lock

from django.contrib.auth.models import User
from django.db import OperationalError, close_old_connections
from django.test import TransactionTestCase, override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from batches.models import Batch


class BatchAPITestCase(TransactionTestCase):
    """
    API tests for the Batch Tracking System.
    
    TransactionTestCase is used instead of TestCase because the
    concurrency test requires independent database transactions.
    """

    reset_sequences = True
    
    # Use in-memory SQLite with WAL mode for better concurrency
    @override_settings(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
                'OPTIONS': {
                    'timeout': 20,  # Wait up to 20 seconds for locks
                },
            }
        }
    )
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        self.client = APIClient()

        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": "testuser",
                "password": "testpass123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Token creation failed: {response.data}",
        )

        self.token = response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.token}"
        )

    def test_create_batch_success(self):
        """A valid batch should be created successfully."""

        data = {
            "sample_id": "SAMPLE001",
            "batch_type": "Blood Panel",
            "submitted_by": "Dr. Smith",
        }

        response = self.client.post(
            "/api/batches/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Batch.objects.count(),
            1,
        )

        batch = Batch.objects.get()

        self.assertEqual(
            batch.sample_id,
            "SAMPLE001",
        )

        self.assertEqual(
            batch.status,
            "queued",
        )

    def test_create_batch_idempotent(self):
        """
        Repeating the same request with the same sample_id
        must not create a duplicate batch.
        """

        data = {
            "sample_id": "SAMPLE002",
            "batch_type": "Blood Panel",
            "submitted_by": "Dr. Smith",
        }

        first_response = self.client.post(
            "/api/batches/",
            data,
            format="json",
        )

        second_response = self.client.post(
            "/api/batches/",
            data,
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            Batch.objects.filter(
                sample_id="SAMPLE002"
            ).count(),
            1,
        )

    def test_status_transition_invalid(self):
        """
        A completed batch must not be allowed to move back
        to processing.
        """

        batch = Batch.objects.create(
            sample_id="SAMPLE003",
            batch_type="Blood Panel",
            submitted_by="Dr. Smith",
            status="completed",
        )

        response = self.client.patch(
            f"/api/batches/{batch.id}/status/",
            {"status": "processing"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        batch.refresh_from_db()

        self.assertEqual(
            batch.status,
            "completed",
        )

    def test_concurrent_updates(self):
        """
        Two simultaneous requests attempting to move the same
        batch from queued -> processing must not both succeed.

        Expected:
            Request 1 -> 200
            Request 2 -> 400

        Final state:
            processing
        """

        batch = Batch.objects.create(
            sample_id="SAMPLE004",
            batch_type="Blood Panel",
            submitted_by="Dr. Smith",
            status="queued",
        )

        # Use a lock to ensure both threads don't start exactly at the same time
        # which can cause SQLite to lock up completely
        start_lock = Lock()
        start_lock.acquire()
        
        results = []
        
        def update_batch(thread_id):
            """
            Execute one status update using an independent
            database connection.
            """
            
            # Wait for both threads to be ready
            start_lock.acquire()
            start_lock.release()
            
            close_old_connections()

            try:
                # Create a new client for this thread
                client = APIClient()

                # Use force_authenticate to avoid auth DB queries
                client.force_authenticate(
                    user=self.user
                )

                # Retry logic for SQLite locked database
                for attempt in range(5):
                    try:
                        response = client.patch(
                            f"/api/batches/{batch.id}/status/",
                            {"status": "processing"},
                            format="json",
                        )
                        results.append(response)
                        return response

                    except OperationalError as exc:
                        if "locked" not in str(exc).lower():
                            raise

                        if attempt == 4:
                            raise

                        # Exponential backoff
                        wait_time = 0.1 * (2 ** attempt)
                        time.sleep(wait_time)

                    except Exception as e:
                        # Catch any other exceptions and return as error
                        from rest_framework.response import Response
                        results.append(Response(
                            {'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        ))
                        return results[-1]

            finally:
                close_old_connections()
            
            return None

        # Start both threads
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=2
        ) as executor:
            
            # Submit both tasks
            future1 = executor.submit(update_batch, 1)
            future2 = executor.submit(update_batch, 2)
            
            # Release the lock to start both threads simultaneously
            start_lock.release()
            
            # Wait for both to complete
            future1.result()
            future2.result()
            
            # Wait a bit for any pending operations
            time.sleep(0.5)

        # Collect results from both threads
        response_statuses = []
        for result in results:
            if result is not None:
                response_statuses.append(result.status_code)
        
        # If we got fewer than 2 responses, something went wrong
        if len(response_statuses) < 2:
            # Try to get the batch state
            batch.refresh_from_db()
            self.fail(
                f"Only {len(response_statuses)} responses received. "
                f"Batch status: {batch.status}, Results: {response_statuses}"
            )

        # Exactly one request should perform: queued -> processing
        self.assertEqual(
            response_statuses.count(status.HTTP_200_OK),
            1,
            msg=f"Unexpected responses: {response_statuses}",
        )

        # The second request must be rejected because the batch is no longer queued
        self.assertEqual(
            response_statuses.count(status.HTTP_400_BAD_REQUEST),
            1,
            msg=f"Unexpected responses: {response_statuses}",
        )

        # Verify final state
        batch.refresh_from_db()
        self.assertEqual(
            batch.status,
            "processing",
        )

    def test_authentication_failure(self):
        """
        Requests without authentication must be rejected.
        """

        client = APIClient()

        response = client.get(
            "/api/batches/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )