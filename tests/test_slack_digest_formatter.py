from app.services.slack_digest import SlackDigestFormatter


def test_format_digest_builds_slack_payload():
    formatter = SlackDigestFormatter(max_subscription_lines=2)
    digest = {
        "stripe_credential_fingerprint": "fp_123",
        "upcoming": {
            "window_days": 7,
            "total_amount_due": 12345.67,
            "upcoming_subscriptions": [
                {
                    "id": "sub_001",
                    "status": "active",
                    "current_period_end": "2024-06-01T00:00:00+00:00",
                    "amount_due": 4999,
                },
                {
                    "id": "sub_002",
                    "status": "past_due",
                    "current_period_end": "2024-06-02T00:00:00+00:00",
                    "amount_due": "1500.5",
                },
                {
                    "id": "sub_003",
                    "status": "incomplete",
                    "current_period_end": "2024-06-03T00:00:00+00:00",
                    "amount_due": None,
                },
            ],
        },
    }

    payload = formatter.format_digest(digest)

    assert payload["text"] == (
        "Renewal digest for `fp_123`\n"
        "3 upcoming subscriptions in the next 7 days | Projected total: $12,345.67"
    )

    blocks = payload["blocks"]
    assert len(blocks) == 2
    assert blocks[0]["type"] == "section"
    assert blocks[0]["text"]["text"] == (
        "*Renewal digest for* `fp_123`\n"
        "*3* upcoming subscriptions in the next 7 days | Projected total: $12,345.67"
    )
    assert blocks[1]["text"]["text"] == (
        "- `sub_001` | active | renews 2024-06-01T00:00:00+00:00 | $4,999.00 | "
        "<https://dashboard.stripe.com/subscriptions/sub_001|View in Stripe>\n"
        "- `sub_002` | past_due | renews 2024-06-02T00:00:00+00:00 | $1,500.50 | "
        "<https://dashboard.stripe.com/subscriptions/sub_002|View in Stripe>\n"
        "- ...and 1 more subscription"
    )
