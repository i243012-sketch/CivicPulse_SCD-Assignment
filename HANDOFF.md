# CivicPulse - Frontend Handoff Document

**Status:** Backend complete and verified, frontend scaffold exists but needs completion  
**Date:** September 27, 2026  
**For:** Frontend developer starting component work

---

## What's Built and Verified

### Backend (Complete ✅)

**Architecture:**
- 4-layer architecture: Routes → Services → Repositories → Models
- Clean separation: routes handle HTTP only, services contain business logic
- FastAPI with Pydantic validation, SQLAlchemy ORM, Alembic migrations
- PostgreSQL database with one migration creating the complaints table

**AI Triage System:**
- 3 triage providers:
  1. **LLMTriage** (Groq API, llama-3.3-70b-versatile) - primary, uses prompt with delimiters for injection resistance
  2. **RuleBasedTriage** - keyword-based fallback, simple and reliable
  3. **SimulatedTriage** - instant fake results for testing without external dependencies
- Automatic fallback: LLM failures (timeout, rate limit, validation errors) → RuleBasedTriage
- Results cached in Redis per complaint text hash (24h TTL)
- All triage latency tracked with Prometheus metrics

**Database & Seeding:**
- Seed script at `scripts/seed.py` creates 34 realistic complaints in Urdu-influenced English
- Idempotent: safe to run multiple times, won't create duplicates
- Categories: water, electricity, sanitation, roads, streetlights, other
- Priorities: low, normal, high

**Docker Compose:**
- 4 services: postgres, redis, backend, frontend
- **Auto-seeds in development**: backend runs `alembic upgrade head && python /app/scripts/seed.py && uvicorn ...`
- Production compose file does NOT auto-seed (only dev does)
- Healthchecks on all services with proper startup dependencies

**Kubernetes Deployment:**
- Base manifests + dev/prod overlays using Kustomize
- Backend: 2 replicas, HPA (2-10 pods, 60% CPU target), PDB (minAvailable: 1), rolling updates
- Postgres: StatefulSet with volumeClaimTemplates (NOT a Deployment)
- Redis: Deployment with PVC
- InitContainer runs migrations before backend starts
- Probes: startupProbe + livenessProbe → `/api/meta/health` (no DB dependency), readinessProbe → `/api/meta/ready` (checks DB + Redis)
- **VPA included in manifests but intentionally not deployed** to local k3d cluster (CRD not installed, this is expected)
- Tested and verified on local k3d cluster named "civicpulse-test" - all 6 pods running stable, endpoints confirmed working

**Testing:**
- 4 backend test files:
  - `test_triage_fallback.py` - LLM → rules fallback on error
  - `test_llm_prompt_injection_guardrail.py` - LLM delimiter validation
  - `test_rule_based_keyword_sensitivity.py` - documents keyword matching limitation
  - `test_stats_cache.py` - Redis caching for /api/stats
- Coverage tracked with pytest-cov

**Documentation:**
- `docs/adr/0004-pii-and-data-governance.md` - ADR documenting RuleBasedTriage keyword limitation
- `k8s/README.md` - Complete Kubernetes deployment guide (283 lines)

---

## API Contract (Real Endpoints)

All endpoints return JSON. Base URL in dev: `http://localhost:8000`

### Complaints API (`/api/complaints`)

**POST /api/complaints**
- Creates a new complaint
- Request body:
  ```json
  {
    "text": "string (required, 10-5000 chars)",
    "location": "string (required, 5-200 chars)",
    "reporter_contact": "string (optional, phone/email)"
  }
  ```
- Response: `201 Created`
  ```json
  {
    "id": "uuid",
    "text": "string",
    "location": "string",
    "reporter_contact": "string|null",
    "category": "water|electricity|sanitation|roads|streetlights|other",
    "priority": "low|normal|high",
    "status": "open|in_progress|resolved|rejected",
    "ai_summary": "string",
    "triaged_by": "llm:groq|rules:fallback|simulated",
    "triage_latency_ms": 0,
    "created_at": "ISO8601 timestamp",
    "updated_at": "ISO8601 timestamp"
  }
  ```
