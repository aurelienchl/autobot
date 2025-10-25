from datetime import datetime, timedelta, timezone

from app.services.digest import RenewalDigestService
from app.services.ingestion import StripeCredentialRepository, StripeSubscriptionSnapshotRepository
from app.services.renewals import SubscriptionRenewalAnalyzer


def test_build_digest_returns_upcoming_summary():
    stripe_secret_key = "sk_test_123"
    as_of = datetime(2024, 6, 1, tzinfo=timezone.utc)

    snapshot_repository = StripeSubscriptionSnapshotRepository()
    snapshot_repository.save_snapshot(
        stripe_secret_key,
        {
            "customers": [{"id": "cus_123"}],
            "subscriptions": [
                {
                    "id": "sub_in_window",
                    "current_period_end": as_of + timedelta(days=2),
                    "amount_due": 500,
                },
                {
                    "id": "sub_outside_window",
                    "current_period_end": as_of + timedelta(days=10),
                    "amount_due": 900,
                },
            ],
        },
    )

    analyzer = SubscriptionRenewalAnalyzer(clock=lambda: as_of)
    service = RenewalDigestService(snapshot_repository=snapshot_repository, analyzer=analyzer)

    digest = service.build_digest(stripe_secret_key, window_days=7)

    assert digest["stripe_credential_fingerprint"] == StripeCredentialRepository._fingerprint(
        stripe_secret_key
    )
    assert digest["found_snapshot"] is True
    assert digest["customer_count"] == 1
    assert digest["subscription_count"] == 2

    upcoming = digest["upcoming"]
    assert upcoming["window_days"] == 7
    assert upcoming["total_amount_due"] == 500.0

    upcoming_ids = [item["id"] for item in upcoming["upcoming_subscriptions"]]
    assert upcoming_ids == ["sub_in_window"]


def test_build_digest_handles_missing_snapshot():
    stripe_secret_key = "sk_missing"
    as_of = datetime(2024, 6, 1, tzinfo=timezone.utc)

    snapshot_repository = StripeSubscriptionSnapshotRepository()
    analyzer = SubscriptionRenewalAnalyzer(clock=lambda: as_of)
    service = RenewalDigestService(snapshot_repository=snapshot_repository, analyzer=analyzer)

    digest = service.build_digest(stripe_secret_key)

    assert digest["stripe_credential_fingerprint"] == StripeCredentialRepository._fingerprint(
        stripe_secret_key
    )
    assert digest["found_snapshot"] is False
    assert digest["customer_count"] == 0
    assert digest["subscription_count"] == 0

    upcoming = digest["upcoming"]
    assert upcoming["window_days"] == 7
    assert upcoming["total_amount_due"] == 0.0
    assert upcoming["upcoming_subscriptions"] == []
