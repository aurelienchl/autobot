from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.ingestion import (
    StripeCredentialRepository,
    StripeSubscriptionSnapshotRepository,
)
from app.services.renewals import SubscriptionRenewalAnalyzer


class RenewalDigestService:
    """Builds a digest of upcoming renewals using cached Stripe subscription snapshots."""

    def __init__(
        self,
        snapshot_repository: StripeSubscriptionSnapshotRepository,
        analyzer: Optional[SubscriptionRenewalAnalyzer] = None,
    ) -> None:
        self._snapshot_repository = snapshot_repository
        self._analyzer = analyzer or SubscriptionRenewalAnalyzer()

    def build_digest(self, stripe_secret_key: str, window_days: int = 7) -> Dict[str, Any]:
        snapshot = self._snapshot_repository.get_snapshot(stripe_secret_key)
        subscriptions = self._extract_list(snapshot, "subscriptions")
        customers = self._extract_list(snapshot, "customers")

        upcoming = self._analyzer.find_upcoming(subscriptions, window_days=window_days)

        return {
            "stripe_credential_fingerprint": StripeCredentialRepository._fingerprint(
                stripe_secret_key
            ),
            "found_snapshot": snapshot is not None,
            "subscription_count": len(subscriptions),
            "customer_count": len(customers),
            "upcoming": upcoming,
        }

    @staticmethod
    def _extract_list(snapshot: Optional[Dict[str, Any]], key: str) -> List[Any]:
        if not snapshot:
            return []

        value = snapshot.get(key)
        if isinstance(value, list):
            return list(value)
        if isinstance(value, tuple):
            return list(value)
        return []
