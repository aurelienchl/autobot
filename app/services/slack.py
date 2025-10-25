from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

import httpx

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


class SlackDeliveryError(Exception):
    """Raised when Slack webhook delivery fails."""


class SlackWebhookClient:
    """Send Slack messages via incoming webhook URLs."""

    def __init__(
        self,
        client: Optional[httpx.Client] = None,
        timeout: float = 5.0,
    ) -> None:
        self._client = client
        self._timeout = timeout

    def post_message(self, webhook_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self._send(webhook_url, payload)
        if response.status_code >= 400:
            raise SlackDeliveryError(
                f"Slack webhook returned {response.status_code}: {response.text}"
            )
        return {
            "status_code": response.status_code,
            "body": self._parse_body(response),
        }

    def _send(self, webhook_url: str, payload: Dict[str, Any]) -> httpx.Response:
        if self._client is not None:
            return self._client.post(webhook_url, json=payload, timeout=self._timeout)
        with httpx.Client(timeout=self._timeout) as client:
            return client.post(webhook_url, json=payload)

    @staticmethod
    def _parse_body(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text
