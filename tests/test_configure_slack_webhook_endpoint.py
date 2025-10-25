import hashlib
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import main as main_module
from app.services.slack import SlackWebhookRepository


def test_configure_slack_webhook_endpoint_saves_webhook():
    fixed_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    repo = SlackWebhookRepository(clock=lambda: fixed_time)

    original_repo = main_module.slack_webhook_repository
    main_module.slack_webhook_repository = repo

    try:
        with TestClient(main_module.app) as client:
            response = client.post(
                "/slack/webhook",
                json={
                    "stripe_secret_key": "sk_test_dummy",
                    "webhook_url": "https://hooks.slack.com/services/dummy",
                },
            )
    finally:
        main_module.slack_webhook_repository = original_repo

    assert response.status_code == 200
    assert response.json() == {"ok": True}

    stored = repo.get_webhook("sk_test_dummy")
    fingerprint = hashlib.sha256("sk_test_dummy".encode("utf-8")).hexdigest()
    assert stored is not None
    assert stored.stripe_credential_fingerprint == fingerprint
    assert stored.webhook_url == "https://hooks.slack.com/services/dummy"
    assert stored.created_at == fixed_time
    assert stored.last_configured_at == fixed_time
