from fastapi import FastAPI, status
from pydantic import BaseModel


app = FastAPI()


class IngestRequest(BaseModel):
    stripe_api_key: str


@app.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
def ingest_credentials(payload: IngestRequest) -> dict[str, bool]:
    return {"received": True}
