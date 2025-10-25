import re

from fastapi import Depends, FastAPI
from pydantic import BaseModel, field_validator

from app.services.ingestion import IngestionService, InMemoryStripeSecretRepository

STRIPE_SECRET_KEY_PATTERN = re.compile(r"^sk_(live|test)_[A-Za-z0-9]{16,}$")

# --- request models ---
class IngestRequest(BaseModel):
    stripe_secret_key: str

    @field_validator("stripe_secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        cleaned = value.strip()
        if not STRIPE_SECRET_KEY_PATTERN.fullmatch(cleaned):
            raise ValueError("Provide a valid Stripe secret key.")
        return cleaned

# --- DI / service stub ---
def get_ingestion_service() -> IngestionService:
    return IngestionService(InMemoryStripeSecretRepository())

app = FastAPI()

@app.post("/ingest")
def ingest(req: IngestRequest, svc: IngestionService = Depends(get_ingestion_service)):
    svc.record_stripe_secret(req.stripe_secret_key)
    return {"ok": True}
