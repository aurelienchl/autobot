from datetime import datetime, timezone

from app.services.ingestion import StripeCredentialRepository


def test_list_credentials_returns_copy_with_timestamp():
    repo = StripeCredentialRepository()

    repo.save_stripe_secret_key("sk_test_example")

    credentials = repo.list_credentials()

    assert len(credentials) == 1
    stored = credentials[0]
    assert stored.stripe_secret_key == "sk_test_example"
    assert isinstance(stored.created_at, datetime)
    assert stored.created_at.tzinfo == timezone.utc

    credentials.clear()
    assert len(repo.list_credentials()) == 1
