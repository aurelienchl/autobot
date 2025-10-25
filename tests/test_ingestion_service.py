from app.services.ingestion import (
    IngestionService,
    StripeCredentialRepository,
    StripeSubscriptionSnapshotFetcher,
    StripeSubscriptionSnapshotRepository,
)


class RecordingRepository(StripeCredentialRepository):
    def __init__(self):
        super().__init__()
        self.saved_keys = []

    def save_stripe_secret_key(self, stripe_secret_key: str) -> None:
        super().save_stripe_secret_key(stripe_secret_key)
        self.saved_keys.append(stripe_secret_key)


class RecordingFetcher(StripeSubscriptionSnapshotFetcher):
    def __init__(self):
        self.received_keys = []

    def fetch_subscription_snapshot(self, stripe_secret_key: str):
        self.received_keys.append(stripe_secret_key)
        return {"customers": ["cust_123"], "subscriptions": ["sub_123"]}


class RecordingSnapshotRepository(StripeSubscriptionSnapshotRepository):
    def __init__(self):
        super().__init__()
        self.saved = []

    def save_snapshot(self, stripe_secret_key: str, snapshot):
        super().save_snapshot(stripe_secret_key, snapshot)
        self.saved.append((stripe_secret_key, snapshot))


def test_ingest_persists_stripe_secret_key():
    repo = RecordingRepository()
    fetcher = RecordingFetcher()
    snapshot_repo = RecordingSnapshotRepository()
    service = IngestionService(
        credential_repository=repo,
        metadata_fetcher=fetcher,
        snapshot_repository=snapshot_repo,
    )

    response = service.ingest("sk_test_example")

    assert response == {
        "ok": True,
        "subscription_snapshot": {"customers": ["cust_123"], "subscriptions": ["sub_123"]},
    }
    assert repo.saved_keys == ["sk_test_example"]
    assert fetcher.received_keys == ["sk_test_example"]
    assert snapshot_repo.saved == [
        ("sk_test_example", {"customers": ["cust_123"], "subscriptions": ["sub_123"]})
    ]


class RecordingStripeClient:
    def __init__(self):
        self.keys = []
        self.payload = {
            "customers": ["cust_abc"],
            "subscriptions": ["sub_abc"],
        }

    def fetch_customer_and_subscription_data(self, stripe_secret_key: str):
        self.keys.append(stripe_secret_key)
        return self.payload


def test_snapshot_fetcher_delegates_to_client_and_copies_payload():
    client = RecordingStripeClient()
    fetcher = StripeSubscriptionSnapshotFetcher(client=client)

    snapshot = fetcher.fetch_subscription_snapshot("sk_test_key")

    assert client.keys == ["sk_test_key"]
    assert snapshot == client.payload
    assert snapshot["customers"] is not client.payload["customers"]
    assert snapshot["subscriptions"] is not client.payload["subscriptions"]

    snapshot["customers"].append("cust_mutated")
    assert client.payload["customers"] == ["cust_abc"]
