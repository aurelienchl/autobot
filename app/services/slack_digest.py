from __future__ import annotations

from typing import Any, Dict, List, Sequence


class SlackDigestFormatter:
    """Formats renewal digests into Slack-compatible payloads."""

    def __init__(self, max_subscription_lines: int = 5) -> None:
        self._max_subscription_lines = max_subscription_lines

    def format_digest(self, digest: Dict[str, Any]) -> Dict[str, Any]:
        fingerprint = self._as_string(digest.get("stripe_credential_fingerprint"), fallback="unknown")
        upcoming = digest.get("upcoming") or {}
        subscriptions: Sequence[Dict[str, Any]] = list(upcoming.get("upcoming_subscriptions") or [])

        window_days = self._as_int(upcoming.get("window_days"), default=7)
        total_amount_due = self._coerce_float(upcoming.get("total_amount_due"), default=0.0)
        subscription_count = len(subscriptions)

        summary_text = self._build_summary_text(
            fingerprint=fingerprint,
            subscription_count=subscription_count,
            window_days=window_days,
            total_amount_due=total_amount_due,
        )

        detail_lines = self._build_detail_lines(subscriptions)
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": summary_text}}]
        if detail_lines:
            blocks.append(
                {"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(detail_lines)}}
            )

        return {
            "text": summary_text.replace("*", ""),
            "blocks": blocks,
        }

    def _build_summary_text(
        self,
        fingerprint: str,
        subscription_count: int,
        window_days: int,
        total_amount_due: float,
    ) -> str:
        amount_text = self._format_currency(total_amount_due)
        days_text = f"{window_days} day" if window_days == 1 else f"{window_days} days"
        return (
            f"*Renewal digest for* `{fingerprint}`\n"
            f"*{subscription_count}* upcoming subscription"
            f"{'' if subscription_count == 1 else 's'} in the next {days_text} | "
            f"Projected total: {amount_text}"
        )

    def _build_detail_lines(self, subscriptions: Sequence[Dict[str, Any]]) -> List[str]:
        lines: List[str] = []
        max_lines = min(len(subscriptions), self._max_subscription_lines)

        for index in range(max_lines):
            subscription = subscriptions[index]
            subscription_id = self._as_string(subscription.get("id"), fallback="(no id)")
            status = self._as_string(subscription.get("status"), fallback="status unknown")
            period_end = self._as_string(
                subscription.get("current_period_end"),
                fallback="date unknown",
            )
            amount_text = self._format_currency(
                self._coerce_float(subscription.get("amount_due"), default=None)
            )

            lines.append(
                f"- `{subscription_id}` | {status} | renews {period_end} | {amount_text}"
            )

        remaining = len(subscriptions) - max_lines
        if remaining > 0:
            lines.append(f"- ...and {remaining} more subscription{'s' if remaining != 1 else ''}")

        return lines

    @staticmethod
    def _as_string(value: Any, *, fallback: str) -> str:
        if value is None:
            return fallback
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or fallback
        return str(value)

    @staticmethod
    def _as_int(value: Any, *, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _coerce_float(value: Any, *, default: float | None) -> float | None:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return default
        return default

    @staticmethod
    def _format_currency(amount: float | None) -> str:
        if amount is None:
            return "n/a"
        return f"${amount:,.2f}"
