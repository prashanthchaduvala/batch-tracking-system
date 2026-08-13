# Diagnostic Batch Tracking System

A full-stack diagnostic batch tracking application built with Django REST Framework and React (Vite).

The system provides JWT authentication, batch creation and retrieval, idempotent batch creation, status transition management, pagination and filtering, concurrent update handling, partner webhook notification, and a React dashboard.

## Technology Stack

### Backend
- Python
- Django 4.2.7
- Django REST Framework
- Simple JWT
- SQLite for development
- django-cors-headers

### Frontend
- React
- Vite
- Axios
- JavaScript

---

## Project Structure

```text
batch-tracking-system/
├── backend/
│   ├── batch_api/
│   ├── batches/
│   │   ├── migrations/
│   │   └── tests/
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── App.css
│   ├── package.json
│   └── .env.example
│
├── DEBUG.md
├── REVIEW.md
├── DESIGN.md
├── README.md
└── .gitignore
```

---

# 1. Prerequisites

Install the following:

- Git
- Python 3.9+
- Node.js LTS
- npm

Verify the installations:

```bash
git --version
python --version
node --version
npm --version
```

---

# 2. Clone the Repository

```bash
git clone https://github.com/prashanthchaduvala/batch-tracking-system.git
cd batch-tracking-system
```

---

# 3. Backend Setup

Open a terminal and move to the backend:

```cmd
cd backend
```

## Create a virtual environment

Windows:

```cmd
python -m venv batch-env
```

Activate it:

```cmd
batch-env\Scripts\activate
```

You should see:

```text
(batch-env)
```

Linux/macOS:

```bash
python3 -m venv batch-env
source batch-env/bin/activate
```

## Install dependencies

```bash
pip install -r requirements.txt
```

---

# 4. Backend Environment Variables

Create:

```text
backend/.env
```

Use `backend/.env.example` as the template.

Example:

```env
DJANGO_SECRET_KEY=replace-with-a-development-secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Do not commit the actual `.env` file.

Never commit production passwords, API keys, Django secret keys, tokens, or other credentials.

---

# 5. Database Setup

From the `backend` directory:

```cmd
python manage.py makemigrations
python manage.py migrate
```

For a fresh development database, create a user:

```cmd
python manage.py createsuperuser
```

Alternatively, create a normal test user:

```cmd
python manage.py shell
```

```python
from django.contrib.auth.models import User

User.objects.create_user(
    username="testuser",
    password="test@123"
)
```

Then:

```python
exit()
```

---

# 6. Run the Backend

```cmd
python manage.py runserver
```

Backend:

```text
http://127.0.0.1:8000/
```

API base URL:

```text
http://127.0.0.1:8000/api/
```

---

# 7. JWT Authentication

The API uses JWT authentication.

## Obtain an access token

```http
POST /api/token/
```

Example request:

```json
{
    "username": "testuser",
    "password": "testpass123"
}
```

Example response:

```json
{
    "refresh": "<refresh-token>",
    "access": "<access-token>"
}
```

Use the access token for protected requests:

```http
Authorization: Bearer <access-token>
```

The `/api/batches/` endpoints require authentication.

---

# 8. API Endpoints

## Obtain JWT token

```http
POST /api/token/
```

## Refresh JWT token

```http
POST /api/token/refresh/
```

## Create a batch

```http
POST /api/batches/
```

Example:

```json
{
    "sample_id": "SAMPLE001",
    "batch_type": "Blood Panel",
    "submitted_by": "Dr. Smith"
}
```

A newly created batch starts in:

```text
queued
```

## List batches

```http
GET /api/batches/
```

The response is paginated.

Example:

```json
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": []
}
```

## Get batch detail

```http
GET /api/batches/<id>/
```

## Update batch status

```http
PATCH /api/batches/<id>/status/
```

Example:

```json
{
    "status": "processing"
}
```

## Notify partner

```http
POST /api/batches/<id>/notify/
```

---

# 9. Batch Status Transitions

The application validates status transitions.

Expected workflow:

```text
queued
   |
   v
processing
   | \
   |  \
   v   v
completed  failed
              |
              v
          processing
```

Examples:

```text
queued -> processing       Valid
processing -> completed    Valid
processing -> failed       Valid
failed -> processing       Valid
completed -> processing    Invalid
completed -> queued        Invalid
```

Invalid transitions return an appropriate `400 Bad Request`.

---

# 10. Idempotent Batch Creation

Batch creation is designed to prevent duplicate records when the same request is submitted repeatedly.

Example:

```text
First request:
SAMPLE001 -> creates a batch

