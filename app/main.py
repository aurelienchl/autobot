import re

from fastapi import FastAPI, Depends
from pydantic import BaseModel, field_validator

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
def get_ingestion_service():
    # replace with real implementation later
    return object()

app = FastAPI()

@app.post("/ingest")
def ingest(req: IngestRequest, svc=Depends(get_ingestion_service)):
    # basic smoke-return so tests can import and hit the route
    return {"ok": True}
