from fastapi.testclient import TestClient
from backend.app import create_app


def test_metrics_endpoint_available():
    app = create_app()
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    # basic metric exposed by instrumentator
    assert "http_requests_total" in r.text or "http_server_requests_seconds_count" in r.text


