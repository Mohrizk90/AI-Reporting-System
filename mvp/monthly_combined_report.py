"""Monthly combined report (multi-client, multi-source).

This is a lightweight wrapper that combines:
- Paid ads report sections built from Meta export CSV/XLSX inputs
- SEO snapshot from Google Search Console (GSC)

The goal is: run once → one output folder → one report.json/md/html.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from mvp.monthly_report_sources import build_monthly_report_data_sources_payload


def build_monthly_combined_report_payload(
    *,
    title: str,
    subtitle: str | None,
    prepared_by: str,
    clients: list[dict[str, Any]],
    connected_sources: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "meta": {
            "schema_version": "1.0-monthly-combined",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "prepared_by": prepared_by,
        },
        "monthly_report_data_sources": build_monthly_report_data_sources_payload(),
        "monthly_report": {
            "title": title,
            "subtitle": subtitle,
            "connected_sources": connected_sources or [],
            "clients": clients,
        },
    }

