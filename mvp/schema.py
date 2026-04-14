"""
Unified input schema for Meta Ads campaign exports (Excel/CSV).

Canonical field names are snake_case. See SCHEMA dict for documentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

# --- Documentation schema (single source of truth for integrators) ---

SCHEMA: dict[str, Any] = {
    "version": "1.0",
    "source": "meta_ads_campaign_export",
    "row": {
        "reporting_starts": "date — export period start",
        "reporting_ends": "date — export period end",
        "campaign_name": "str",
        "campaign_delivery": "str — e.g. inactive, completed",
        "results": "float — count of optimized events",
        "result_indicator": "str — e.g. actions:link_click, actions:post_engagement",
        "cost_per_result": "float | null — from platform",
        "ad_set_budget": "str | float — raw",
        "ad_set_budget_type": "str",
        "amount_spent": "float — spend in account currency",
        "currency": "str — ISO-like code, e.g. NGN, EUR",
        "impressions": "int | float",
        "reach": "int | float",
        "campaign_ends": "date | null",
        "attribution_setting": "str | null",
    },
}


@dataclass
class CampaignRow:
    reporting_starts: date
    reporting_ends: date
    campaign_name: str
    campaign_delivery: str
    results: float
    result_indicator: str
    cost_per_result: float | None
    ad_set_budget: str | float | None
    ad_set_budget_type: str | None
    amount_spent: float
    currency: str
    impressions: float
    reach: float
    campaign_ends: date | None
    attribution_setting: str | None
    source_row_index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "reporting_starts": self.reporting_starts.isoformat(),
            "reporting_ends": self.reporting_ends.isoformat(),
            "campaign_name": self.campaign_name,
            "campaign_delivery": self.campaign_delivery,
            "results": self.results,
            "result_indicator": self.result_indicator,
            "cost_per_result": self.cost_per_result,
            "ad_set_budget": self.ad_set_budget,
            "ad_set_budget_type": self.ad_set_budget_type,
            "amount_spent": self.amount_spent,
            "currency": self.currency,
            "impressions": self.impressions,
            "reach": self.reach,
            "campaign_ends": self.campaign_ends.isoformat() if self.campaign_ends else None,
            "attribution_setting": self.attribution_setting,
        }
        if self.source_row_index is not None:
            d["source_row_index"] = self.source_row_index
        return d


@dataclass
class NormalizedDataset:
    """Clean dataset ready for KPIs and reporting."""

    client_id: str
    client_display_name: str
    rows: list[CampaignRow]
    currency: str  # primary currency (all rows should match in v1)
    warnings: list[str] = field(default_factory=list)
    raw_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_id": self.client_id,
            "client_display_name": self.client_display_name,
            "currency": self.currency,
            "warnings": self.warnings,
            "raw_path": self.raw_path,
            "row_count": len(self.rows),
            "rows": [r.to_dict() for r in self.rows],
        }


Channel = Literal["meta_ads", "seo", "email", "other"]


def example_normalized_rows() -> list[dict[str, Any]]:
    """Example normalized rows for tests/docs."""
    return [
        {
            "reporting_starts": "2026-03-11",
            "reporting_ends": "2026-04-09",
            "campaign_name": "Brand — Link clicks",
            "campaign_delivery": "active",
            "results": 1000.0,
            "result_indicator": "actions:link_click",
            "cost_per_result": 0.05,
            "ad_set_budget": 50.0,
            "ad_set_budget_type": "Daily",
            "amount_spent": 50.0,
            "currency": "EUR",
            "impressions": 50000.0,
            "reach": 40000.0,
            "campaign_ends": "2026-05-01",
            "attribution_setting": "7-day click or 1-day view",
        }
    ]
