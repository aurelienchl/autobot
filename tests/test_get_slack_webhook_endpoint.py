import hashlib
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import main as main_module
from app.services.slack import SlackWebhookRepository


def test_get_slack_webhook_endpoint_returns_stored_webhook():
    fixed_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    repo = SlackWebhookRepository(clock=lambda: fixed_time)
    repo.configure_webhook(
        stripe_secret_key="sk_test_dummy",
        webhook_url="https://hooks.slack.com/services/dummy",
    )

    original_repo = main_module.slack_webhook_repository
    main_module.slack_webhook_repository = repo

    try:
        with TestClient(main_module.app) as client:
            response = client.get("/slack/webhook/sk_test_dummy")
    finally:
        main_module.slack_webhook_repository = original_repo

    assert response.status_code == 200
    fingerprint = hashlib.sha256("sk_test_dummy".encode("utf-8")).hexdigest()
    assert response.json() == {
        "stripe_secret_key": "sk_test_dummy",
        "webhook": {
            "stripe_credential_fingerprint": fingerprint,
            "webhook_url": "https://hooks.slack.com/services/dummy",
            "created_at": "2024-01-01T00:00:00+00:00",
            "last_configured_at": "2024-01-01T00:00:00+00:00",
        },
    }


def test_get_slack_webhook_endpoint_returns_404_when_missing():
    repo = SlackWebhookRepository()

    original_repo = main_module.slack_webhook_repository
    main_module.slack_webhook_repository = repo

    try:
        with TestClient(main_module.app) as client:
            response = client.get("/slack/webhook/sk_missing")
    finally:
        main_module.slack_webhook_repository = original_repo

    assert response.status_code == 404
    assert response.json() == {"detail": "Slack webhook not found"}