Repeated request:
SAMPLE001 -> returns the existing batch
```

This protects against duplicate records caused by client retries or network retry behavior.

---

# 11. Filtering

The batch list API supports filtering.

Filter by status:

```text
GET /api/batches/?status=queued
```

Filter by batch type:

```text
GET /api/batches/?type=Blood%20Panel
```

Combine filters:

```text
GET /api/batches/?status=queued&type=Blood%20Panel
```

Filtering is combined with pagination.

---

# 12. Concurrent Status Updates

The backend protects batch status transitions against concurrent requests.

For example, if two clients simultaneously attempt:

```text
queued -> processing
```

the application must not allow an invalid final state or an inconsistent transition.

The backend test suite includes a concurrent update test.

> Note: SQLite is used for local development. For production workloads with significant concurrent writes, PostgreSQL is recommended.

---

# 13. Partner Webhook

The notification endpoint is:

```http
POST /api/batches/<id>/notify/
```

The endpoint communicates the batch status to the configured partner webhook.

The webhook integration is designed to handle external failures using timeout and retry/backoff behavior where implemented by the backend.

For a production system, webhook delivery can be moved to a background worker such as Celery so API requests are not blocked by an external partner.

---

# 14. Frontend Setup

Open a second terminal.

From the project root:

```cmd
cd frontend
```

Install dependencies:

```cmd
npm install
```

---

# 15. Frontend Environment Variables

Create:

```text
frontend/.env
```

Example:

```env
VITE_API_URL=http://127.0.0.1:8000/api
```

Do not commit the actual `.env` file.

Use:

```text
frontend/.env.example
```

as the shareable configuration template.

---

# 16. Run the Frontend

```cmd
npm run dev
```

Vite will normally start the application at:

```text
http://localhost:5173/
```

Open the URL in a browser.

---

# 17. CORS Configuration

The Django backend allows the Vite development origins:

```text
http://localhost:5173
http://127.0.0.1:5173
```

Configured using:

```env
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Restart Django after changing environment variables.

---

# 18. Frontend Features

The React application provides:

- JWT login
- Logout
- Batch list
- Status badges
- Status filtering
- Batch type filtering
- Combined filtering
- Pagination
- Loading state
- Empty state
- API error handling
- Authentication error handling
- Valid status actions
- Optimistic status updates
- Rollback when a status update fails

The frontend sends the JWT access token in the `Authorization` header for protected API calls.

---

# 19. Running Backend and Frontend Together

Use two terminals.

### Terminal 1 — Backend

```cmd
cd batch-tracking-system\backend
batch-env\Scripts\activate
python manage.py migrate
python manage.py runserver
```

Backend:

```text
http://127.0.0.1:8000/
```

### Terminal 2 — Frontend

```cmd
cd batch-tracking-system\frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173/
```

---

# 20. Automated Tests

Backend tests are located under:

```text
backend/batches/tests/
```

Run all tests:

```cmd
cd backend
python manage.py test
```

Run the batch API tests:

```cmd
python manage.py test batches.tests.test_views -v 2
```

The test suite covers:

- Successful batch creation
- Idempotent batch creation
- Invalid status transition
- Concurrent status update
- Authentication failure

Run tests after applying migrations.

---

# 21. Debugging Task

The debugging analysis is documented in:

```text
DEBUG.md
```

The primary issues identified in the supplied debugging task are:

### Incorrect baseline

The original implementation used:

```python
baseline = raw_counts[0]
```

The specification states that the last reading is the control channel.

Correct approach:

```python
baseline = raw_counts[-1]
```

### Mutable default argument

The original implementation used:

```python
results_store={}
```

This creates a shared mutable dictionary across function calls.

Correct approach:

```python
def process_batch_results(
    batch_id,
    raw_counts,
    results_store=None
):
    if results_store is None:
        results_store = {}
```

The full debugging explanation and corrected implementation are available in `DEBUG.md`.

---

# 22. Code Review

The code review is documented in:

```text
REVIEW.md
```

The review covers the issues requested by the assessment, including:

- Security concerns
- Hard-coded secrets
- External HTTP request handling
- Timeout handling
- Retry behavior
- Error handling
- Validation
- Logging/observability
- Maintainability
- Production considerations

---

# 23. System Design

The system design task is documented in:

```text
DESIGN.md
```

It covers the proposed architecture for large Whole Slide Imaging files, including:

- Large 1–5 GB files
- Unreliable hospital networks
- Resumable uploads
- Object storage
- Asynchronous processing
- Queue-based workers
- Failure recovery
- Horizontal scaling
- Growth in hospitals and concurrent uploads

---

# 24. Database Choice

SQLite is used for local development because it is simple and requires no separate database server.

For production, PostgreSQL would be preferred because of:

- Better concurrent write handling
- Strong transactional support
- Better indexing
- Connection pooling
- Better scalability
- Production operational tooling

