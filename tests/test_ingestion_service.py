from app.services.ingestion import (
    IngestionService,
    StripeCredentialRepository,
    StripeSubscriptionSnapshotFetcher,
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


def test_ingest_persists_stripe_secret_key():
    repo = RecordingRepository()
    fetcher = RecordingFetcher()
    service = IngestionService(credential_repository=repo, metadata_fetcher=fetcher)

    response = service.ingest("sk_test_example")

    assert response == {
        "ok": True,
        "subscription_snapshot": {"customers": ["cust_123"], "subscriptions": ["sub_123"]},
    }
    assert repo.saved_keys == ["sk_test_example"]
    assert fetcher.received_keys == ["sk_test_example"]
