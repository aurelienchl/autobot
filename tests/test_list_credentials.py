from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import main as main_module
from app.services.ingestion import StripeCredentialRepository


def test_list_credentials_returns_saved_metadata():
    fixed_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    repo = StripeCredentialRepository(clock=lambda: fixed_time)

    original_repo = main_module.credential_repository
    main_module.credential_repository = repo

    try:
        repo.save_stripe_secret_key("sk_test_dummy")

        with TestClient(main_module.app) as client:
            response = client.get("/credentials")
    finally:
        main_module.credential_repository = original_repo

    assert response.status_code == 200
    assert response.json() == {
        "credentials": [
            {
                "stripe_secret_key": "sk_test_dummy",
                "created_at": "2024-01-01T00:00:00+00:00",
                "last_ingested_at": "2024-01-01T00:00:00+00:00",
            }
        ]
    }
