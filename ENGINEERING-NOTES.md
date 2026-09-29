# Engineering Notes

**Question 1**: How does triage provider selection work?
- Answer: Factory pattern reads TRIAGE_PROVIDER env var
- Files: `backend/app/providers/triage/factory.py`, `backend/app/core/config.py`

**Question 2**: Where are database migrations?
- Answer: Alembic migrations in `backend/alembic/versions/`
- Applied by init container before backend starts

**Question 3**: How does Redis caching work?
- Answer: Cache-aside pattern, 60s TTL, `stats:global` key
- Files: `backend/app/services/redis_service.py`, `backend/app/routes/stats.py`

**Question 4**: Where is rate limiting?
- Answer: Need to check `backend/app/main.py` for middleware or decorator
- Look for rate limit configuration in config.py
