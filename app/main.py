from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

from app.services.digest import RenewalDigestService
from app.services.ingestion import (
    IngestionService,
    StripeCredentialRepository,
    StripeSubscriptionSnapshotRepository,
)
from app.services.slack import SlackWebhookClient, SlackWebhookRepository
from app.services.slack_delivery import SlackDigestDeliveryService
from app.services.slack_digest import SlackDigestFormatter

# --- request models ---
class IngestRequest(BaseModel):
    stripe_secret_key: str


class ConfigureSlackWebhookRequest(BaseModel):
    stripe_secret_key: str
    webhook_url: str


class DeliverSlackDigestRequest(BaseModel):
    stripe_secret_key: str
    window_days: int = 7

# --- DI / service stub ---
credential_repository = StripeCredentialRepository()
snapshot_repository = StripeSubscriptionSnapshotRepository()
slack_webhook_repository = SlackWebhookRepository()
slack_webhook_client = SlackWebhookClient()
slack_digest_formatter = SlackDigestFormatter()


def get_ingestion_service():
    return IngestionService(
        credential_repository=credential_repository,
        snapshot_repository=snapshot_repository,
    )


def get_digest_service():
    return RenewalDigestService(
        snapshot_repository=snapshot_repository,
    )


def get_slack_digest_delivery_service():
    return SlackDigestDeliveryService(
        digest_service=get_digest_service(),
        webhook_repository=slack_webhook_repository,
        slack_client=slack_webhook_client,
        formatter=slack_digest_formatter,
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


@app.get("/digest/{stripe_secret_key}")
def get_digest(
    stripe_secret_key: str,
    window_days: int = 7,
    svc: RenewalDigestService = Depends(get_digest_service),
):
    return svc.build_digest(
        stripe_secret_key=stripe_secret_key,
        window_days=window_days,
    )


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


@app.post("/slack/digest")
def deliver_slack_digest(
    req: DeliverSlackDigestRequest,
    svc: SlackDigestDeliveryService = Depends(get_slack_digest_delivery_service),
):
    return svc.deliver_digest(
        stripe_secret_key=req.stripe_secret_key,
        window_days=req.window_days,
    )
