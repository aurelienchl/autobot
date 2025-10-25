class IngestionService:
    """Business logic for processing Stripe ingestion requests."""

    def ingest(self, stripe_secret_key: str) -> dict:
        # TODO: persist the key securely and fetch Stripe metadata
        return {"ok": True}
