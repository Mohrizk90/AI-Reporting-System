"""Email KPIs computed from normalized EmailDataset."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mvp.email_schema import EmailDataset, EmailCampaignRow


def safe_div(num: float | int | None, den: float | int | None) -> float | None:
    if num is None or den is None or den == 0:
        return None
    return float(num) / float(den)


def pct(num: float | int | None, den: float | int | None) -> float | None:
    v = safe_div(num, den)
    if v is None:
        return None
    return v * 100.0


@dataclass
class EmailAggregateKPIs:
    sent: int | None
    delivered: int | None
    opens_unique: int | None
    clicks_unique: int | None
    hard_bounces: int | None
    soft_bounces: int | None
    unsubscribes: int | None
    spam_complaints: int | None

    delivery_rate_pct: float | None
    open_rate_pct: float | None
    ctr_pct: float | None  # clicks / delivered
    ctor_pct: float | None  # clicks / opens
    bounce_rate_pct: float | None  # (hard+soft)/sent
    unsubscribe_rate_pct: float | None  # unsub / delivered
    complaint_rate_pct: float | None  # complaints / delivered

    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sent": self.sent,
            "delivered": self.delivered,
            "opens_unique": self.opens_unique,
            "clicks_unique": self.clicks_unique,
            "hard_bounces": self.hard_bounces,
            "soft_bounces": self.soft_bounces,
            "unsubscribes": self.unsubscribes,
            "spam_complaints": self.spam_complaints,
            "delivery_rate_pct": _r(self.delivery_rate_pct),
            "open_rate_pct": _r(self.open_rate_pct),
            "ctr_pct": _r(self.ctr_pct),
            "ctor_pct": _r(self.ctor_pct),
            "bounce_rate_pct": _r(self.bounce_rate_pct),
            "unsubscribe_rate_pct": _r(self.unsubscribe_rate_pct),
            "complaint_rate_pct": _r(self.complaint_rate_pct),
            "notes": self.notes,
        }


def _sum(rows: list[EmailCampaignRow], field: str) -> int | None:
    vals = [getattr(r, field) for r in rows if getattr(r, field) is not None]
    if not vals:
        return None
    return int(sum(vals))


def _r(v: float | None) -> float | None:
    return round(v, 4) if v is not None else None


def compute_email_aggregate_kpis(ds: EmailDataset) -> EmailAggregateKPIs:
    rows = ds.rows
    sent = _sum(rows, "sent")
    delivered = _sum(rows, "delivered")
    opens_unique = _sum(rows, "opens_unique")
    clicks_unique = _sum(rows, "clicks_unique")
    hard_bounces = _sum(rows, "hard_bounces")
    soft_bounces = _sum(rows, "soft_bounces")
    unsubscribes = _sum(rows, "unsubscribes")
    spam_complaints = _sum(rows, "spam_complaints")

    bounces = (hard_bounces or 0) + (soft_bounces or 0) if (hard_bounces is not None or soft_bounces is not None) else None

    delivery_rate = pct(delivered, sent)
    open_rate = pct(opens_unique, delivered)
    ctr = pct(clicks_unique, delivered)
    ctor = pct(clicks_unique, opens_unique)
    bounce_rate = pct(bounces, sent) if bounces is not None else None
    unsub_rate = pct(unsubscribes, delivered)
    complaint_rate = pct(spam_complaints, delivered)

    notes: list[str] = []
    if ds.source == "brevo_api":
        notes.append("Rates computed from unique opens/clicks where available.")

    return EmailAggregateKPIs(
        sent=sent,
        delivered=delivered,
        opens_unique=opens_unique,
        clicks_unique=clicks_unique,
        hard_bounces=hard_bounces,
        soft_bounces=soft_bounces,
        unsubscribes=unsubscribes,
        spam_complaints=spam_complaints,
        delivery_rate_pct=delivery_rate,
        open_rate_pct=open_rate,
        ctr_pct=ctr,
        ctor_pct=ctor,
        bounce_rate_pct=bounce_rate,
        unsubscribe_rate_pct=unsub_rate,
        complaint_rate_pct=complaint_rate,
        notes=notes,
    )

