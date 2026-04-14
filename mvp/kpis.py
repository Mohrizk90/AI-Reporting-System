"""KPI calculations — modular functions; Meta export compatible."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mvp.schema import CampaignRow, NormalizedDataset

LINK_CLICK = "actions:link_click"


def safe_div(num: float, den: float) -> float | None:
    if den == 0:
        return None
    return num / den


def cpm(amount_spent: float, impressions: float) -> float | None:
    """Cost per 1000 impressions."""
    v = safe_div(amount_spent * 1000.0, impressions)
    return round(v, 4) if v is not None else None


def frequency(impressions: float, reach: float) -> float | None:
    """Impressions / reach (Meta-style)."""
    v = safe_div(impressions, reach)
    return round(v, 4) if v is not None else None


def ctr_pct(clicks_or_results: float, impressions: float) -> float | None:
    """CTR as percentage (e.g. 1.25 means 1.25%)."""
    v = safe_div(clicks_or_results, impressions)
    if v is None:
        return None
    return round(v * 100.0, 4)


def cpc_spend(spend: float, clicks: float) -> float | None:
    v = safe_div(spend, clicks)
    return round(v, 6) if v is not None else None


def engagement_rate_pct(engagements: float, impressions: float) -> float | None:
    """Engagements / impressions as percentage."""
    return ctr_pct(engagements, impressions)


def conversion_rate_pct(conversions: float, clicks: float) -> float | None:
    """Conversions ÷ clicks × 100. Not available from Meta export alone unless clicks align with conv. window."""
    v = safe_div(conversions, clicks)
    if v is None:
        return None
    return round(v * 100.0, 4)


# --- SEO placeholders (no data in Meta export; extend when GSC CSV exists) ---


def seo_click_through_rate(clicks: float, impressions: float) -> float | None:
    return ctr_pct(clicks, impressions)


@dataclass
class AggregateKPIs:
    total_spend: float
    total_impressions: float
    total_reach: float
    total_results: float
    row_count: int
    frequency: float | None
    cpm: float | None
    unique_result_indicators: list[str]
    link_click_rows: int
    link_click_results: float
    link_click_spend: float
    link_click_impressions: float
    ctr_link_pct: float | None
    cpc_link: float | None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_spend": round(self.total_spend, 2),
            "total_impressions": int(self.total_impressions),
            "total_reach": int(self.total_reach),
            "total_results": round(self.total_results, 2),
            "row_count": self.row_count,
            "frequency": self.frequency,
            "cpm": self.cpm,
            "unique_result_indicators": self.unique_result_indicators,
            "link_click_rows": self.link_click_rows,
            "link_click_results": round(self.link_click_results, 2),
            "link_click_spend": round(self.link_click_spend, 2),
            "link_click_impressions": int(self.link_click_impressions),
            "ctr_link_pct": self.ctr_link_pct,
            "cpc_link": self.cpc_link,
            "notes": self.notes,
        }


def compute_aggregate_kpis(ds: NormalizedDataset) -> AggregateKPIs:
    rows = ds.rows
    spend = sum(r.amount_spent for r in rows)
    impr = sum(r.impressions for r in rows)
    reach = sum(r.reach for r in rows)
    res = sum(r.results for r in rows)
    indicators = sorted({r.result_indicator for r in rows if r.result_indicator})

    notes: list[str] = []
    if len(indicators) > 1:
        notes.append(
            "total_results sums different optimization events; interpret totals with caution."
        )

    lc_rows = [r for r in rows if r.result_indicator == LINK_CLICK]
    lc_res = sum(r.results for r in lc_rows)
    lc_spend = sum(r.amount_spent for r in lc_rows)
    lc_impr = sum(r.impressions for r in lc_rows)

    ctr_l = ctr_pct(lc_res, lc_impr) if lc_rows else None
    cpc_l = cpc_spend(lc_spend, lc_res) if lc_rows and lc_res > 0 else None

    freq = frequency(impr, reach)
    cpm_v = cpm(spend, impr)

    return AggregateKPIs(
        total_spend=spend,
        total_impressions=impr,
        total_reach=reach,
        total_results=res,
        row_count=len(rows),
        frequency=freq,
        cpm=cpm_v,
        unique_result_indicators=indicators,
        link_click_rows=len(lc_rows),
        link_click_results=lc_res,
        link_click_spend=lc_spend,
        link_click_impressions=lc_impr,
        ctr_link_pct=ctr_l,
        cpc_link=cpc_l,
        notes=notes,
    )


def campaign_table(rows: list[CampaignRow]) -> list[dict[str, Any]]:
    """Per-campaign metrics for report tables."""
    out: list[dict[str, Any]] = []
    for r in rows:
        row = {
            "campaign_name": r.campaign_name,
            "delivery": r.campaign_delivery,
            "amount_spent": round(r.amount_spent, 2),
            "impressions": int(r.impressions),
            "reach": int(r.reach),
            "results": r.results,
            "result_indicator": r.result_indicator,
            "cost_per_result": r.cost_per_result,
            "frequency": frequency(r.impressions, r.reach),
            "cpm": cpm(r.amount_spent, r.impressions),
        }
        if r.result_indicator == LINK_CLICK:
            row["ctr_link_pct"] = ctr_pct(r.results, r.impressions)
            row["cpc_link"] = cpc_spend(r.amount_spent, r.results)
        else:
            row["ctr_link_pct"] = None
            row["cpc_link"] = None
        out.append(row)
    return out
