import json
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.repositories import InMemorySelectionRepository
from backend.services import RecommendationService
from backend.routers import recommendations as rec_router
from backend.routers import reports as reports_router


def main() -> None:
    app: FastAPI = create_app()
    repo = InMemorySelectionRepository()

    async def get_fake_service():
        return RecommendationService(repo)

    app.dependency_overrides[rec_router.get_service] = get_fake_service
    app.dependency_overrides[reports_router.get_repo] = lambda: repo

    client = TestClient(app)

    prompts = [
        "Classify customer reviews by sentiment with a small labeled dataset",
        "Predict house prices from numerical features",
        "Cluster customers into segments based on transactions",
        "Detect anomalies in time series",
        "Build a recommender for similar products",
    ]

    for p in prompts:
        r = client.post("/api/recommend", json={"prompt": p})
        assert r.status_code == 200

    rep = client.get("/api/reports/usage")
    data = rep.json()

    total = data.get("total", 0)
    counts = data.get("counts", [])
    counts_sorted = sorted(counts, key=lambda c: (-c["count"], c["algorithm"]))

    enhanced = {
        "total": total,
        "distinct_algorithms": len(counts_sorted),
        "top": counts_sorted[:3],
        "percentages": [
            {
                "algorithm": c["algorithm"],
                "count": c["count"],
                "percent": round((c["count"] / total) * 100, 2) if total else 0.0,
            }
            for c in counts_sorted
        ],
    }

    print(json.dumps(enhanced, indent=2))


if __name__ == "__main__":
    main()
