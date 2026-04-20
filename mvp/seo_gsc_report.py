"""SEO block from Google Search Console (GSC) Search Analytics.

This is intentionally small and report-friendly:
- Totals for the period (clicks, impressions, ctr, position)
- Top queries and top pages (rows)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class GscSeoSnapshot:
    site_url: str
    start_date: date
    end_date: date
    totals: dict[str, float]
    top_queries: list[dict[str, Any]]
    top_pages: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": "google_search_console_api",
            "site_url": self.site_url,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "totals": self.totals,
            "top_queries": self.top_queries,
            "top_pages": self.top_pages,
        }


def _sum_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    clicks = float(sum((r.get("clicks") or 0) for r in rows))
    impressions = float(sum((r.get("impressions") or 0) for r in rows))
    ctr = (clicks / impressions) if impressions > 0 else 0.0
    # Position in GSC rows is already an average for that row; no perfect rollup.
    # We compute impression-weighted position when possible.
    weighted_pos = 0.0
    if impressions > 0:
        weighted_pos = float(
            sum((r.get("position") or 0.0) * (r.get("impressions") or 0.0) for r in rows) / impressions
        )
    return {"clicks": clicks, "impressions": impressions, "ctr": ctr, "position": weighted_pos}


def build_gsc_seo_snapshot(
    *,
    site_url: str,
    start_date: date,
    end_date: date,
    query_rows: list[dict[str, Any]],
    page_rows: list[dict[str, Any]],
) -> GscSeoSnapshot:
    totals = _sum_metrics(query_rows) if query_rows else _sum_metrics(page_rows)
    return GscSeoSnapshot(
        site_url=site_url,
        start_date=start_date,
        end_date=end_date,
        totals=totals,
        top_queries=query_rows,
        top_pages=page_rows,
    )

