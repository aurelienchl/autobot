from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.digest import RenewalDigestService
from app.services.ingestion import StripeCredentialRepository
from app.services.slack import (
    SlackDeliveryError,
    SlackWebhookClient,
    SlackWebhookRepository,
)
from app.services.slack_digest import SlackDigestFormatter


class SlackDigestDeliveryService:
    """Coordinates digest generation and Slack delivery for a Stripe account."""

    def __init__(
        self,
        digest_service: RenewalDigestService,
        webhook_repository: SlackWebhookRepository,
        slack_client: SlackWebhookClient,
        formatter: Optional[SlackDigestFormatter] = None,
    ) -> None:
        self._digest_service = digest_service
        self._webhook_repository = webhook_repository
        self._slack_client = slack_client
        self._formatter = formatter or SlackDigestFormatter()

    def deliver_digest(self, stripe_secret_key: str, window_days: int = 7) -> Dict[str, Any]:
        fingerprint = StripeCredentialRepository._fingerprint(stripe_secret_key)
        webhook = self._webhook_repository.get_webhook(stripe_secret_key)

        if webhook is None:
            return {
                "ok": False,
                "stripe_credential_fingerprint": fingerprint,
                "reason": "slack_webhook_not_configured",
            }

        digest = self._digest_service.build_digest(
            stripe_secret_key=stripe_secret_key,
            window_days=window_days,
        )
        payload = self._formatter.format_digest(digest)
        try:
            slack_response = self._slack_client.post_message(webhook.webhook_url, payload)
        except SlackDeliveryError as exc:
            return {
                "ok": False,
                "stripe_credential_fingerprint": webhook.stripe_credential_fingerprint,
                "reason": "slack_delivery_failed",
                "digest": digest,
                "slack_payload": payload,
                "error": str(exc),
            }

        return {
            "ok": True,
            "stripe_credential_fingerprint": webhook.stripe_credential_fingerprint,
            "digest": digest,
            "slack_payload": payload,
            "slack_response": slack_response,
        }
