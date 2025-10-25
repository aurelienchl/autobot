from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ingest_accepts_valid_key():
    response = client.post("/ingest", json={"stripe_secret_key": "sk_test_" + "a" * 24})
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_ingest_rejects_invalid_key():
    response = client.post("/ingest", json={"stripe_secret_key": "invalid"})
    assert response.status_code == 422
