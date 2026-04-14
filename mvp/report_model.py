"""Assemble report JSON aligned to Pedicel Paid Ads template + ingestion meta."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from mvp.kpis import AggregateKPIs, compute_aggregate_kpis
from mvp.paid_ads_template import build_paid_ads_template_report
from mvp.schema import NormalizedDataset


def build_report_payload(
    ds: NormalizedDataset,
    kpis: AggregateKPIs | None = None,
    ai_block: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Primary output: `paid_ads_report` mirrors Ads_Report_Template.docx.pdf sections.

    `insights` is a flat compatibility layer for automation (same content as §5.1 / §5.3).
    """
    kpis = kpis or compute_aggregate_kpis(ds)
    ai = ai_block or {}

    paid = build_paid_ads_template_report(ds, kpis, ai)

    report: dict[str, Any] = {
        "meta": {
            "schema_version": "1.2",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "client_id": ds.client_id,
            "client_name": ds.client_display_name,
            "currency": ds.currency,
            "source_path": ds.raw_path,
            "prepared_by": "Pedicel Marketing",
            "template_id": "Ads_Report_Template.docx.pdf",
        },
        "scope": {
            "supported_now": [
                {
                    "channel": "meta_ads_campaign_export",
                    "description": "Meta Ads Manager campaign-level Excel/CSV (see mvp/ingest.py).",
                }
            ],
            "not_implemented": [
                {
                    "channel": "google_ads",
                    "reason": "Not in MVP scope; requires Google Ads export or API (template §3).",
                },
                {
                    "channel": "seo",
                    "reason": "Not in MVP scope; no Search Console ingest.",
                },
                {
                    "channel": "social_organic",
                    "reason": "Not in MVP scope; no organic social exports.",
                },
                {
                    "channel": "email",
                    "reason": "Not in MVP scope; no ESP export.",
                },
                {
                    "channel": "creative_level_meta",
                    "reason": "Template §2.2 requires ad/asset-level data; only campaign export is ingested.",
                },
            ],
        },
        "ingestion": {
            "warnings": ds.warnings + kpis.notes,
            "row_count": len(ds.rows),
        },
        "paid_ads_report": paid,
        # Compatibility / LLM hooks (dashboards may read these keys)
        "insights": {
            "summary": ai.get("summary"),
            "insights": ai.get("insights") or [],
            "recommendations": ai.get("recommendations") or [],
            "caveats": ai.get("caveats") or [],
            "source": ai.get("source", "unknown"),
        },
    }
    return report
