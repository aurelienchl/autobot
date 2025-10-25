from app.services.ingestion import IngestionService, StripeCredentialRepository


class RecordingRepository(StripeCredentialRepository):
    def __init__(self):
        super().__init__()
        self.saved_keys = []

    def save_stripe_secret_key(self, stripe_secret_key: str) -> None:
        super().save_stripe_secret_key(stripe_secret_key)
        self.saved_keys.append(stripe_secret_key)


def test_ingest_persists_stripe_secret_key():
    repo = RecordingRepository()
    service = IngestionService(credential_repository=repo)

    response = service.ingest("sk_test_example")

    assert response == {"ok": True}
    assert repo.saved_keys == ["sk_test_example"]
