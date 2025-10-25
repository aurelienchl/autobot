"""Domain services for Stripe ingestion."""


class IngestionService:
    """Placeholder implementation until persistence is wired up."""

    def record_stripe_secret(self, stripe_secret_key: str) -> None:
        # Future work: write the secret into encrypted storage / secrets manager.
        # For now we simply no-op to exercise the endpoint contract.
        _ = stripe_secret_key
