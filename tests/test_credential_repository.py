from datetime import datetime, timedelta, timezone
from itertools import chain, repeat

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
    assert stored.last_ingested_at == stored.created_at

    credentials.clear()
    assert len(repo.list_credentials()) == 1


def test_saving_existing_key_updates_last_ingested_at_without_duplicating():
    first_timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    refreshed_timestamp = first_timestamp + timedelta(minutes=5)
    clock_values = chain([first_timestamp, refreshed_timestamp], repeat(refreshed_timestamp))
    repo = StripeCredentialRepository(clock=lambda: next(clock_values))

    repo.save_stripe_secret_key("sk_test_example")
    initial_snapshot = repo.list_credentials()[0]

    repo.save_stripe_secret_key("sk_test_example")
    refreshed_snapshot = repo.list_credentials()[0]

    assert len(repo.list_credentials()) == 1
    assert refreshed_snapshot.created_at == initial_snapshot.created_at == first_timestamp
    assert refreshed_snapshot.last_ingested_at == refreshed_timestamp
    assert refreshed_snapshot.last_ingested_at >= initial_snapshot.last_ingested_at
