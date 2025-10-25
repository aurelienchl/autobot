from fastapi.testclient import TestClient

from app import main as main_module


class RecordingSlackDigestDeliveryService:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def deliver_digest(self, stripe_secret_key: str, window_days: int):
        self.calls.append((stripe_secret_key, window_days))
        return self.response


def _override_service(service):
    original = main_module.app.dependency_overrides.get(
        main_module.get_slack_digest_delivery_service
    )
    main_module.app.dependency_overrides[
        main_module.get_slack_digest_delivery_service
    ] = lambda: service
    return original


def _restore_service(original):
    if original is None:
        main_module.app.dependency_overrides.pop(
            main_module.get_slack_digest_delivery_service, None
        )
    else:
        main_module.app.dependency_overrides[
            main_module.get_slack_digest_delivery_service
        ] = original


def test_deliver_slack_digest_endpoint_uses_default_window_days():
    service = RecordingSlackDigestDeliveryService(response={"ok": True, "result": "sent"})
    original = _override_service(service)

    try:
        with TestClient(main_module.app) as client:
            response = client.post("/slack/digest", json={"stripe_secret_key": "sk_test_default"})
            assert response.status_code == 200
            assert response.json() == {"ok": True, "result": "sent"}
            assert service.calls == [("sk_test_default", 7)]
    finally:
        _restore_service(original)


def test_deliver_slack_digest_endpoint_forwards_window_days():
    service = RecordingSlackDigestDeliveryService(
        response={"ok": False, "reason": "slack_webhook_not_configured"}
    )
    original = _override_service(service)

    try:
        with TestClient(main_module.app) as client:
            response = client.post(
                "/slack/digest",
                json={"stripe_secret_key": "sk_test_window", "window_days": 14},
            )
            assert response.status_code == 200
            assert response.json() == {"ok": False, "reason": "slack_webhook_not_configured"}
            assert service.calls == [("sk_test_window", 14)]
    finally:
        _restore_service(original)
