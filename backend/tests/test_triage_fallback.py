"""Test triage fallback behavior when provider fails."""
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.providers.triage.base import TriageProvider
from app.routes.complaints import get_complaint_service
from app.schemas.triage import TriageResult
from app.services.complaint_service import ComplaintService
from app.services.redis_service import RedisService


class TriageTimeoutError(Exception):
    """Custom exception for triage timeout."""

    pass


class AlwaysFailingProvider:
    """Provider that always raises TriageTimeoutError."""

    name = "failing-test-provider"

    def triage(self, text: str, location: str) -> TriageResult:
        """Always raises TriageTimeoutError."""
        raise TriageTimeoutError("Simulated timeout for testing")


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_fallback.db"
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
    
    # Override complaint service to inject failing provider
    def override_complaint_service(db: Session = Depends(override_get_db)):  # type: ignore[assignment]
        # Use the failing provider
        failing_provider = AlwaysFailingProvider()  # type: ignore[assignment]
        redis_service = RedisService()
        return ComplaintService(db, failing_provider, redis_service)  # type: ignore[arg-type]
    
    # Use FastAPI's dependency override system
    app.dependency_overrides[get_complaint_service] = override_complaint_service
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up overrides
    app.dependency_overrides.clear()


def test_triage_fallback_on_provider_failure(client):
    """
    Test that when triage provider fails, system falls back to rules engine.
    
    Must return 201 (not 500) and triaged_by must be "rules:fallback".
    """
    complaint_data = {
        "text": "There is a water leak on Main Street causing flooding",
        "location": "123 Main Street, Downtown",
        "reporter_contact": "test@example.com",
    }
    
    response = client.post("/api/complaints", json=complaint_data)
    
    # Must return 201, never 500 (citizen must always get success)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    
    # Parse response
    data = response.json()
    
    # Must indicate fallback occurred
    assert data["triaged_by"] == "rules:fallback", (
        f"Expected triaged_by='rules:fallback', got '{data['triaged_by']}'"
    )
    
    # Must have valid triage results from fallback
    assert data["category"] in ["water", "electricity", "sanitation", "roads", "streetlights", "other"]
    assert data["priority"] in ["high", "normal", "low"]
    assert data["status"] == "open"
    assert data["ai_summary"] is not None
    assert len(data["ai_summary"]) <= 140


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
