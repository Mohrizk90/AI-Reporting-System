"""
Email report structure aligned to Files/Email_Report_Template.docx.pdf (Pedicel Marketing).

MVP support:
- Campaign-level email stats (broadcast + sequences if provided by source)
- Brevo API ingestion (campaign stats)

Not in scope yet:
- List health/subscriber metrics unless a contacts/list export is provided
- Cold outreach reply/meetings metrics unless a sales/outreach system export is provided
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from mvp.email_kpis import EmailAggregateKPIs, compute_email_aggregate_kpis
from mvp.email_schema import EmailDataset, EmailCampaignRow

PREPARED_BY = "Pedicel Marketing"


def _fmt_int(v: int | None) -> str:
    return "—" if v is None else f"{v:,}"


def _fmt_pct(v: float | None) -> str:
    return "—" if v is None else f"{v:.2f}%"


def _top_campaigns(rows: list[EmailCampaignRow], n: int = 5) -> list[EmailCampaignRow]:
    # prioritize by delivered then sent
    return sorted(rows, key=lambda r: (r.delivered or 0, r.sent or 0), reverse=True)[:n]


def build_email_report_template(ds: EmailDataset, ai_block: dict[str, Any] | None = None) -> dict[str, Any]:
    k = compute_email_aggregate_kpis(ds)
    period_label = f"{ds.report_period_start.isoformat()} to {ds.report_period_end.isoformat()}"

    # Template top table: Period / Emails Sent / Avg. Open Rate / Avg. CTR / Avg. Unsub Rate / Total Conversions
    # We compute portfolio rates (not per-campaign average) to avoid misleading averages.
    top_table = [
        {"label": "Period", "value": period_label},
        {"label": "Emails Sent", "value": _fmt_int(k.sent)},
        {"label": "Avg. Open Rate", "value": _fmt_pct(k.open_rate_pct)},
        {"label": "Avg. CTR", "value": _fmt_pct(k.ctr_pct)},
        {"label": "Avg. Unsubscribe Rate", "value": _fmt_pct(k.unsubscribe_rate_pct)},
        {"label": "Total Conversions", "value": "Not available in current source"},
    ]

    # Section 2 list health — not available without subscriber/list export
    section_2 = {
        "title": "2. List Health & Subscriber Metrics",
        "status_label": "Not included in this MVP scope",
        "explanation": (
            "Subscriber/list health metrics require an ESP contacts/list export or API endpoints "
            "for subscriber counts and growth. This MVP ingests campaign-level performance only."
        ),
        "rows": [
            {"metric": "Total Active Subscribers", "value": "—"},
            {"metric": "New Subscribers Added", "value": "—"},
            {"metric": "Unsubscribes", "value": _fmt_int(k.unsubscribes)},
            {"metric": "Hard Bounces", "value": _fmt_int(k.hard_bounces)},
            {"metric": "Soft Bounces", "value": _fmt_int(k.soft_bounces)},
            {"metric": "Net List Growth", "value": "—"},
            {"metric": "List Growth Rate", "value": "—"},
            {"metric": "Spam Complaints", "value": _fmt_int(k.spam_complaints)},
        ],
        "note": (
            "A hard bounce rate above 2% can signal deliverability problems. Spam complaints above 0.1% "
            "may trigger inbox filtering penalties. (Reference copy from Pedicel template.)"
        ),
    }

    # Section 3 core KPIs — use template names and computed values where supported
    section_3_rows = [
        {"metric": "Delivered", "how_calculated": "Sent − Hard Bounces − Soft Bounces", "value": _fmt_int(k.delivered), "benchmark": "—"},
        {"metric": "Opens", "how_calculated": "Unique recipients who opened the email", "value": _fmt_int(k.opens_unique), "benchmark": "—"},
        {"metric": "Clicks", "how_calculated": "Unique recipients who clicked any link", "value": _fmt_int(k.clicks_unique), "benchmark": "—"},
        {"metric": "Unsubscribes", "how_calculated": "Recipients who opted out after receiving the email", "value": _fmt_int(k.unsubscribes), "benchmark": "—"},
        {"metric": "Delivery Rate", "how_calculated": "Delivered ÷ Sent × 100", "value": _fmt_pct(k.delivery_rate_pct), "benchmark": "> 98%"},
        {"metric": "Open Rate", "how_calculated": "Opens ÷ Delivered × 100", "value": _fmt_pct(k.open_rate_pct), "benchmark": "> 20%–35%"},
        {"metric": "Click-Through Rate (CTR)", "how_calculated": "Clicks ÷ Delivered × 100", "value": _fmt_pct(k.ctr_pct), "benchmark": "> 2%–5%"},
        {"metric": "CTOR", "how_calculated": "Clicks ÷ Opens × 100", "value": _fmt_pct(k.ctor_pct), "benchmark": "> 10%–20%"},
        {"metric": "Unsubscribe Rate", "how_calculated": "Unsubscribes ÷ Delivered × 100", "value": _fmt_pct(k.unsubscribe_rate_pct), "benchmark": "< 0.3% per campaign"},
        {"metric": "Bounce Rate", "how_calculated": "(Hard + Soft) ÷ Sent × 100", "value": _fmt_pct(k.bounce_rate_pct), "benchmark": "< 2% hard; < 5% cold"},
        {"metric": "Spam Complaint Rate", "how_calculated": "Complaints ÷ Delivered × 100", "value": _fmt_pct(k.complaint_rate_pct), "benchmark": "< 0.1%"},
    ]

    # Section 4 campaign breakdown — broadcast-like campaigns (classic) or unknown
    top = _top_campaigns(ds.rows, 5)
    breakdown_rows = []
    for r in top:
        breakdown_rows.append(
            {
                "campaign_name": r.campaign_name,
                "sent": r.sent,
                "open_rate_pct": (r.opens_unique / r.delivered * 100.0) if (r.opens_unique is not None and r.delivered) else None,
                "ctr_pct": (r.clicks_unique / r.delivered * 100.0) if (r.clicks_unique is not None and r.delivered) else None,
                "ctor_pct": (r.clicks_unique / r.opens_unique * 100.0) if (r.clicks_unique is not None and r.opens_unique) else None,
                "unsubs": r.unsubscribes,
                "conversions": r.conversions,
            }
        )

    # Section 9 insights — AI slots
    ai = ai_block or {}
    insights = {
        "newsletter_broadcast_summary": ai.get("summary") or "—",
        "sequence_automation_summary": ai.get("sequence_summary") or "Not available in current source",
        "cold_outreach_summary": ai.get("cold_outreach_summary") or "Not available in current source",
        "recommended_actions": ai.get("recommendations") or [],
        "caveats": ai.get("caveats") or [],
        "source": ai.get("source", "unknown"),
    }

    return {
        "document": {
            "report_title": "Email Marketing Performance Report",
            "report_subtitle": "Newsletters, Sequences & Campaigns",
            "header_line": f"Report period: {period_label} | Prepared by: {PREPARED_BY}",
            "prepared_by": PREPARED_BY,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "section_0_topline_table": top_table,
        "section_1_report_overview": {
            "title": "1. Report Overview",
            "body": (
                "This report covers email marketing performance for the period specified above. "
                "Data is sourced from your email service provider (ESP). "
                "All placeholder values are replaced with available source data; fields not supported by the current "
                "source are clearly marked as not available."
            ),
        },
        "section_2_list_health": section_2,
        "section_3_core_kpis": {"title": "3. Core Email KPIs", "rows": section_3_rows},
        "section_4_campaign_breakdown": {
            "title": "4. Campaign Breakdown",
            "subsection_4_1_broadcast": {"title": "4.1 Broadcast / Newsletter Campaigns", "rows": breakdown_rows},
            "note": "MVP: showing top campaigns by delivered volume. Full campaign lists are available in the JSON export.",
        },
        "section_8_key_benchmarks": {
            "title": "8. Key Benchmarks",
            "reference": [
                {"metric": "Open Rate (Broadcast)", "target": "> 20%–35%", "watch": "< 15% = subject line or list fatigue"},
                {"metric": "CTR (Broadcast)", "target": "> 2%–5%", "watch": "< 1% = weak content or CTA"},
                {"metric": "CTOR", "target": "> 10%–20%", "watch": "< 8% = content relevance issue"},
                {"metric": "Unsubscribe Rate", "target": "< 0.3%", "watch": "> 0.5% = frequency or content mismatch"},
                {"metric": "Spam Complaint Rate", "target": "< 0.1%", "watch": "> 0.1% = urgent list hygiene needed"},
            ],
        },
        "section_9_insights_and_recommendations": {"title": "9. Insights & Recommendations", **insights},
        "kpis": k.to_dict(),
    }

