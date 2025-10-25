from fastapi import FastAPI, Depends
from pydantic import BaseModel

# --- request models ---
class IngestRequest(BaseModel):
    stripe_secret_key: str

# --- DI / service stub ---
def get_ingestion_service():
    # replace with real implementation later
    return object()

app = FastAPI()

@app.post("/ingest")
def ingest(req: IngestRequest, svc=Depends(get_ingestion_service)):
    # basic smoke-return so tests can import and hit the route
    return {"ok": True}