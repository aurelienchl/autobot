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


class StripeSubscriptionSnapshotRepository:
    """Temporary in-memory storage for Stripe subscription snapshots until persistence is wired up."""

    def __init__(self) -> None:
        self._snapshots: Dict[str, Dict[str, List]] = {}

    def save_snapshot(self, stripe_secret_key: str, snapshot: Dict[str, List]) -> None:
        self._snapshots[stripe_secret_key] = {
            key: list(value) if isinstance(value, list) else value
            for key, value in snapshot.items()
        }


class IngestionService:
    """Business logic for processing Stripe ingestion requests."""

    def __init__(
        self,
        credential_repository: StripeCredentialRepository,
        metadata_fetcher: Optional[StripeSubscriptionSnapshotFetcher] = None,
        snapshot_repository: Optional[StripeSubscriptionSnapshotRepository] = None,
    ) -> None:
        self._credential_repository = credential_repository
        self._metadata_fetcher = metadata_fetcher or StripeSubscriptionSnapshotFetcher()
        self._snapshot_repository = snapshot_repository or StripeSubscriptionSnapshotRepository()

    def ingest(self, stripe_secret_key: str) -> dict:
        # TODO: persist the key securely and fetch Stripe metadata
        self._credential_repository.save_stripe_secret_key(stripe_secret_key)
        snapshot = self._metadata_fetcher.fetch_subscription_snapshot(stripe_secret_key)
        self._snapshot_repository.save_snapshot(stripe_secret_key, snapshot)
        return {"ok": True, "subscription_snapshot": snapshot}
