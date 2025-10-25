from fastapi.testclient import TestClient

from app.main import app, get_ingestion_service


class DummyIngestionService:
    def __init__(self):
        self.called_with = None

    def ingest(self, stripe_secret_key: str):
        self.called_with = stripe_secret_key
        return {
            "ok": True,
            "subscription_snapshot": {"customers": [], "subscriptions": []},
        }


def test_ingest_route_calls_service():
    dummy_service = DummyIngestionService()
    app.dependency_overrides[get_ingestion_service] = lambda: dummy_service

    try:
        client = TestClient(app)
        response = client.post("/ingest", json={"stripe_secret_key": "sk_test_123"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "subscription_snapshot": {"customers": [], "subscriptions": []},
    }
    assert dummy_service.called_with == "sk_test_123"
