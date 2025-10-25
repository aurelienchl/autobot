from datetime import datetime, timezone

from app.services.renewals import SubscriptionRenewalAnalyzer


def test_find_upcoming_filters_by_window_and_sums_amounts():
    as_of = datetime(2024, 6, 1, tzinfo=timezone.utc)
    analyzer = SubscriptionRenewalAnalyzer(clock=lambda: as_of)

    subscriptions = [
        {
            "id": "sub_due_within_window",
            "current_period_end": "2024-06-05T12:00:00Z",
            "status": "active",
            "amount_due": 1200,
        },
        {
            "id": "sub_outside_window",
            "current_period_end": "2024-06-20T00:00:00+00:00",
            "status": "active",
            "amount_due": 800,
        },
        {
            "id": "sub_without_amount",
            "current_period_end": datetime(2024, 6, 3, tzinfo=timezone.utc),
            "status": "trialing",
        },
        {
            "id": "sub_with_unparseable_timestamp",
            "current_period_end": "not-a-date",
            "status": "active",
            "amount_due": "100.00",
        },
        {
            "id": "sub_numeric_timestamp",
            "current_period_end": as_of.timestamp() + 2 * 24 * 60 * 60,
            "status": "active",
            "amount_due": "1300",
        },
    ]

    result = analyzer.find_upcoming(subscriptions, window_days=7)

    assert result["window_days"] == 7
    assert result["as_of"] == as_of.isoformat()

    upcoming_ids = [item["id"] for item in result["upcoming_subscriptions"]]
    assert upcoming_ids == ["sub_due_within_window", "sub_without_amount", "sub_numeric_timestamp"]

    assert result["total_amount_due"] == 2500.0

    numeric_entry = next(item for item in result["upcoming_subscriptions"] if item["id"] == "sub_numeric_timestamp")
    assert numeric_entry["amount_due"] == 1300.0
