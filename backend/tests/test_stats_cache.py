"""Test stats endpoint caching behavior."""
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.providers.triage import get_triage_provider
from app.routes.complaints import get_complaint_service
from app.services.complaint_service import ComplaintService
from app.services.redis_service import RedisService

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_stats_cache.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_db():
    """Create test database and tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create test client with overridden dependencies."""
    # Override database
    app.dependency_overrides[get_db] = override_get_db
    
    # Override complaint service
    def override_complaint_service(db: Session = Depends(override_get_db)):  # type: ignore[assignment]
        triage_provider = get_triage_provider()
        redis_service = RedisService()
        return ComplaintService(db, triage_provider, redis_service)
    
    app.dependency_overrides[get_complaint_service] = override_complaint_service
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up overrides
    app.dependency_overrides.clear()


def test_stats_cache_miss_then_hit(client):
    """
    Test that stats endpoint caching works correctly.
    
    First request should be X-Cache: MISS, second should be X-Cache: HIT.
    If Redis is unreachable, test fails explicitly instead of silently skipping.
    """
    # Check Redis connectivity upfront
    redis_service = RedisService()
    try:
        redis_service.client.ping()
    except Exception as e:
        pytest.fail(
            f"Redis is not reachable: {e}. "
            "Start Redis with: docker compose up -d redis"
        )
    
    # Clear any existing cache
    redis_service.client.delete("stats:cache")
    
    # First request - should be cache MISS
    response1 = client.get("/api/stats")
    assert response1.status_code == 200, (
        f"Expected 200, got {response1.status_code}: {response1.text}"
    )
    
    cache_status_1 = response1.headers.get("X-Cache")
    assert cache_status_1 == "MISS", (
        f"First request should have X-Cache: MISS, got X-Cache: {cache_status_1}"
    )
    
    # Second request - should be cache HIT
    response2 = client.get("/api/stats")
    assert response2.status_code == 200, (
        f"Expected 200, got {response2.status_code}: {response2.text}"
    )
    
    cache_status_2 = response2.headers.get("X-Cache")
    assert cache_status_2 == "HIT", (
        f"Second request should have X-Cache: HIT, got X-Cache: {cache_status_2}"
    )
    
    # Both responses should have same data
    assert response1.json() == response2.json(), (
        "Cached response data should match original response"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
