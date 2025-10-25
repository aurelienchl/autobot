from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

from app.services.ingestion import (
    IngestionService,
    StripeCredentialRepository,
    StripeSubscriptionSnapshotRepository,
)
from app.services.slack import SlackWebhookRepository

# --- request models ---
class IngestRequest(BaseModel):
    stripe_secret_key: str


class ConfigureSlackWebhookRequest(BaseModel):
    stripe_secret_key: str
    webhook_url: str

# --- DI / service stub ---
credential_repository = StripeCredentialRepository()
snapshot_repository = StripeSubscriptionSnapshotRepository()
slack_webhook_repository = SlackWebhookRepository()


def get_ingestion_service():
    return IngestionService(
        credential_repository=credential_repository,
        snapshot_repository=snapshot_repository,
    )

app = FastAPI()


@app.post("/ingest")
def ingest(req: IngestRequest, svc: IngestionService = Depends(get_ingestion_service)):
    return svc.ingest(stripe_secret_key=req.stripe_secret_key)


@app.post("/slack/webhook")
def configure_slack_webhook(req: ConfigureSlackWebhookRequest):
    slack_webhook_repository.configure_webhook(
        stripe_secret_key=req.stripe_secret_key,
        webhook_url=req.webhook_url,
    )
    return {"ok": True}


@app.get("/slack/webhook/{stripe_secret_key}")
def get_slack_webhook(stripe_secret_key: str):
    stored = slack_webhook_repository.get_webhook(stripe_secret_key)
    if stored is None:
        raise HTTPException(status_code=404, detail="Slack webhook not found")
    return {
        "stripe_secret_key": stripe_secret_key,
        "webhook": {
            "stripe_credential_fingerprint": stored.stripe_credential_fingerprint,
            "webhook_url": stored.webhook_url,
            "created_at": stored.created_at.isoformat(),
            "last_configured_at": stored.last_configured_at.isoformat(),
        },
    }


@app.get("/snapshots/{stripe_secret_key}")
def get_snapshot(stripe_secret_key: str):
    snapshot = snapshot_repository.get_snapshot(stripe_secret_key)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {
        "stripe_secret_key": stripe_secret_key,
        "subscription_snapshot": snapshot,
    }


@app.get("/credentials")
def list_credentials():
    credentials = credential_repository.list_credentials()
    return {
        "credentials": [
            {
                "stripe_secret_key": credential.stripe_secret_key,
                "created_at": credential.created_at.isoformat(),
                "last_ingested_at": credential.last_ingested_at.isoformat(),
            }
            for credential in credentials
        ]
    }
