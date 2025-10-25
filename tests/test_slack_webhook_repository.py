import hashlib
from datetime import datetime, timedelta, timezone
from itertools import chain, repeat

from app.services.slack import SlackWebhookRepository


def test_configure_webhook_saves_fingerprint_and_timestamps():
    fixed_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    repo = SlackWebhookRepository(clock=lambda: fixed_time)

    repo.configure_webhook("sk_test_dummy", "https://hooks.slack.com/services/dummy")

    stored = repo.get_webhook("sk_test_dummy")
    fingerprint = hashlib.sha256("sk_test_dummy".encode("utf-8")).hexdigest()
    assert stored is not None
    assert stored.stripe_credential_fingerprint == fingerprint
    assert stored.webhook_url == "https://hooks.slack.com/services/dummy"
    assert stored.created_at == fixed_time
    assert stored.last_configured_at == fixed_time


def test_configure_webhook_updates_existing_entry_without_duplication():
    first_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    refreshed_time = first_time + timedelta(hours=1)
    clock = chain([first_time, refreshed_time], repeat(refreshed_time))
    repo = SlackWebhookRepository(clock=lambda: next(clock))

    repo.configure_webhook("sk_test_dummy", "https://hooks.slack.com/services/initial")
    original = repo.get_webhook("sk_test_dummy")

    repo.configure_webhook("sk_test_dummy", "https://hooks.slack.com/services/updated")
    updated = repo.get_webhook("sk_test_dummy")

    assert original is not None
    assert updated is not None
    assert updated.created_at == original.created_at == first_time
    assert updated.last_configured_at == refreshed_time
    assert updated.webhook_url == "https://hooks.slack.com/services/updated"
    assert len(repo.list_webhooks()) == 1


def test_get_webhook_returns_copy():
    repo = SlackWebhookRepository(clock=lambda: datetime.now(tz=timezone.utc))

    repo.configure_webhook("sk_test_dummy", "https://hooks.slack.com/services/dummy")
    stored = repo.get_webhook("sk_test_dummy")
    assert stored is not None

    stored.webhook_url = "https://mutated"
    fresh = repo.get_webhook("sk_test_dummy")

    assert fresh is not None
    assert fresh.webhook_url == "https://hooks.slack.com/services/dummy"
