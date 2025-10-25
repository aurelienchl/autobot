import hashlib

from fastapi.testclient import TestClient

from app.main import app, get_ingestion_service
from app.services.ingestion import IngestionService, InMemoryStripeSecretRepository

client = TestClient(app)


def test_ingest_accepts_valid_key():
    response = client.post("/ingest", json={"stripe_secret_key": "sk_test_" + "a" * 24})
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_ingest_rejects_invalid_key():
    response = client.post("/ingest", json={"stripe_secret_key": "invalid"})
    assert response.status_code == 422


def test_ingest_passes_clean_key_to_service():
    captured = {}

    class CaptureService:
        def record_stripe_secret(self, stripe_secret_key: str) -> None:
            captured["key"] = stripe_secret_key

    app.dependency_overrides[get_ingestion_service] = lambda: CaptureService()
    try:
        response = client.post(
            "/ingest", json={"stripe_secret_key": "  sk_test_" + "b" * 24 + "   "}
        )
    finally:
        app.dependency_overrides.pop(get_ingestion_service, None)

    assert response.status_code == 200
    assert captured["key"] == "sk_test_" + "b" * 24


def test_ingest_hashes_secret_before_storage():
    repository = InMemoryStripeSecretRepository()
    service = IngestionService(repository)
    app.dependency_overrides[get_ingestion_service] = lambda: service
    secret = "sk_test_" + "c" * 24
    try:
        response = client.post("/ingest", json={"stripe_secret_key": secret})
    finally:
        app.dependency_overrides.pop(get_ingestion_service, None)

    assert response.status_code == 200
    expected_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    assert repository.hashed_secrets == [expected_hash]
