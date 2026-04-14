"""
Email reporting schema (MVP).

Supports:
- File-based exports (Excel/CSV) from ESPs
- Brevo API ingestion

Important: the sample file `Files/YOA Campaigns-1-Sep-2025-31-Mar-2026.xlsx` in this workspace
is a Meta Ads campaign export (columns like Impressions/Reach/Result indicator) and is NOT an
email export. The email Excel ingester below expects email-campaign fields (sent, delivered,
opens, clicks, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Literal


EmailSource = Literal["excel", "csv", "brevo_api"]


@dataclass
class EmailCampaignRow:
    # identity
    campaign_id: str | None
    campaign_name: str
    campaign_type: str | None  # broadcast/newsletter/sequence/trigger/cold_outreach/unknown

    # time
    sent_at: datetime | None
    report_period_start: date
    report_period_end: date

    # core counts
    sent: int | None
    delivered: int | None
    opens_unique: int | None
    clicks_unique: int | None
    hard_bounces: int | None
    soft_bounces: int | None
    unsubscribes: int | None
    spam_complaints: int | None

    # optional business metrics
    conversions: int | None = None
    revenue: float | None = None
    currency: str | None = None

    # provenance
    source: EmailSource = "excel"
    source_row_index: int | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "campaign_type": self.campaign_type,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "report_period_start": self.report_period_start.isoformat(),
            "report_period_end": self.report_period_end.isoformat(),
            "sent": self.sent,
            "delivered": self.delivered,
            "opens_unique": self.opens_unique,
            "clicks_unique": self.clicks_unique,
            "hard_bounces": self.hard_bounces,
            "soft_bounces": self.soft_bounces,
            "unsubscribes": self.unsubscribes,
            "spam_complaints": self.spam_complaints,
            "conversions": self.conversions,
            "revenue": self.revenue,
            "currency": self.currency,
            "source": self.source,
            "source_row_index": self.source_row_index,
            "warnings": self.warnings,
        }


@dataclass
class EmailDataset:
    client_id: str
    client_display_name: str
    report_period_start: date
    report_period_end: date
    rows: list[EmailCampaignRow]
    source: EmailSource
    warnings: list[str] = field(default_factory=list)
    raw_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_id": self.client_id,
            "client_display_name": self.client_display_name,
            "report_period_start": self.report_period_start.isoformat(),
            "report_period_end": self.report_period_end.isoformat(),
            "source": self.source,
            "warnings": self.warnings,
            "raw_path": self.raw_path,
            "row_count": len(self.rows),
            "rows": [r.to_dict() for r in self.rows],
        }

