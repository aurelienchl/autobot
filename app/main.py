from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

from app.services.ingestion import (
    IngestionService,
    StripeCredentialRepository,
    StripeSubscriptionSnapshotRepository,
)

# --- request models ---
class IngestRequest(BaseModel):
    stripe_secret_key: str

# --- DI / service stub ---
credential_repository = StripeCredentialRepository()
snapshot_repository = StripeSubscriptionSnapshotRepository()


def get_ingestion_service():
    return IngestionService(
        credential_repository=credential_repository,
        snapshot_repository=snapshot_repository,
    )

app = FastAPI()


@app.post("/ingest")
def ingest(req: IngestRequest, svc: IngestionService = Depends(get_ingestion_service)):
    return svc.ingest(stripe_secret_key=req.stripe_secret_key)


@app.get("/snapshots/{stripe_secret_key}")
def get_snapshot(stripe_secret_key: str):
    snapshot = snapshot_repository.get_snapshot(stripe_secret_key)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {
        "stripe_secret_key": stripe_secret_key,
        "subscription_snapshot": snapshot,
    }