The application should be configured to use PostgreSQL in a production environment.

---

# 25. Scaling the Batch List API

If `GET /api/batches/` becomes slow as the number of records grows, I would address the bottleneck in stages.

### Database indexes

Add indexes to fields frequently used for filtering and ordering, such as:

```text
status
batch_type
sample_id
created_at
```

### Pagination

Keep pagination enabled to avoid returning a large number of records in one response.

### Query optimization

Use appropriate Django ORM techniques and avoid unnecessary database queries.

### Query analysis

Use database query plans and application profiling to identify the actual bottleneck before adding infrastructure.

### Caching

Redis can be introduced for frequently repeated read queries where caching provides a measurable benefit.

### Read replicas

For a large read-heavy production system, PostgreSQL read replicas can distribute read traffic.

---

# 26. Security

Important security practices include:

- JWT authentication
- Environment-based secrets
- No credentials committed to Git
- Input validation
- Django ORM/parameterized queries
- HTTPS in production
- Webhook timeout handling
- Webhook URL validation
- Appropriate HTTP status codes
- Limited sensitive information in error responses
- Secure secret management in production

---

# 27. Production Improvements

If the system were moved to production, I would consider:

1. PostgreSQL
2. Redis
3. Celery/background workers
4. Durable webhook delivery records
5. Structured logging
6. Prometheus metrics
7. Grafana monitoring
8. Distributed tracing
9. CI/CD
10. Docker/containerization
11. API documentation
12. Rate limiting
13. Cloud secret management
14. Automated frontend tests
15. Centralized error monitoring

These would be introduced based on actual requirements, traffic, reliability needs, and operational constraints.

---

# 28. Git and Secrets

Before committing:

```cmd
git status
```

The repository must not contain:

```text
.env
batch-env/
venv/
.venv/
node_modules/
db.sqlite3
```

The `.gitignore` should include:

```gitignore
.env
*.env
__pycache__/
*.pyc
batch-env/
venv/
.venv/
node_modules/
dist/
db.sqlite3
```

Commit environment templates instead:

```text
backend/.env.example
frontend/.env.example
```

---

# 29. Assessment Deliverables

The repository contains the requested assessment documentation:

```text
DEBUG.md
```

Task 2 debugging analysis.

```text
REVIEW.md
```

Task 4 code review.

```text
DESIGN.md
```

Task 5 system design.

```text
README.md
```

Project setup, API usage, architecture, design decisions, testing, and production considerations.

---

# 30. Submission Checklist

Before submission, verify:

- [ ] Repository is accessible to the evaluator
- [ ] Top-level README is present
- [ ] Backend is under `/backend`
- [ ] Frontend is under `/frontend`
- [ ] `requirements.txt` exists
- [ ] `package.json` exists
- [ ] `.env` is not committed
- [ ] `.env.example` files are present
- [ ] Database migrations are committed
- [ ] JWT authentication works
- [ ] Batch creation works
- [ ] Idempotent creation works
- [ ] Batch detail works
- [ ] Status transitions are validated
- [ ] Pagination works
- [ ] Status filtering works
- [ ] Batch type filtering works
- [ ] Concurrent update handling is implemented
- [ ] Partner notification endpoint works
- [ ] Webhook failure/retry handling is implemented as documented
- [ ] Required backend tests are present
- [ ] React frontend runs with Vite
- [ ] Login works
- [ ] JWT is sent with API requests
- [ ] Loading state is implemented
- [ ] Empty state is implemented
- [ ] Error state is implemented
- [ ] Combined filters work
- [ ] Pagination works
- [ ] Optimistic updates work
- [ ] Optimistic rollback works
- [ ] DEBUG.md is present
- [ ] REVIEW.md is present
- [ ] DESIGN.md is present
- [ ] No secrets are committed
- [ ] Git history contains meaningful incremental commits

---

# 31. Future Enhancements

Potential future enhancements include:

- PostgreSQL deployment
- Redis caching
- Celery task processing
- Docker and Docker Compose
- Kubernetes deployment
- CI/CD pipeline
- Prometheus/Grafana monitoring
- Centralized logging
- Distributed tracing
- API rate limiting
- More comprehensive automated tests
- Production-grade webhook delivery and observability

---

# 32. Conclusion

The Diagnostic Batch Tracking System demonstrates a complete backend and frontend implementation for managing diagnostic batches.

The project focuses on:

- Secure API access
- Reliable batch creation
- Idempotency
- Valid state transitions
- Concurrent update protection
- External webhook communication
- Pagination and filtering
- React-based user interface
- Optimistic UI updates
- Automated testing
- Debugging analysis
- Code review
- Production architecture considerations
