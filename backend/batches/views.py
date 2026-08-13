from django.shortcuts import render

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.db.models import Q
from django.core.cache import cache
from django.core.exceptions import ValidationError
import requests
import logging
from .models import Batch
from .serializers import (
    BatchSerializer, BatchCreateSerializer, BatchStatusUpdateSerializer
)
from .utils import retry_on_failure

logger = logging.getLogger(__name__)

class BatchPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all().order_by('-created_at')
    serializer_class = BatchSerializer
    pagination_class = BatchPagination
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BatchCreateSerializer
        return BatchSerializer
    
    def create(self, request, *args, **kwargs):
        # Idempotent creation using sample_id as idempotency key
        sample_id = request.data.get('sample_id')
        if sample_id:
            existing = Batch.objects.filter(sample_id=sample_id).first()
            if existing:
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)
        
        return super().create(request, *args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        # Filtering by status and type
        queryset = self.get_queryset()
        
        status_filter = request.query_params.get('status')
        type_filter = request.query_params.get('type')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if type_filter:
            queryset = queryset.filter(batch_type=type_filter)
        
        # Cache for frequently used filters (optional)
        cache_key = f"batch_list_{status_filter}_{type_filter}_{request.query_params.get('page')}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return Response(cached_result)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            cache.set(cache_key, result.data, 60)  # Cache for 60 seconds
            return result
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    # @action(detail=True, methods=['patch'])
    # def status(self, request, pk=None):
    #     batch = self.get_object()
    #     serializer = BatchStatusUpdateSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
        
    #     try:
    #         # Use select_for_update for row-level locking
    #         with transaction.atomic():
    #             batch = Batch.objects.select_for_update().get(pk=batch.pk)
    #             batch.update_status(serializer.validated_data['status'])
    #             return Response(BatchSerializer(batch).data)
    #     except ValidationError as e:
    #         return Response(
    #             {'error': str(e)},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )
    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        batch = self.get_object()
        serializer = BatchStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Use a simpler approach for SQLite compatibility
            # Instead of select_for_update which doesn't work well with SQLite
            with transaction.atomic():
                # Refresh the batch with locking
                batch = Batch.objects.select_for_update().get(pk=batch.pk)
                
                # Check if transition is valid
                if not batch.can_transition_to(serializer.validated_data['status']):
                    return Response(
                        {'error': f'Invalid status transition from {batch.status} to {serializer.validated_data["status"]}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Update the status
                batch.status = serializer.validated_data['status']
                batch.save(update_fields=['status', 'updated_at'])
                
                return Response(BatchSerializer(batch).data)
                
        except Batch.DoesNotExist:
            return Response(
                {'error': 'Batch not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    @retry_on_failure(max_retries=3, backoff_factor=2)
    def notify(self, request, pk=None):
        batch = self.get_object()
        partner_url = batch.partner_webhook
        
        if not partner_url:
            return Response(
                {'error': 'No partner webhook configured'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            response = requests.post(
                partner_url,
                json={
                    'batch_id': batch.id,
                    'sample_id': batch.sample_id,
                    'status': batch.status,
                    'result': batch.result
                },
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            return Response({
                'sent': True,
                'status_code': response.status_code
            })
        except requests.RequestException as e:
            logger.error(f"Webhook notification failed: {str(e)}")
            # Will be retried by decorator
            raise