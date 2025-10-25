import hashlib
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import main as main_module
from app.services.ingestion import (
    IngestionService,
    StripeCredentialRepository,
    StripeSubscriptionSnapshotFetcher,
    StripeSubscriptionSnapshotRepository,
)


class DummySnapshotFetcher(StripeSubscriptionSnapshotFetcher):
    def fetch_subscription_snapshot(self, stripe_secret_key: str):
        assert stripe_secret_key == "sk_test_dummy"
        return {
            "customers": [{"id": "cus_123"}],
            "subscriptions": [{"id": "sub_123"}],
        }


def test_ingest_endpoint_saves_credential_and_snapshot():
    fixed_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    credential_repo = StripeCredentialRepository(clock=lambda: fixed_time)
    snapshot_repo = StripeSubscriptionSnapshotRepository()
    fetcher = DummySnapshotFetcher()
    service = IngestionService(
        credential_repository=credential_repo,
        metadata_fetcher=fetcher,
        snapshot_repository=snapshot_repo,
    )

    original_credential_repo = main_module.credential_repository
    original_snapshot_repo = main_module.snapshot_repository
    original_override = main_module.app.dependency_overrides.get(
        main_module.get_ingestion_service
    )

    main_module.credential_repository = credential_repo
    main_module.snapshot_repository = snapshot_repo
    main_module.app.dependency_overrides[main_module.get_ingestion_service] = (
        lambda: service
    )

    try:
        with TestClient(main_module.app) as client:
            ingest_response = client.post(
                "/ingest", json={"stripe_secret_key": "sk_test_dummy"}
            )
            assert ingest_response.status_code == 200
            assert ingest_response.json() == {
                "ok": True,
                "subscription_snapshot": {
                    "customers": [{"id": "cus_123"}],
                    "subscriptions": [{"id": "sub_123"}],
                },
            }

            snapshot_response = client.get("/snapshots/sk_test_dummy")
            assert snapshot_response.status_code == 200
            assert snapshot_response.json() == {
                "stripe_secret_key": "sk_test_dummy",
                "subscription_snapshot": {
                    "customers": [{"id": "cus_123"}],
                    "subscriptions": [{"id": "sub_123"}],
                },
            }

            credentials_response = client.get("/credentials")
            fingerprint = hashlib.sha256("sk_test_dummy".encode("utf-8")).hexdigest()
            assert credentials_response.status_code == 200
            assert credentials_response.json() == {
                "credentials": [
                    {
                        "stripe_secret_key": fingerprint,
                        "created_at": "2024-01-01T00:00:00+00:00",
                        "last_ingested_at": "2024-01-01T00:00:00+00:00",
                    }
                ]
            }
    finally:
        if original_override is None:
            main_module.app.dependency_overrides.pop(
                main_module.get_ingestion_service, None
            )
        else:
            main_module.app.dependency_overrides[
                main_module.get_ingestion_service
            ] = original_override
        main_module.credential_repository = original_credential_repo
        main_module.snapshot_repository = original_snapshot_repo
