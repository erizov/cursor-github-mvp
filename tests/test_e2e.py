import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.repositories import InMemorySelectionRepository
from backend.services import RecommendationService
from backend.routers import recommendations as rec_router
from backend.routers import reports as reports_router


@pytest.fixture()
def app_and_repo():
    app: FastAPI = create_app()
    repo = InMemorySelectionRepository()

    async def get_fake_service():
        return RecommendationService(repo)

    # Override both routers to use the shared in-memory repo
    app.dependency_overrides[rec_router.get_service] = get_fake_service
    app.dependency_overrides[reports_router.get_repo] = lambda: repo
    return app, repo


def test_end_to_end_multiple_prompts_and_usage_report(app_and_repo):
    app, _ = app_and_repo
    client = TestClient(app)

    prompts = [
        # Classification (text)
        "Classify customer reviews by sentiment with a small labeled dataset",
        # Regression (tabular)
        "Predict house prices from numerical features",
        # Clustering
        "Cluster customers into segments based on transactions",
        # Time series
        "Forecast monthly demand with trend and seasonality",
        # Anomaly detection
        "Detect anomalies in server metrics with rare spikes",
        # Recommendation system
        "Recommend items to users based on interaction history",
        # NLP transformers
        "Fine-tune a BERT model to classify support tickets by topic",
        # Vision classification
        "Image classification for plant diseases using transfer learning",
        # Object detection
        "Object detection for detecting cars and pedestrians in street images",
        # Reinforcement learning
        "Train an agent with reinforcement learning to maximize long-term rewards",
        # Causal inference
        "Estimate causal effect of a marketing campaign on sales using observational data",
        # Dimensionality reduction
        "Visualize high-dimensional embeddings with PCA and UMAP",
        # Margin-based classifier (SVM)
        "Classify documents with a clear margin between classes using SVM",
        # KNN small dataset
        "Use KNN to classify iris flowers with standardized features",
        # Explicit LSTM phrasing for multi-variate sequence forecasting
        "Use LSTM to forecast a multivariate time series with long dependencies",
    ]

    for p in prompts:
        r = client.post("/api/recommend", json={"prompt": p})
        assert r.status_code == 200
        body = r.json()
        assert body.get("recommendations")

    rep = client.get("/api/reports/usage")
    assert rep.status_code == 200
    data = rep.json()
    assert data["total"] == len(prompts)
    assert sum(c["count"] for c in data["counts"]) == len(prompts)
    # Expect multiple algorithms to appear as top recommendations across diverse prompts
    assert len(data["counts"]) >= 6


