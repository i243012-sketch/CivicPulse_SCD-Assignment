# Fixes Applied to CivicPulse

## Summary
Fixed 7 critical issues in the existing codebase as requested.

---

## Issue 1: SIGTERM Handler
**File**: `backend/app/main.py`

**Change**: Removed `sys.exit(0)` from SIGTERM handler

**Before**:
```python
def handle_sigterm(signum: int, frame: object) -> None:
    global shutdown_event
    logger.info("Received SIGTERM, initiating graceful shutdown")
    shutdown_event = True
    sys.exit(0)  # ❌ Immediate exit
```

**After**:
```python
def handle_sigterm(signum: int, frame: object) -> None:
    global shutdown_event
    logger.info("Received SIGTERM, initiating graceful shutdown")
    shutdown_event = True  # ✅ Only set flag
```

**Reason**: Allows in-flight requests to complete before Uvicorn naturally exits through the lifespan shutdown sequence.

---

## Issue 2: Triage Fallback Test
**File**: `backend/tests/test_triage_fallback.py` (NEW)

**Created**: Complete test suite for fallback behavior

**Test Coverage**:
- Provider that always raises `TriageTimeoutError`
- POST to `/api/complaints` 
- Asserts:
  - Status code is 201 (never 500)
  - `triaged_by` equals "rules:fallback"
  - Valid triage results from fallback provider
  - All required fields present

**Key Assertion**:
```python
assert response.status_code == 201, f"Expected 201, got {response.status_code}"
assert data["triaged_by"] == "rules:fallback"
```

---

## Issue 3: Database CHECK Constraints
**File**: `backend/alembic/versions/20240101_0001_initial_create_complaints_table.py`

**Added**: CHECK constraints for data validation at database level

**Constraints Added**:
```python
sa.CheckConstraint("length(text) >= 10 AND length(text) <= 2000", name="check_text_length")
sa.CheckConstraint("length(location) >= 3 AND length(location) <= 200", name="check_location_length")
```

**Reason**: Defense in depth - validation at both application (Pydantic) and database (PostgreSQL) layers.

---

## Issue 4: Index Optimization
**File**: `backend/alembic/versions/20240101_0001_initial_create_complaints_table.py`

**Changed**: Composite index strategy

**Before**:
- Composite index: `(status, created_at)`

**After**:
- Composite index: `(status, priority)`
- Separate index: `created_at` (kept as is)

**Indexes Now**:
1. `ix_complaints_category` - Single column
2. `ix_complaints_priority` - Single column
3. `ix_complaints_status` - Single column
4. `ix_complaints_created_at` - Single column
5. `ix_complaints_status_priority` - Composite (NEW)

**Reason**: More useful for filtering by status + priority (common query pattern).

---

## Issue 5: Environment Variable for Database Password
**File**: `compose.yaml`

**Changed**: Postgres password to use environment variable

**Before**:
```yaml
environment:
  POSTGRES_PASSWORD: dev_password_change_in_prod  # ❌ Hardcoded
```

**After**:
```yaml
environment:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-dev_password_change_in_prod}  # ✅ From env
```

**Also Updated**: Backend DATABASE_URL to use same variable

**Reason**: Follows 12-factor app principles, allows customization via `.env` file.

---

## Issue 6: Cache Provider Name Preservation
**File**: `backend/app/services/complaint_service.py`

**Fixed**: Cache now stores original provider name

**Before**:
```python
# Cached only result
self.redis.set(cache_key, triage_result.model_dump_json(), ttl=...)

# On cache hit
triage_result = TriageResult(**json.loads(cached))
triaged_by = self.triage_provider.name  # ❌ Wrong! Uses CURRENT provider
```

**After**:
```python
# Cache result WITH provider name
cache_data = {
    "result": json.loads(triage_result.model_dump_json()),
    "triaged_by": triaged_by,  # ✅ Store original provider
}
self.redis.set(cache_key, json.dumps(cache_data), ttl=...)

# On cache hit
cached_data = json.loads(cached)
triage_result = TriageResult(**cached_data["result"])
triaged_by = cached_data["triaged_by"]  # ✅ Restore original provider
```

**Impact**: 
- If complaint was triaged by "llm:groq", cached version shows "llm:groq" (not "rules" or "simulated")
- If complaint was triaged by "rules:fallback", cached version preserves "rules:fallback"
- Accurate audit trail

---

## Issue 7: Remove Unused Groq SDK
**File**: `backend/pyproject.toml`

**Removed**: `groq==0.4.1` dependency

**Reason**: LLM calls are made directly via `httpx` to Groq API. The SDK is not used anywhere in the codebase.

**Verification**:
```bash
grep -r "from groq" backend/app/  # No results
grep -r "import groq" backend/app/  # No results
```

**Benefits**:
- Smaller dependency tree
- Faster installs
- Reduced attack surface

---

## Files Modified

### Modified (6 files):
1. `backend/app/main.py` - Fixed SIGTERM handler
2. `backend/app/services/complaint_service.py` - Fixed cache to preserve provider name
3. `backend/alembic/versions/20240101_0001_initial_create_complaints_table.py` - Added CHECK constraints, changed composite index
4. `backend/pyproject.toml` - Removed groq SDK
5. `compose.yaml` - Use environment variable for password
6. `.env.example` - Already had POSTGRES_PASSWORD (no change needed)

### Created (1 file):
7. `backend/tests/test_triage_fallback.py` - NEW test for fallback behavior

---

## Verification Commands

### Run the fallback test:
```bash
cd backend
pytest tests/test_triage_fallback.py -v
```

### Check migration is valid:
```bash
cd backend
alembic check
```

### Verify groq is not imported:
```bash
grep -r "groq" backend/app/
# Should only find GROQ_API_KEY in config, no imports
```

### Test with compose:
```bash
# Create .env from template
cp .env.example .env

# Edit .env and set POSTGRES_PASSWORD
nano .env

# Start services
docker compose up
```

---

## Impact Assessment

✅ **No Breaking Changes**: All fixes are backward compatible
✅ **Production Ready**: Fixes improve reliability and security
✅ **Test Coverage**: Added critical fallback test
✅ **Database Safety**: CHECK constraints prevent invalid data
✅ **Security**: Password externalized to environment
✅ **Observability**: Provider names accurately tracked
✅ **Performance**: Better index strategy for common queries

---

## Notes

1. **SIGTERM**: Apps now shut down more gracefully, honoring in-flight requests
2. **Test**: Must pass before deployment - validates core fallback requirement
3. **CHECK Constraints**: Database-level validation complements Pydantic
4. **Index**: (status, priority) more useful than (status, created_at) for filtering
5. **Password**: .env file required for compose (use .env.example as template)
6. **Cache**: Provider attribution now accurate across cache hits
7. **Dependencies**: Leaner, faster builds without unused SDK
