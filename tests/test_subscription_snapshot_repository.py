from app.services.ingestion import StripeSubscriptionSnapshotRepository


def test_get_snapshot_returns_copy_of_saved_data():
    repo = StripeSubscriptionSnapshotRepository()
    repo.save_snapshot(
        "sk_test_key",
        {"customers": ["cust_123"], "subscriptions": ["sub_123"]},
    )

    snapshot = repo.get_snapshot("sk_test_key")

    assert snapshot == {
        "customers": ["cust_123"],
        "subscriptions": ["sub_123"],
    }
    snapshot["customers"].append("cust_456")

    assert repo.get_snapshot("sk_test_key") == {
        "customers": ["cust_123"],
        "subscriptions": ["sub_123"],
    }


def test_get_snapshot_returns_none_for_unknown_key():
    repo = StripeSubscriptionSnapshotRepository()

    assert repo.get_snapshot("sk_missing") is None
