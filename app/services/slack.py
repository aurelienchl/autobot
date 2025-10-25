from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from app.services.ingestion import StripeCredentialRepository


@dataclass
class StoredSlackWebhook:
    """DTO representing a configured Slack webhook for a Stripe account."""

    stripe_credential_fingerprint: str
    webhook_url: str
    created_at: datetime
    last_configured_at: datetime

    @classmethod
    def new(
        cls,
        fingerprint: str,
        webhook_url: str,
        now: datetime,
    ) -> "StoredSlackWebhook":
        return cls(
            stripe_credential_fingerprint=fingerprint,
            webhook_url=webhook_url,
            created_at=now,
            last_configured_at=now,
        )

    def update(self, webhook_url: str, now: datetime) -> None:
        self.webhook_url = webhook_url
        self.last_configured_at = now


class SlackWebhookRepository:
    """In-memory storage for Slack webhooks keyed by Stripe credential fingerprint."""

    def __init__(self, clock: Optional[Callable[[], datetime]] = None) -> None:
        self._clock = clock or (lambda: datetime.now(tz=timezone.utc))
        self._webhooks: Dict[str, StoredSlackWebhook] = {}

    def configure_webhook(self, stripe_secret_key: str, webhook_url: str) -> None:
        fingerprint = StripeCredentialRepository._fingerprint(stripe_secret_key)
        now = self._clock()
        existing = self._webhooks.get(fingerprint)
        if existing is None:
            self._webhooks[fingerprint] = StoredSlackWebhook.new(
                fingerprint=fingerprint,
                webhook_url=webhook_url,
                now=now,
            )
        else:
            existing.update(webhook_url=webhook_url, now=now)

    def get_webhook(self, stripe_secret_key: str) -> Optional[StoredSlackWebhook]:
        fingerprint = StripeCredentialRepository._fingerprint(stripe_secret_key)
        stored = self._webhooks.get(fingerprint)
        if stored is None:
            return None
        return StoredSlackWebhook(
            stripe_credential_fingerprint=stored.stripe_credential_fingerprint,
            webhook_url=stored.webhook_url,
            created_at=stored.created_at,
            last_configured_at=stored.last_configured_at,
        )

    def list_webhooks(self) -> List[StoredSlackWebhook]:
        return [
            StoredSlackWebhook(
                stripe_credential_fingerprint=webhook.stripe_credential_fingerprint,
                webhook_url=webhook.webhook_url,
                created_at=webhook.created_at,
                last_configured_at=webhook.last_configured_at,
            )
            for webhook in self._webhooks.values()
        ]