- Rate limited: 60 requests/minute per IP (dev), returns `429` with `Retry-After` header if exceeded
- Always returns 201 (never 500) due to triage fallback

**GET /api/complaints/{complaint_id}**
- Get single complaint by UUID
- Response: `200 OK` with complaint object (same schema as POST response)
- Response: `404 Not Found` if complaint doesn't exist

**GET /api/complaints**
- List complaints with filtering and pagination
- Query parameters:
  - `category` (optional): filter by category enum
  - `priority` (optional): filter by priority enum
  - `status` (optional): filter by status enum
  - `page` (optional, default 1): page number (1-indexed)
  - `page_size` (optional, default 20, max 100): items per page
- Response: `200 OK`
  ```json
  {
    "items": [/* array of complaint objects */],
    "total": 123,
    "page": 1,
    "page_size": 20,
    "total_pages": 7
  }
  ```

**PATCH /api/complaints/{complaint_id}/status**
- Update complaint status
- Request body:
  ```json
  {
    "status": "open|in_progress|resolved|rejected"
  }
  ```
- State machine enforced:
  - `open` → `in_progress` or `rejected`
  - `in_progress` → `resolved` or `rejected`
  - `resolved` → (terminal, no transitions)
  - `rejected` → (terminal, no transitions)
- Response: `200 OK` with updated complaint object
- Response: `404 Not Found` if complaint doesn't exist
- Response: `409 Conflict` with error message if invalid transition

### Stats API (`/api`)

**GET /api/stats**
- Get aggregated statistics
- Response: `200 OK`
  ```json
  {
    "by_category": [
      {"category": "water", "count": 15},
      {"category": "electricity", "count": 8}
    ],
    "by_priority": [
      {"priority": "high", "count": 12},
      {"priority": "normal", "count": 18}
    ],
    "total_complaints": 34
  }
  ```
- Response header `X-Cache: HIT` or `X-Cache: MISS` (Redis cache, 30s TTL)
- Cache invalidated immediately on any complaint write operation

### Meta/Health API (`/api/meta`)

**GET /api/meta/health**
- Liveness check, always returns 200 if app is running
- Does NOT depend on database or cache
- Response: `200 OK`
  ```json
  {
    "status": "healthy",
    "service": "civicpulse-backend"
  }
  ```

**GET /api/meta/ready**
- Readiness check, verifies database and Redis connectivity
- Response: `200 OK` if both dependencies healthy
  ```json
  {
    "status": "ready",
    "postgres": "healthy",
    "redis": "healthy"
  }
  ```
- Response: `503 Service Unavailable` if any dependency unhealthy
  ```json
  {
    "detail": {
      "status": "not_ready",
      "postgres": "unhealthy",
      "redis": "healthy"
    }
  }
  ```

**GET /api/meta/providers**
- Get active triage provider and recent outcomes
- Response: `200 OK`
  ```json
  {
    "active_provider": "simulated",
    "recent_outcomes": [
      /* last 20 triage operations with latency and fallback info */
    ]
  }
  ```

### Metrics API

**GET /metrics**
- Prometheus metrics in text format
- Returns metrics for:
  - HTTP request counts/duration by method/endpoint/status
  - Triage duration by provider
  - Triage fallback counts by provider/reason
  - Cache hit/miss counters (triage cache, stats cache)
  - Rate limit violations by IP

---

## What's NOT Done

### Frontend (Partially Done)

**Exists:**
- Basic scaffold: ComplaintForm.tsx, ComplaintList.tsx, Dashboard.tsx, HomePage.tsx
- Filtering and pagination in ComplaintList (category, priority, status filters)
- API client in `src/api/client.ts`

