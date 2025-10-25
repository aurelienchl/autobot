from typing import List, Dict, Optional


class StripeCredentialRepository:
    """Temporary in-memory storage for Stripe credentials until persistent storage is wired up."""

    def __init__(self) -> None:
        self._keys: List[str] = []

    def save_stripe_secret_key(self, stripe_secret_key: str) -> None:
        self._keys.append(stripe_secret_key)


class StripeSubscriptionSnapshotFetcher:
    """Placeholder Stripe integration that will eventually pull customer/subscription metadata."""

    def fetch_subscription_snapshot(self, stripe_secret_key: str) -> Dict[str, List]:
        # TODO: replace with real Stripe client call
        return {"customers": [], "subscriptions": []}


class IngestionService:
    """Business logic for processing Stripe ingestion requests."""

    def __init__(
        self,
        credential_repository: StripeCredentialRepository,
        metadata_fetcher: Optional[StripeSubscriptionSnapshotFetcher] = None,
    ) -> None:
        self._credential_repository = credential_repository
        self._metadata_fetcher = metadata_fetcher or StripeSubscriptionSnapshotFetcher()

    def ingest(self, stripe_secret_key: str) -> dict:
        # TODO: persist the key securely and fetch Stripe metadata
        self._credential_repository.save_stripe_secret_key(stripe_secret_key)
        snapshot = self._metadata_fetcher.fetch_subscription_snapshot(stripe_secret_key)
        return {"ok": True, "subscription_snapshot": snapshot}
