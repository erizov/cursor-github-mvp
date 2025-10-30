import asyncio
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.repositories import InMemorySelectionRepository, SelectionRepository
from backend.routers import recommendations as rec_router
from backend.services import RecommendationService
from backend.routers import reports as reports_router


@pytest.fixture()
def app_with_fake_repo():
    app: FastAPI = create_app()

    fake_repo = InMemorySelectionRepository()

    async def get_fake_service():
        return RecommendationService(fake_repo)

    # Override dependencies for tests (recommendations and reports)
    app.dependency_overrides[rec_router.get_service] = get_fake_service
    app.dependency_overrides[reports_router.get_repo] = lambda: fake_repo
    return app, fake_repo


def test_recommend_and_counts(app_with_fake_repo):
    app, repo = app_with_fake_repo
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