**Still Needed:**
- ❌ Error boundary component (does not exist)
- ❌ Component tests (0 test files exist, need at least 5)
- ❌ Stats page could be enhanced (currently just shows basic dashboard)
- ❌ Form validation feedback could be improved
- ❌ Loading states and error handling in components

### CI/CD (Not Started)

- ❌ `.github/workflows/ci.yml` - lint, test, build
- ❌ `.github/workflows/cd.yml` - deploy on merge to main
- ❌ `.github/workflows/release.yml` - release automation

### Load Testing (Not Started)

- ❌ `load/` directory only has .gitkeep, no k6 script

### Documentation (Mostly Empty)

- ❌ `README.md` - exists but only contains title
- ❌ `docs/RUNBOOK.md` - does not exist
- ❌ `docs/AI-USAGE.md` - does not exist
- ❌ `docs/ENGINEERING-NOTES.md` - does not exist
- ✅ `k8s/README.md` - complete (283 lines)
- ✅ `docs/adr/0004-pii-and-data-governance.md` - complete

### Git Workflow

- ❌ Deliberate merge conflict has not occurred yet (only one clean merge so far: PR #1 into dev)

---

## How to Run Locally

### Prerequisites
- Docker and Docker Compose
- Git

### Steps

1. **Clone and enter the repository:**
   ```bash
   cd /path/to/CivicPulse_SCD-Assignment
   ```

2. **Start everything (builds, seeds, and runs):**
   ```bash
   docker compose up --build
   ```

   This will:
   - Build backend and frontend images
   - Start postgres, redis, backend, frontend
   - **Automatically run migrations and seed 34 complaints** (dev only)
   - Backend available at `http://localhost:8000`
   - Frontend available at `http://localhost:8080`

3. **Verify it's working:**
   ```bash
   # Check backend health
   curl http://localhost:8000/api/meta/health
   
   # Check stats (should show 34 complaints)
   curl http://localhost:8000/api/stats
   
   # List complaints
   curl http://localhost:8000/api/complaints?page=1&page_size=5
   
   # Open frontend in browser
   open http://localhost:8080
   ```

4. **Stop everything:**
   ```bash
   docker compose down
   ```

5. **Clean restart (delete volumes/data):**
   ```bash
   docker compose down -v
   docker compose up --build
   ```

### Development Workflow

- Backend code changes are hot-reloaded (uvicorn --reload)
- Frontend changes require rebuild (it's a production nginx container, not a dev server)
- Database persists in Docker volume between restarts (unless you use `-v`)
- Seed script is idempotent - running it multiple times won't create duplicates

---

## Git Workflow (IMPORTANT)

### Branch Strategy

- `main` - production, protected
- `dev` - integration branch, protected
- Feature branches - all work happens here

### Workflow Rules

1. **NEVER commit directly to `dev` or `main`**
2. **Always branch off `dev`:**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feat/your-feature-name
   ```

3. **Commit your changes:**
   ```bash
   git add <files>
   git commit -m "feat: descriptive message"
   ```

4. **Push and open PR:**
   ```bash
   git push origin feat/your-feature-name
   # Open PR on GitHub targeting `dev` (not main)
   ```

5. **Wait for review:**
   - Do NOT merge your own PR immediately
   - Wait for at least one review comment
   - Address any requested changes
   - Reviewer approves → then merge

6. **After merge:**
   ```bash
   git checkout dev
   git pull origin dev
   git branch -d feat/your-feature-name  # delete local branch
   ```

### Commit Message Format

- `feat:` - new feature
- `fix:` - bug fix
- `docs:` - documentation only
- `test:` - adding/updating tests
- `chore:` - maintenance (dependencies, config)

---

## Questions?

- Backend code: `backend/app/`
- API schemas: `backend/app/schemas/`
- Frontend scaffold: `frontend/src/`
- Tests: `backend/tests/`
- K8s manifests: `k8s/base/` and `k8s/overlays/`

Run `docker compose up` first to see the system working before writing frontend code against it.
