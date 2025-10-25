from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app import main as main_module
from app.services.digest import RenewalDigestService
from app.services.ingestion import (
    StripeCredentialRepository,
    StripeSubscriptionSnapshotRepository,
)
from app.services.renewals import SubscriptionRenewalAnalyzer


def test_get_digest_endpoint_returns_digest_summary():
    stripe_secret_key = "sk_test_digest"
    as_of = datetime(2024, 6, 1, tzinfo=timezone.utc)
    period_inside_window = as_of + timedelta(days=3)
    period_outside_window = as_of + timedelta(days=10)

    snapshot_repository = StripeSubscriptionSnapshotRepository()
    snapshot_repository.save_snapshot(
        stripe_secret_key,
        {
            "customers": [{"id": "cus_123"}],
            "subscriptions": [
                {
                    "id": "sub_in_window",
                    "current_period_end": period_inside_window.isoformat(),
                    "status": "active",
                    "amount_due": 2500,
                },
                {
                    "id": "sub_outside_window",
                    "current_period_end": period_outside_window.isoformat(),
                    "status": "active",
                    "amount_due": 5000,
                },
            ],
        },
    )

    analyzer = SubscriptionRenewalAnalyzer(clock=lambda: as_of)
    digest_service = RenewalDigestService(
        snapshot_repository=snapshot_repository,
        analyzer=analyzer,
    )

    original_override = main_module.app.dependency_overrides.get(
        main_module.get_digest_service
    )
    main_module.app.dependency_overrides[main_module.get_digest_service] = (
        lambda: digest_service
    )

    try:
        with TestClient(main_module.app) as client:
            response = client.get("/digest/sk_test_digest?window_days=5")
    finally:
        if original_override is None:
            main_module.app.dependency_overrides.pop(
                main_module.get_digest_service, None
            )
        else:
            main_module.app.dependency_overrides[
                main_module.get_digest_service
            ] = original_override

    assert response.status_code == 200
    body = response.json()
    fingerprint = StripeCredentialRepository._fingerprint(stripe_secret_key)
    assert body["stripe_credential_fingerprint"] == fingerprint
    assert body["found_snapshot"] is True
    assert body["customer_count"] == 1
    assert body["subscription_count"] == 2

    upcoming = body["upcoming"]
    assert upcoming["as_of"] == as_of.isoformat()
    assert upcoming["window_days"] == 5
    assert upcoming["total_amount_due"] == 2500.0
    assert upcoming["upcoming_subscriptions"] == [
        {
            "id": "sub_in_window",
            "current_period_end": period_inside_window.isoformat(),
            "status": "active",
            "amount_due": 2500.0,
        }
    ]


def test_get_digest_endpoint_handles_missing_snapshot():
    stripe_secret_key = "sk_missing_digest"
    as_of = datetime(2024, 6, 1, tzinfo=timezone.utc)

    snapshot_repository = StripeSubscriptionSnapshotRepository()
    analyzer = SubscriptionRenewalAnalyzer(clock=lambda: as_of)
    digest_service = RenewalDigestService(
        snapshot_repository=snapshot_repository,
        analyzer=analyzer,
    )

    original_override = main_module.app.dependency_overrides.get(
        main_module.get_digest_service
    )
    main_module.app.dependency_overrides[main_module.get_digest_service] = (
        lambda: digest_service
    )

    try:
        with TestClient(main_module.app) as client:
            response = client.get("/digest/sk_missing_digest")
    finally:
        if original_override is None:
            main_module.app.dependency_overrides.pop(
                main_module.get_digest_service, None
            )
        else:
            main_module.app.dependency_overrides[
                main_module.get_digest_service
            ] = original_override

    assert response.status_code == 200
    body = response.json()
    fingerprint = StripeCredentialRepository._fingerprint(stripe_secret_key)
    assert body["stripe_credential_fingerprint"] == fingerprint
    assert body["found_snapshot"] is False
    assert body["customer_count"] == 0
    assert body["subscription_count"] == 0

    upcoming = body["upcoming"]
    assert upcoming["as_of"] == as_of.isoformat()
    assert upcoming["window_days"] == 7
    assert upcoming["total_amount_due"] == 0.0
    assert upcoming["upcoming_subscriptions"] == []
