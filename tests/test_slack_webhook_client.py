import json

import httpx
import pytest

from app.services.slack import SlackDeliveryError, SlackWebhookClient


def test_post_message_success():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["json"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(status_code=200, text="ok")

    transport = httpx.MockTransport(handler)
    webhook_url = "https://hooks.slack.com/services/T123/B456/XYZ"
    payload = {"text": "hello"}

    with httpx.Client(transport=transport) as http_client:
        client = SlackWebhookClient(client=http_client, timeout=1.0)
        result = client.post_message(webhook_url, payload)

    assert captured["url"] == webhook_url
    assert captured["json"] == payload
    assert result == {"status_code": 200, "body": "ok"}


def test_post_message_failure_raises():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=500, text="error")

    transport = httpx.MockTransport(handler)
    webhook_url = "https://hooks.slack.com/services/T123/B456/XYZ"

    with httpx.Client(transport=transport) as http_client:
        client = SlackWebhookClient(client=http_client)
        with pytest.raises(SlackDeliveryError) as exc:
            client.post_message(webhook_url, {"text": "boom"})

    assert "500" in str(exc.value)
