"""Domain services for Stripe ingestion."""

import hashlib
from typing import Protocol


class StripeSecretRepository(Protocol):
    """Persistence boundary for storing Stripe secrets securely."""

    def store_hashed_secret(self, hashed_secret: str) -> None:
        ...


class InMemoryStripeSecretRepository:
    """Non-production repository that keeps hashed secrets in memory."""

    def __init__(self) -> None:
        self._hashed_secrets: list[str] = []

    def store_hashed_secret(self, hashed_secret: str) -> None:
        self._hashed_secrets.append(hashed_secret)

    @property
    def hashed_secrets(self) -> list[str]:
        # Expose a copy for inspection in tests without leaking mutability.
        return list(self._hashed_secrets)


class IngestionService:
    """Hash Stripe secrets before delegating to the persistence layer."""

    def __init__(self, repository: StripeSecretRepository) -> None:
        self._repository = repository

    def record_stripe_secret(self, stripe_secret_key: str) -> None:
        hashed_secret = hashlib.sha256(stripe_secret_key.encode("utf-8")).hexdigest()
        self._repository.store_hashed_secret(hashed_secret)
