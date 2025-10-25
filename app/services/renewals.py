from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional


@dataclass
class UpcomingRenewal:
    """Canonical representation of an upcoming subscription renewal."""

    id: Optional[str]
    current_period_end: datetime
    status: Optional[str]
    amount_due: Optional[float]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "current_period_end": self.current_period_end.isoformat(),
            "status": self.status,
            "amount_due": self.amount_due,
        }


class SubscriptionRenewalAnalyzer:
    """Filters Stripe subscriptions for renewals approaching within a time window."""

    def __init__(self, clock: Optional[Callable[[], datetime]] = None) -> None:
        self._clock = clock or (lambda: datetime.now(tz=timezone.utc))

    def find_upcoming(
        self, subscriptions: Iterable[Dict[str, Any]], window_days: int = 7
    ) -> Dict[str, Any]:
        """Return renewals that fall within the upcoming window along with aggregate totals."""
        as_of = self._clock()
        window_end = as_of + timedelta(days=window_days)

        upcoming: List[UpcomingRenewal] = []
        total_amount_due = 0.0

        for subscription in subscriptions:
            period_end = self._parse_period_end(subscription.get("current_period_end"))
            if period_end is None or not (as_of <= period_end <= window_end):
                continue

            amount_due = self._coerce_amount(subscription.get("amount_due"))

            if amount_due is not None:
                total_amount_due += amount_due

            upcoming.append(
                UpcomingRenewal(
                    id=subscription.get("id"),
                    current_period_end=period_end,
                    status=subscription.get("status"),
                    amount_due=amount_due,
                )
            )

        return {
            "as_of": as_of.isoformat(),
            "window_days": window_days,
            "total_amount_due": total_amount_due,
            "upcoming_subscriptions": [item.as_dict() for item in upcoming],
        }

    @staticmethod
    def _parse_period_end(value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        if isinstance(value, str):
            iso_value = value.replace("Z", "+00:00") if value.endswith("Z") else value
            try:
                parsed = datetime.fromisoformat(iso_value)
            except ValueError:
                return None
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        return None

    @staticmethod
    def _coerce_amount(value: Any) -> Optional[float]:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return None
