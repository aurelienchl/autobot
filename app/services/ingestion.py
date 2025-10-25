from typing import List


class StripeCredentialRepository:
    """Temporary in-memory storage for Stripe credentials until persistent storage is wired up."""

    def __init__(self) -> None:
        self._keys: List[str] = []

    def save_stripe_secret_key(self, stripe_secret_key: str) -> None:
        self._keys.append(stripe_secret_key)


class IngestionService:
    """Business logic for processing Stripe ingestion requests."""

    def __init__(self, credential_repository: StripeCredentialRepository) -> None:
        self._credential_repository = credential_repository

    def ingest(self, stripe_secret_key: str) -> dict:
        # TODO: persist the key securely and fetch Stripe metadata
        self._credential_repository.save_stripe_secret_key(stripe_secret_key)
        return {"ok": True}
