from fastapi import FastAPI, Depends
from pydantic import BaseModel

from app.services.ingestion import IngestionService

# --- request models ---
class IngestRequest(BaseModel):
    stripe_secret_key: str

# --- DI / service stub ---
def get_ingestion_service():
    return IngestionService()

app = FastAPI()

@app.post("/ingest")
def ingest(req: IngestRequest, svc: IngestionService = Depends(get_ingestion_service)):
    return svc.ingest(stripe_secret_key=req.stripe_secret_key)
