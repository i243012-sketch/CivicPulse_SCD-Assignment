# Engineering Notes - CivicPulse Municipal Complaint System

## Overview

This document answers technical questions about the codebase architecture and implementation details. Each answer includes specific file paths and line numbers for reference.

---

## Questions 1-4 (Partner's Section)

_[Partner to complete questions 1-4:]_

### 1. How does triage provider selection work?

**Answer**: _[Partner to fill in]_

**References**:
- File: `backend/app/providers/triage/factory.py`
- File: `backend/app/core/config.py`

---

### 2. Where are database migrations defined and how are they applied?

**Answer**: _[Partner to fill in]_

**References**:
- Directory: `backend/alembic/versions/`
- File: `backend/alembic/versions/20240101_0001_initial_create_complaints_table.py`

---

### 3. How does Redis caching work for the stats endpoint?

**Answer**: _[Partner to fill in]_

**References**:
- File: `backend/app/services/redis_service.py`
- File: `backend/app/routes/stats.py`

---

### 4. Where is rate limiting implemented and how does it work?

**Answer**: _[Partner to fill in]_

**References**:
- File: `backend/app/main.py`
- File: `backend/app/core/config.py`

---

## Questions 5-8 (My Section)

### 5. How does the frontend get the backend URL at runtime?

**Answer**: 

The frontend uses a **runtime environment variable injection** strategy to determine the backend URL. Unlike traditional build-time configuration, the backend URL is injected when the container starts, making the same Docker image portable across all environments (dev, staging, production).

The process works as follows:

1. **Environment Variables Read**: The `docker-entrypoint.sh` script reads `BACKEND_HOST` and `BACKEND_PORT` environment variables (with defaults: `backend` and `8000`)
   - **File**: `frontend/docker-entrypoint.sh`, lines 4-6

2. **Nginx Configuration Generation**: The entrypoint script generates `/etc/nginx/nginx.conf` dynamically, substituting the environment variables into the proxy configuration:
   ```nginx
   location /api/ {
       proxy_pass http://${BACKEND_HOST}:${BACKEND_PORT};
       # ... proxy headers ...
   }
   ```
   - **File**: `frontend/docker-entrypoint.sh`, lines 59-76

3. **React Application Access**: The React app makes API calls to `/api/*` endpoints, which nginx proxies to the actual backend service. This approach:
   - Avoids CORS issues (same-origin requests)
   - Keeps backend URL hidden from browser
   - Allows single image to work in any environment

4. **Configuration Examples**:
   - **Docker Compose**: `BACKEND_HOST=backend` (service name)
     - **File**: `compose.yaml`, lines 89-90
   - **Kubernetes**: `BACKEND_HOST=prod-backend` (k8s service name)
     - **File**: `k8s/base/frontend-deployment.yaml`, lines 20-23

**Key Benefits**:
- ✅ Single Docker image for all environments
- ✅ No rebuild needed when backend URL changes
- ✅ Works in Docker Compose, Kubernetes, bare metal

**References**:
- **Implementation**: `frontend/docker-entrypoint.sh`, lines 1-95
- **Nginx proxy config**: `frontend/docker-entrypoint.sh`, lines 59-76
- **Compose env vars**: `compose.yaml`, lines 89-90
- **Kubernetes env vars**: `k8s/base/frontend-deployment.yaml`, lines 20-23
- **Architecture decision**: `docs/adr/0002-frontend-runtime-config.md`

---

### 6. Where is the health check endpoint defined?

**Answer**:

The application has **multiple health check endpoints** at different levels:

1. **Primary Health Endpoint** (FastAPI):
   - **Route**: `GET /api/meta/health`
   - **File**: `backend/app/routes/meta.py`, line 30
   - **Returns**: JSON with status, timestamp, triage provider info
   - **Purpose**: Application-level health check (verifies FastAPI is responding)

2. **Health Route Registration**:
   - **File**: `backend/app/main.py`, line 161 (includes meta router)
   - **File**: `backend/app/main.py`, line 164 (duplicates at root level for convenience)

3. **Container Health Checks**:
   
   a. **Backend Container** (Docker/Kubernetes):
   - **Command**: `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/meta/health')"`
   - **File**: `compose.yaml`, lines 68-72
   - **Kubernetes**: `k8s/base/backend-deployment.yaml`, lines 45-50
   
   b. **Frontend Container** (nginx):
   - **Route**: `GET /nginx-health` (custom endpoint)
   - **File**: `frontend/docker-entrypoint.sh`, lines 88-92
   - **Returns**: Plain text "healthy\n"
   - **Purpose**: Verifies nginx is running (lightweight, no backend dependency)

