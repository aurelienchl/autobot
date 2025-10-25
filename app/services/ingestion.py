import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional


@dataclass
class StoredStripeCredential:
    """DTO representing a saved Stripe credential fingerprint and metadata."""

    stripe_secret_key: str
    created_at: datetime
    last_ingested_at: datetime

    @classmethod
    def new(cls, stripe_secret_key: str, now: datetime) -> "StoredStripeCredential":
        return cls(
            stripe_secret_key=stripe_secret_key,
            created_at=now,
            last_ingested_at=now,
        )

    def touch(self, now: datetime) -> None:
        self.last_ingested_at = now


class StripeCredentialRepository:
    """Temporary in-memory storage for Stripe credentials until persistent storage is wired up."""

    def __init__(self, clock: Optional[Callable[[], datetime]] = None) -> None:
        self._clock = clock or (lambda: datetime.now(tz=timezone.utc))
        self._credentials: Dict[str, StoredStripeCredential] = {}

    def save_stripe_secret_key(self, stripe_secret_key: str) -> None:
        now = self._clock()
        fingerprint = self._fingerprint(stripe_secret_key)
        existing = self._credentials.get(fingerprint)
        if existing is None:
            self._credentials[fingerprint] = StoredStripeCredential.new(
                stripe_secret_key=fingerprint,
                now=now,
            )
        else:
            existing.touch(now)

    @staticmethod
    def _fingerprint(stripe_secret_key: str) -> str:
        """Returns a deterministic fingerprint so we avoid storing raw secrets."""
        return hashlib.sha256(stripe_secret_key.encode("utf-8")).hexdigest()

    def list_credentials(self) -> List[StoredStripeCredential]:
        return [
            StoredStripeCredential(
                stripe_secret_key=credential.stripe_secret_key,
                created_at=credential.created_at,
                last_ingested_at=credential.last_ingested_at,
            )
            for credential in self._credentials.values()
        ]


class StripeAPIClient:
    """Placeholder Stripe API client that will eventually call Stripe's SDK."""

    def fetch_customer_and_subscription_data(
        self, stripe_secret_key: str
    ) -> Dict[str, List]:
        # TODO: replace with real Stripe client call
        return {"customers": [], "subscriptions": []}


class StripeSubscriptionSnapshotFetcher:
    """Placeholder Stripe integration that will eventually pull customer/subscription metadata."""

    def __init__(self, client: Optional[StripeAPIClient] = None) -> None:
        self._client = client or StripeAPIClient()

    def fetch_subscription_snapshot(self, stripe_secret_key: str) -> Dict[str, List]:
        raw_snapshot = (
            self._client.fetch_customer_and_subscription_data(stripe_secret_key) or {}
        )

        customers = list(raw_snapshot.get("customers", []))
        subscriptions = list(raw_snapshot.get("subscriptions", []))
        return {"customers": customers, "subscriptions": subscriptions}


class StripeSubscriptionSnapshotRepository:
    """Temporary in-memory storage for Stripe subscription snapshots until persistence is wired up."""

    def __init__(self) -> None:
        self._snapshots: Dict[str, Dict[str, List]] = {}

    def save_snapshot(self, stripe_secret_key: str, snapshot: Dict[str, List]) -> None:
        self._snapshots[stripe_secret_key] = {
            key: list(value) if isinstance(value, list) else value
            for key, value in snapshot.items()
        }

    def get_snapshot(self, stripe_secret_key: str) -> Optional[Dict[str, List]]:
        snapshot = self._snapshots.get(stripe_secret_key)
        if snapshot is None:
            return None
        return {
            key: list(value) if isinstance(value, list) else value
            for key, value in snapshot.items()
        }

    def list_snapshots(self) -> Dict[str, Dict[str, List]]:
        return {
            key: {
                inner_key: list(inner_value) if isinstance(inner_value, list) else inner_value
                for inner_key, inner_value in snapshot.items()
            }
            for key, snapshot in self._snapshots.items()
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
