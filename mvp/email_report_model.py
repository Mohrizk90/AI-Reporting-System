"""Top-level report assembly for Email template-aligned report."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from mvp.email_ai import generate_email_ai_insights
from mvp.email_kpis import compute_email_aggregate_kpis
from mvp.email_schema import EmailDataset
from mvp.email_template import build_email_report_template
from mvp.monthly_report_sources import build_monthly_report_data_sources_payload


def build_email_report_payload(
    *,
    ds: EmailDataset,
    skip_ai: bool,
) -> dict[str, Any]:
    kpis = compute_email_aggregate_kpis(ds)

    if skip_ai:
        ai = {
            "summary": "Automated narrative disabled (--no-ai). Review KPI tables and top campaigns, then complete §9 manually or re-run with OPENAI_API_KEY.",
            "insights": [],
            "recommendations": [
                "Review open rate vs benchmark; retest subject lines where under target.",
                "Review CTR/CTOR; tighten CTAs and link placement in low performers.",
                "Monitor unsubscribes and complaints; adjust frequency if elevated.",
            ],
            "caveats": ["LLM not invoked (--no-ai)."],
            "source": "skipped",
        }
    else:
        ai = generate_email_ai_insights(ds, kpis)

    email_report = build_email_report_template(ds, ai_block=ai)

    return {
        "meta": {
            "schema_version": "1.0-email",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "client_id": ds.client_id,
            "client_name": ds.client_display_name,
            "channel": "email",
            "source": ds.source,
            "source_path": ds.raw_path,
            "template_id": "Email_Report_Template.docx.pdf",
        },
        "monthly_report_data_sources": build_monthly_report_data_sources_payload(),
        "scope": {
            "supported_now": [
                {
                    "channel": "email_campaign_reporting",
                    "description": "Campaign-level email metrics (sent/delivered/opens/clicks/bounces/unsubs) from Brevo API or an ESP export.",
                }
            ],
            "not_implemented": [
                {
                    "channel": "list_health",
                    "reason": "Template §2 requires subscriber/list export or additional ESP endpoints.",
                },
                {
                    "channel": "cold_outreach_pipeline",
                    "reason": "Template §5 requires reply/meeting data from outreach/CRM; not in campaign stats.",
                },
                {
                    "channel": "revenue_attribution",
                    "reason": "Template §4.2 revenue requires commerce/CRM linkage; not in current sources.",
                },
            ],
        },
        "ingestion": {"warnings": ds.warnings + (kpis.notes if hasattr(kpis, "notes") else []), "row_count": len(ds.rows)},
        "email_report": email_report,
        "insights": {
            "summary": ai.get("summary"),
            "insights": ai.get("insights") or [],
            "recommendations": ai.get("recommendations") or [],
            "caveats": ai.get("caveats") or [],
            "source": ai.get("source", "unknown"),
        },
    }

