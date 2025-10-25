from datetime import datetime, timezone

from app.services.ingestion import StripeCredentialRepository
from app.services.slack import StoredSlackWebhook
from app.services.slack_delivery import SlackDigestDeliveryService


class RecordingDigestService:
    def __init__(self, digest):
        self.digest = digest
        self.calls = []

    def build_digest(self, stripe_secret_key: str, window_days: int):
        self.calls.append((stripe_secret_key, window_days))
        return self.digest


class RecordingFormatter:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def format_digest(self, digest):
        self.calls.append(digest)
        return self.payload


class RecordingSlackClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post_message(self, webhook_url, payload):
        self.calls.append((webhook_url, payload))
        return self.response


class RecordingWebhookRepository:
    def __init__(self, webhook):
        self.webhook = webhook
        self.keys = []

    def get_webhook(self, stripe_secret_key: str):
        self.keys.append(stripe_secret_key)
        return self.webhook


def test_deliver_digest_sends_payload_via_slack_client():
    stripe_secret_key = "sk_test_deliver"
    fingerprint = StripeCredentialRepository._fingerprint(stripe_secret_key)
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    webhook = StoredSlackWebhook.new(
        fingerprint=fingerprint,
        webhook_url="https://hooks.slack.com/services/example",
        now=now,
    )

    digest_payload = {"digest": "data"}
    formatter_payload = {"text": "hello", "blocks": []}
    slack_response = {"status_code": 200, "body": "ok"}

    digest_service = RecordingDigestService(digest_payload)
    formatter = RecordingFormatter(formatter_payload)
    slack_client = RecordingSlackClient(slack_response)
    webhook_repository = RecordingWebhookRepository(webhook)

    service = SlackDigestDeliveryService(
        digest_service=digest_service,
        webhook_repository=webhook_repository,
        slack_client=slack_client,
        formatter=formatter,
    )

    result = service.deliver_digest(stripe_secret_key=stripe_secret_key, window_days=3)

    assert result == {
        "ok": True,
        "stripe_credential_fingerprint": fingerprint,
        "digest": digest_payload,
        "slack_payload": formatter_payload,
        "slack_response": slack_response,
    }
    assert digest_service.calls == [(stripe_secret_key, 3)]
    assert formatter.calls == [digest_payload]
    assert slack_client.calls == [
        ("https://hooks.slack.com/services/example", formatter_payload)
    ]
    assert webhook_repository.keys == [stripe_secret_key]


def test_deliver_digest_short_circuits_when_webhook_missing():
    stripe_secret_key = "sk_test_missing"
    fingerprint = StripeCredentialRepository._fingerprint(stripe_secret_key)

    digest_service = RecordingDigestService({"irrelevant": True})
    formatter = RecordingFormatter({"text": "ignored"})
    slack_client = RecordingSlackClient({"status_code": 500})
    webhook_repository = RecordingWebhookRepository(webhook=None)

    service = SlackDigestDeliveryService(
        digest_service=digest_service,
        webhook_repository=webhook_repository,
        slack_client=slack_client,
        formatter=formatter,
    )

    result = service.deliver_digest(stripe_secret_key=stripe_secret_key, window_days=5)

    assert result == {
        "ok": False,
        "stripe_credential_fingerprint": fingerprint,
        "reason": "slack_webhook_not_configured",
    }
    assert digest_service.calls == []
    assert formatter.calls == []
    assert slack_client.calls == []
    assert webhook_repository.keys == [stripe_secret_key]
