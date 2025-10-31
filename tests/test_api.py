import asyncio
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.repositories import (
    InMemorySelectionRepository,
    InMemoryUniqueRequestRepository,
    SelectionRepository,
)
from backend.routers import recommendations as rec_router
from backend.services import RecommendationService
from backend.routers import reports as reports_router


@pytest.fixture()
def app_with_fake_repo():
    app: FastAPI = create_app()

    fake_repo = InMemorySelectionRepository()
    fake_unique_repo = InMemoryUniqueRequestRepository()

    async def get_fake_service():
        return RecommendationService(fake_repo, fake_unique_repo)

    # Override dependencies for tests (recommendations and reports)
    app.dependency_overrides[rec_router.get_service] = get_fake_service
    app.dependency_overrides[reports_router.get_repo] = lambda: fake_repo
    return app, fake_repo, fake_unique_repo


def test_recommend_and_counts(app_with_fake_repo):
    app, repo, unique_repo = app_with_fake_repo
    client = TestClient(app)

    body = {"prompt": "Classify customer reviews by sentiment with small labeled data"}
    r = client.post("/api/recommend", json=body)
    assert r.status_code == 200
    data = r.json()
    assert "recommendations" in data and len(data["recommendations"]) > 0

    # Now usage report should reflect 1 selection
    r2 = client.get("/api/reports/usage")
    assert r2.status_code == 200
    rep = r2.json()
    assert rep["total"] == 1
    assert sum(c["count"] for c in rep["counts"]) == 1


def test_unique_requests(app_with_fake_repo):
    """Test that unique requests are stored correctly."""
    app, repo, unique_repo = app_with_fake_repo
    client = TestClient(app)

    prompt = "Classify customer reviews by sentiment with small labeled data"
    body = {"prompt": prompt}
    
    # First request should be stored
    r = client.post("/api/recommend", json=body)
    assert r.status_code == 200
    
    # Check unique requests
    requests = asyncio.run(unique_repo.get_all_requests())
    assert len(requests) == 1
    assert requests[0]["prompt"] == prompt
    
    # Second identical request should not create duplicate
    r2 = client.post("/api/recommend", json=body)
    assert r2.status_code == 200
    
    requests2 = asyncio.run(unique_repo.get_all_requests())
    assert len(requests2) == 1  # Still only one unique request
    
    # Different prompt should be added
    body2 = {"prompt": "Forecast monthly sales with trend and yearly seasonality"}
    r3 = client.post("/api/recommend", json=body2)
    assert r3.status_code == 200
    data3 = r3.json()
    assert "recommendations" in data3 and len(data3["recommendations"]) > 0
    
    requests3 = asyncio.run(unique_repo.get_all_requests())
    assert len(requests3) == 2  # Now two unique requests
    
    # Check counts by type
    counts = asyncio.run(unique_repo.count_by_type())
    assert len(counts) > 0