4. **Additional Endpoints**:
   - **Readiness**: `GET /api/meta/ready` - checks database connectivity
     - **File**: `backend/app/routes/meta.py`, line 42
   - **Metrics**: `GET /api/metrics` - Prometheus metrics endpoint
     - **File**: `backend/app/routes/metrics.py`, line 17

**Health Check Flow**:
```
Docker/K8s → /nginx-health (frontend) → 200 OK
Docker/K8s → /api/meta/health (backend) → FastAPI → 200 OK + JSON
Kubernetes → /api/meta/ready (backend) → FastAPI → DB ping → 200 OK
```

**References**:
- **Backend health**: `backend/app/routes/meta.py`, lines 30-40
- **Backend readiness**: `backend/app/routes/meta.py`, lines 42-55
- **Frontend nginx health**: `frontend/docker-entrypoint.sh`, lines 88-92
- **Compose healthcheck**: `compose.yaml`, lines 68-72
- **K8s healthcheck**: `k8s/base/backend-deployment.yaml`, lines 45-50

---

### 7. How do we handle database connection failures?

**Answer**:

The application uses **multiple layers of defense** against database connection failures:

1. **Connection Pool Pre-Ping** (SQLAlchemy):
   - **Setting**: `pool_pre_ping=True` in engine configuration
   - **File**: `backend/app/core/database.py`, line 20
   - **Behavior**: SQLAlchemy tests each connection before using it from the pool. If the connection is dead (e.g., database restarted), it's automatically recycled and a new connection is established.
   - **Benefit**: Handles transient network issues and database restarts without application errors

2. **Connection Pool Configuration**:
   - **Pool Size**: Configurable via `DB_POOL_SIZE` (default: 5)
   - **Max Overflow**: Configurable via `DB_MAX_OVERFLOW` (default: 10)
   - **File**: `backend/app/core/database.py`, lines 17-21
   - **File**: `backend/app/core/config.py`, lines 35-36
   - **Behavior**: Maintains 5 persistent connections, can create up to 10 additional temporary connections under load

3. **Graceful Shutdown**:
   - **Function**: `close_db_connections()` disposes all connections cleanly
   - **File**: `backend/app/core/database.py`, lines 40-42
   - **Called**: During application shutdown in lifespan manager
   - **File**: `backend/app/main.py`, line 54

4. **Session Management** (Dependency Injection):
   - **Function**: `get_db()` ensures sessions are always closed after use
   - **File**: `backend/app/core/database.py`, lines 28-38
   - **Pattern**: Uses Python context manager (`try`/`finally`) to guarantee cleanup
   - **Behavior**: Even if an exception occurs during request processing, the session is closed and returned to the pool

5. **Docker/Kubernetes Health Checks**:
   - **Readiness Probe**: Verifies database connectivity before routing traffic
   - **File**: `backend/app/routes/meta.py`, lines 42-55 (ready endpoint)
   - **Behavior**: If database is unreachable, readiness check fails and container is marked "not ready"
   - **K8s Response**: Kubernetes stops sending traffic to unhealthy pods

6. **Init Container Wait Strategy** (Kubernetes):
   - **Container**: `wait-for-db` init container runs before backend starts
   - **File**: `.github/workflows/cd.yml`, lines 280-295
   - **Command**: Uses `busybox` to check if postgres port is open (`nc -z`)
   - **Retries**: 30 attempts with 5-second sleep between tries
   - **Benefit**: Backend pod only starts after database is accepting connections

7. **Alembic Migration Handling**:
   - **Init Container**: `run-migrations` init container applies schema changes
   - **File**: `k8s/overlays/prod/backend-deployment-patch.yaml` (applied via kustomize)
   - **Command**: `alembic upgrade head`
   - **Dependency**: Runs after `wait-for-db` completes
   - **Benefit**: Schema is always up-to-date before backend accepts traffic

**Failure Scenarios Handled**:

| Scenario | Handled By | Behavior |
|----------|-----------|----------|
| Database not started | Init container wait-for-db | Backend pod waits up to 150s |
| Database connection stale | pool_pre_ping=True | Connection refreshed automatically |
| Database temporarily down | Health check + pool_pre_ping | Traffic stopped, connections recycled |
| High connection load | Connection pool (5+10) | Up to 15 concurrent connections |
| Application crash | Session cleanup (finally) | Connections returned to pool |
| Graceful shutdown | close_db_connections() | All connections disposed cleanly |

**References**:
- **Pool pre-ping**: `backend/app/core/database.py`, line 20
- **Connection pool**: `backend/app/core/database.py`, lines 17-21
- **Session cleanup**: `backend/app/core/database.py`, lines 28-38
- **Graceful shutdown**: `backend/app/core/database.py`, lines 40-42
- **Config settings**: `backend/app/core/config.py`, lines 35-36
- **Readiness check**: `backend/app/routes/meta.py`, lines 42-55
- **Init containers**: `.github/workflows/cd.yml`, lines 280-295

