from fastapi.testclient import TestClient

from app import main
from app.services.ingestion import StripeSubscriptionSnapshotRepository


def test_get_snapshot_returns_saved_snapshot():
    original_repo = main.snapshot_repository
    main.snapshot_repository = StripeSubscriptionSnapshotRepository()
    try:
        main.snapshot_repository.save_snapshot(
            "sk_test_key",
            {"customers": ["cust_123"], "subscriptions": ["sub_123"]},
        )
        client = TestClient(main.app)
        response = client.get("/snapshots/sk_test_key")
    finally:
        main.snapshot_repository = original_repo

    assert response.status_code == 200
    assert response.json() == {
        "stripe_secret_key": "sk_test_key",
        "subscription_snapshot": {
            "customers": ["cust_123"],
            "subscriptions": ["sub_123"],
        },
    }


def test_get_snapshot_returns_404_when_missing():
    original_repo = main.snapshot_repository
    main.snapshot_repository = StripeSubscriptionSnapshotRepository()
    try:
        client = TestClient(main.app)
        response = client.get("/snapshots/missing_key")
    finally:
        main.snapshot_repository = original_repo

    assert response.status_code == 404
    assert response.json() == {"detail": "Snapshot not found"}
