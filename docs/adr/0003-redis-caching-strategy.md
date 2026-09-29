# ADR-0003: Redis Caching Strategy for Statistics Endpoint

## Status
Accepted

## Context

The `/api/stats` endpoint calculates aggregate statistics across all complaints:
- Total count by category
- Total count by priority
- Average triage latency

This requires:
- Full table scan (or multiple indexed queries)
- Aggregation computations
- High read frequency (dashboard refreshes every 30s)

Without caching, every dashboard view triggers expensive database queries.

## Decision

Use **Redis** for caching stats with 60-second TTL:

1. **Cache Key**: `stats:global` (string key)
2. **Cache Value**: JSON-serialized stats object
3. **TTL**: 60 seconds
4. **Strategy**: Cache-aside pattern
   - Check cache first
   - On miss: query database → cache result → return
   - On hit: return cached value

**Implementation**:
- **Service**: `RedisService` class handles caching logic
  - **File**: `backend/app/services/redis_service.py`, lines 20-65
- **Stats Route**: Calls `RedisService.get_cached_stats()`
  - **File**: `backend/app/routes/stats.py`, lines 25-40

## Consequences

### Positive
✅ Reduces database load (1 query per 60s vs. 1 query per request)
✅ Faster response time (~5ms cached vs. ~100ms uncached)
✅ Stats endpoint scales to thousands of requests/minute
✅ TTL ensures data is reasonably fresh

### Negative
❌ Stats can be up to 60 seconds stale
❌ Redis becomes a dependency (but degrades gracefully)
❌ Cache invalidation complexity (currently time-based only)

### Trade-offs Considered

| Strategy | Pros | Cons | Decision |
|----------|------|------|----------|
| **No caching** | Always fresh | High DB load | ❌ Rejected |
| **Redis cache (chosen)** | Fast, scalable | 60s staleness | ✅ Accepted |
| **Materialized view** | Always up-to-date | PostgreSQL-specific | ❌ Rejected |
| **Event-based invalidation** | Fresh when changed | Complex implementation | ❌ Future work |

## References
- **Redis service**: `backend/app/services/redis_service.py`, lines 20-65
- **Stats route**: `backend/app/routes/stats.py`, lines 25-40
- **Config**: `backend/app/core/config.py`, line 26 (REDIS_URL)
- **Docker Compose**: `compose.yaml`, lines 25-42 (Redis service)
- **Kubernetes**: `k8s/base/redis-deployment.yaml`