---

### 8. Where is the complaint model defined and what are its key fields?

**Answer**:

The complaint model is defined using **SQLAlchemy ORM** with modern Python type hints (PEP 695).

**Location**:
- **File**: `backend/app/models/complaint.py`
- **Class**: `Complaint(Base)`, lines 68-115
- **Table Name**: `complaints`

**Key Fields**:

1. **Primary Key**:
   - `id: UUID` - Primary key, auto-generated UUID
   - **Line**: 72-76
   - **Type**: `Uuid` (PostgreSQL native UUID type)

2. **Core Complaint Data**:
   - `text: str` - Full complaint description (Text field, no length limit)
   - `location: str` - Address or location reference (max 200 chars)
   - `reporter_contact: str | None` - Optional contact info (max 200 chars)
   - **Lines**: 79-82

3. **Triage Results**:
   - `category: Category` - Enum: water, electricity, sanitation, roads, streetlights, other
   - `priority: Priority` - Enum: high, normal, low
   - `status: Status` - Enum: open, in_progress, resolved, rejected
   - **Lines**: 85-96
   - **Enums Defined**: Lines 13-48

4. **AI Triage Metadata**:
   - `ai_summary: str | None` - 140-char summary generated by LLM (optional)
   - `triaged_by: str` - Provider identifier (e.g., "llm", "simulated", "rules")
   - `triage_latency_ms: int` - Time taken to triage in milliseconds
   - **Lines**: 99-102

5. **Timestamps**:
   - `created_at: datetime` - Set by database on insert (`server_default=func.now()`)
   - `updated_at: datetime` - Automatically updated on modification (`onupdate=func.now()`)
   - **Lines**: 105-115

**Enumerations** (using Python 3.11+ `enum.StrEnum`):

1. **Category** (line 13-22):
   - WATER, ELECTRICITY, SANITATION, ROADS, STREETLIGHTS, OTHER

2. **Priority** (line 25-31):
   - HIGH, NORMAL, LOW

3. **Status** (line 34-42):
   - OPEN, IN_PROGRESS, RESOLVED, REJECTED

**State Machine** (for status transitions):
- **Function**: `is_valid_transition()` validates status changes
- **Line**: 53-55
- **Transition Rules** (line 45-51):
  ```python
  OPEN → {IN_PROGRESS, REJECTED}
  IN_PROGRESS → {RESOLVED, REJECTED}
  RESOLVED → {}  # Terminal state
  REJECTED → {}  # Terminal state
  ```

**Database Type Mappings**:
- UUIDs: `Uuid` (PostgreSQL native, not `String`)
- Enums: `Enum(Category, native_enum=False)` - stored as VARCHAR, not PostgreSQL ENUM
- Timestamps: `TIMESTAMP(timezone=True)` - timezone-aware timestamps

**Migration**:
- **File**: `backend/alembic/versions/20240101_0001_initial_create_complaints_table.py`
- **Creates**: Table with all columns, indexes, constraints

**Key Design Decisions**:
- ✅ UUIDs prevent sequential ID enumeration attacks
- ✅ Enums enforce valid values at database level
- ✅ `server_default` ensures timestamps even if app logic fails
- ✅ State machine prevents invalid status transitions
- ✅ Nullable fields (`reporter_contact`, `ai_summary`) for optional data

**References**:
- **Model definition**: `backend/app/models/complaint.py`, lines 68-115
- **Enumerations**: `backend/app/models/complaint.py`, lines 13-42
- **State machine**: `backend/app/models/complaint.py`, lines 45-55
- **Database migration**: `backend/alembic/versions/20240101_0001_initial_create_complaints_table.py`
- **Base class**: `backend/app/core/database.py`, lines 10-13

---

## Additional Technical Notes

### Testing Strategy
- **Backend**: pytest with fixtures for database and Redis
- **Frontend**: Vitest + React Testing Library
- **Integration**: Docker Compose with curl-based health checks

### CI/CD Pipeline
- **CI Jobs**: Lint, type check, backend tests, frontend tests, integration tests
- **CD Jobs**: Build Docker images, deploy to kind cluster, smoke tests
- **Release**: Automatic on version tags (v*)

### Infrastructure
- **Local Dev**: Docker Compose with hot reload
- **Production**: Kubernetes with HPA, StatefulSets for databases
- **Observability**: Prometheus metrics, structured logging (JSON)

---

## Document Metadata

**Created**: 2024-09-28  
**Last Updated**: 2024-09-28  
**Authors**: Development Team  
**Purpose**: Technical reference for codebase navigation and onboarding
