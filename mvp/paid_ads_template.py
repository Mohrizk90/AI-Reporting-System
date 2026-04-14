"""
Paid Ads Report structure aligned to Files/Ads_Report_Template.docx.pdf (Pedicel Marketing).

MVP scope: Meta Ads Manager campaign exports only (see docs/SCOPE_STATEMENT.md).
"""

from __future__ import annotations

from typing import Any

from mvp.kpis import AggregateKPIs, campaign_table, LINK_CLICK
from mvp.schema import NormalizedDataset

PREPARED_BY = "Pedicel Marketing"
PRODUCT_NAME = "Pedicel Paid Ads reporting automation MVP (Meta campaign exports)"

# Aligns with template §1: full template spans Meta + Google; we state Meta-from-file and explicit MVP boundaries.
OVERVIEW_INTRO = (
    "This report follows the Pedicel Paid Ads layout. Facebook / Meta Ads figures below are calculated from "
    "the Meta Ads Manager campaign export supplied for this run. "
    "Google Ads sections of the template are not filled here—this MVP does not ingest Google Ads data. "
    "Fields that require revenue (for example blended ROAS) are marked not available unless revenue is added to the pipeline."
)


def _date_pretty(d) -> str:
    return d.strftime("%d %b %Y")


def build_executive_summary_paragraph(ds: NormalizedDataset, kpis: AggregateKPIs) -> str:
    """
    Client-ready, deterministic summary: period, scale, dominant spend, frequency note, optimization-event caveat.
    Does not claim revenue, ROAS, or Google performance.
    """
    if not ds.rows:
        return "No campaign rows were found in the supplied export."

    r0 = ds.rows[0]
    p0 = _date_pretty(r0.reporting_starts)
    p1 = _date_pretty(r0.reporting_ends)
    cur = ds.currency

    top = max(ds.rows, key=lambda x: x.amount_spent)
    pct = (top.amount_spent / kpis.total_spend * 100) if kpis.total_spend > 0 else 0.0

    freq = kpis.frequency
    if freq is None:
        freq_part = ""
    elif freq > 3.5:
        freq_part = (
            f" Portfolio average frequency is {freq:.2f} (above the common 3.5 fatigue watch-point); "
            "consider creative or audience refreshes on high-delivery campaigns."
        )
    else:
        freq_part = f" Portfolio average frequency is {freq:.2f}."

    if len(kpis.unique_result_indicators) > 1:
        mix_part = (
            " Campaigns use different Meta optimization events; treat portfolio-level “results” as informational "
            "and compare performance within the same event type."
        )
    elif kpis.unique_result_indicators:
        ev = kpis.unique_result_indicators[0]
        mix_part = (
            f" All visible campaigns share the same optimization-event label ({ev}); "
            "totals still follow Meta attribution settings per row."
        )
    else:
        mix_part = " Totals follow Meta attribution settings per row."

    return (
        f"For the reporting period {p0} – {p1}, this export includes {kpis.row_count} campaign row(s) with "
        f"{kpis.total_spend:,.2f} {cur} in spend, {int(kpis.total_impressions):,} impressions, and "
        f"{int(kpis.total_reach):,} reach.{freq_part}"
        f" The largest share of spend is “{top.campaign_name[:90]}” (approximately {pct:.0f}% of spend)."
        f"{mix_part}"
        " Revenue, blended ROAS, and Google Ads are not derived from this Meta export and are not stated here."
    )


# Core KPI definitions (2.1) — match template wording where possible
CORE_KPI_DEFINITIONS: list[dict[str, str]] = [
    {"metric": "Impressions", "what_it_measures": "How many times your ad was displayed", "benchmark_target": "—"},
    {"metric": "Reach", "what_it_measures": "Unique people who saw the ad", "benchmark_target": "—"},
    {
        "metric": "Frequency",
        "what_it_measures": "Impressions ÷ reach",
        "benchmark_target": "1.5 – 3.0 (above 3.5 = audience fatigue)",
    },
    {
        "metric": "CTR (link)",
        "what_it_measures": "Link clicks ÷ impressions",
        "benchmark_target": "> 0.8%–1.5%",
    },
    {"metric": "CPC", "what_it_measures": "Spend ÷ link clicks", "benchmark_target": "Depends on objective"},
    {
        "metric": "CPM",
        "what_it_measures": "Cost per 1,000 impressions",
        "benchmark_target": "₦200 – ₦1,200 (Nigeria) — reference §4",
    },
    {
        "metric": "CPL / CPA",
        "what_it_measures": "Spend ÷ leads or actions",
        "benchmark_target": "Varies by industry",
    },
    {"metric": "ROAS", "what_it_measures": "Revenue ÷ ad spend", "benchmark_target": "3x+ (e-commerce)"},
    {
        "metric": "Conversion rate",
        "what_it_measures": "Conversions ÷ link clicks",
        "benchmark_target": "> 3%–5%",
    },
    {
        "metric": "Lead form CVR",
        "what_it_measures": "Leads ÷ form opens (lead gen objective)",
        "benchmark_target": "> 10%",
    },
]

CREATIVE_ENGAGEMENT_INTRO = (
    "These metrics diagnose the quality of your ad creative and audience engagement beyond clicks."
)

KEY_BENCHMARKS_REFERENCE = [
    {"context": "Facebook — Nigeria / B2B", "metric": "CTR (link)", "target": "> 0.8%–1.5%"},
    {"context": "Facebook — Nigeria / B2B", "metric": "CPM", "target": "₦200 – ₦1,200"},
    {"context": "Facebook — Nigeria / B2B", "metric": "Frequency", "target": "1.5 – 3.0"},
    {"context": "Facebook — Nigeria / B2B", "metric": "Video hook rate", "target": "> 30%"},
    {"context": "Facebook — Nigeria / B2B", "metric": "Lead form CVR", "target": "> 10%"},
    {"context": "Google Search Ads", "metric": "CTR (search)", "target": "> 4%–7%"},
    {"context": "Google Search Ads", "metric": "Quality Score", "target": "7–10"},
    {"context": "Google Search Ads", "metric": "Impression share", "target": "> 60%"},
    {"context": "Google Search Ads", "metric": "ROAS (e-commerce)", "target": "3x+"},
]


def _fmt_num(v: float | int | None, decimals: int = 2) -> str:
    if v is None:
        return "—"
    if isinstance(v, int):
        return f"{v:,}"
    return format(float(v), f",.{decimals}f")


def _humanize_indicator(ind: str) -> str:
    if not ind:
        return "—"
    return ind.replace("actions:", "").replace("_", " ").title()


def build_section_2_1_core_kpis(kpis: AggregateKPIs, currency: str) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for row in CORE_KPI_DEFINITIONS:
        m = row["metric"]
        period_val: str | None = None
        note: str | None = None

        if m == "Impressions":
            period_val = _fmt_num(int(kpis.total_impressions), 0)
        elif m == "Reach":
            period_val = _fmt_num(int(kpis.total_reach), 0)
        elif m == "Frequency":
            period_val = _fmt_num(kpis.frequency, 4) if kpis.frequency is not None else "—"
        elif m == "CTR (link)":
            if kpis.link_click_rows and kpis.ctr_link_pct is not None:
                period_val = f"{kpis.ctr_link_pct:.4f}% (link-click rows only)"
            else:
                period_val = "Not available in current export"
                note = "No campaigns optimized for link clicks in this file."
        elif m == "CPC":
            if kpis.link_click_rows and kpis.cpc_link is not None:
                period_val = f"{kpis.cpc_link:.6f} {currency} (link-click rows only)"
            else:
                period_val = "Not available in current export"
                note = "Requires link-click results."
        elif m == "CPM":
            period_val = f"{kpis.cpm:.4f} {currency}" if kpis.cpm is not None else "—"
        elif m == "CPL / CPA":
            spend = kpis.total_spend
            res = kpis.total_results
            if res > 0:
                period_val = f"{(spend / res):.6f} {currency} (spend ÷ total results; mixed events possible)"
                note = "Interpret alongside each campaign’s optimization event."
            else:
                period_val = "—"
        elif m == "ROAS":
            period_val = "Not available in current export"
            note = "Revenue not included in the Meta campaign file."
        elif m == "Conversion rate":
            period_val = "Not available in current export"
            note = "Requires matched conversion and click fields not present in this export."
        elif m == "Lead form CVR":
            period_val = "Not available in current export"
            note = "Requires lead-form funnel fields not present in this export."

        rows_out.append(
            {
                "metric": m,
                "what_it_measures": row["what_it_measures"],
                "period_value": period_val or "—",
                "benchmark_target": row["benchmark_target"],
                "notes": note,
            }
        )
    return rows_out


def _fmt_money(amount: float, currency: str) -> str:
    return f"{amount:,.2f} {currency}"


def build_section_2_3_campaign_breakdown(ds: NormalizedDataset, kpis: AggregateKPIs) -> dict[str, Any]:
    cur = ds.currency
    campaigns: list[dict[str, Any]] = []
    for c in campaign_table(ds.rows):
        spend = float(c["amount_spent"])
        ctr = c.get("ctr_link_pct")
        cpc_v = c.get("cpc_link")
        cpm_v = c.get("cpm")
        if c.get("result_indicator") == LINK_CLICK:
            clicks_label = "Link clicks"
            clicks_val = c["results"]
        else:
            clicks_label = "Results (optimized)"
            clicks_val = c["results"]

        campaigns.append(
            {
                "campaign_name": c["campaign_name"],
                "objective": _humanize_indicator(str(c.get("result_indicator", ""))),
                "spend": spend,
                "spend_display": _fmt_money(spend, cur),
                "currency": cur,
                "impressions": int(c["impressions"]),
                "impressions_display": f"{int(c['impressions']):,}",
                "clicks_label": clicks_label,
                "clicks_or_results": clicks_val,
                "ctr_pct": ctr,
                "ctr_display": f"{ctr:.4f}%" if ctr is not None else "—",
                "cpc": cpc_v,
                "cpc_display": f"{cpc_v:.6f} {cur}" if cpc_v is not None else "—",
                "cpm": cpm_v,
                "cpm_display": f"{cpm_v:.4f} {cur}" if cpm_v is not None else "—",
            }
        )

    total_spend = kpis.total_spend
    total_impr = int(kpis.total_impressions)
    tr_ctr = kpis.ctr_link_pct if kpis.link_click_rows else None
    tr_cpc = kpis.cpc_link if kpis.link_click_rows else None
    tr_cpm = kpis.cpm

    total_row = {
        "campaign_name": "TOTAL",
        "objective": "—",
        "spend": total_spend,
        "spend_display": _fmt_money(total_spend, cur),
        "currency": cur,
        "impressions": total_impr,
        "impressions_display": f"{total_impr:,}",
        "clicks_label": "—",
        "clicks_or_results": None,
        "ctr_pct": tr_ctr,
        "ctr_display": f"{tr_ctr:.4f}%" if tr_ctr is not None else "—",
        "cpc": tr_cpc,
        "cpc_display": f"{tr_cpc:.6f} {cur}" if tr_cpc is not None else "—",
        "cpm": tr_cpm,
        "cpm_display": f"{tr_cpm:.4f} {cur}" if tr_cpm is not None else "—",
        "is_total": True,
    }

    return {
        "footnote": (
            "Watch frequency closely. Once it exceeds 3.5, CPM typically rises and CTR drops, signalling audience fatigue — "
            "consider expanding targeting or refreshing creatives."
        ),
        "campaigns": campaigns,
        "total_row": total_row,
    }


def build_paid_ads_template_report(
    ds: NormalizedDataset,
    kpis: AggregateKPIs,
    ai_block: dict[str, Any] | None,
) -> dict[str, Any]:
    r0 = ds.rows[0]
    period_start = r0.reporting_starts.isoformat()
    period_end = r0.reporting_ends.isoformat()
    date_range_label = f"{period_start} to {period_end}"

    overview_table = [
        {"label": "Report period", "value": date_range_label},
        {"label": "Total ad spend (Meta)", "value": f"{kpis.total_spend:,.2f} {ds.currency}"},
        {
            "label": "Total results (Meta optimization events)",
            "value": f"{kpis.total_results:,.0f}",
            "note": "Sum of Meta “Results”; meaning depends on each campaign’s optimization (see §2.3).",
        },
        {
            "label": "Blended ROAS",
            "value": "Not available in current export",
            "note": "Revenue / purchase value not included in this Meta campaign file.",
        },
    ]

    section_2_2 = {
        "title": "2.2 Creative & Engagement Metrics",
        "intro": CREATIVE_ENGAGEMENT_INTRO,
        "status": "not_in_scope",
        "status_label": "Not available from current export",
        "explanation": (
            "Video hook rate, ThruPlay rate, engagement rate, landing-page view rate, and similar creative-level "
            "metrics are intentionally not generated here. This MVP uses campaign-level Meta exports only; "
            "ad- or asset-level exports (or API) are required to populate this subsection."
        ),
    }

    section_3 = {
        "title": "3. Google Ads",
        "status": "not_included",
        "status_label": "Not included in this MVP scope",
        "reason": (
            "Google Ads data was not ingested. Sections 3.1–3.3 of the Pedicel template require a Google Ads "
            "export or API connection—out of scope for this Meta-only MVP."
        ),
    }

    fb_summary = (ai_block or {}).get("summary") or ""
    google_summary_text = (ai_block or {}).get("google_ads_summary")
    if google_summary_text is None:
        google_summary_text = (
            "Not included in this MVP scope. Add a Google Ads data source to populate this subsection."
        )
    recs = (ai_block or {}).get("recommendations") or []

    section_5 = {
        "title": "5. Insights & Recommendations",
        "instruction": (
            "Complete this section after reviewing the data above. For this automated run, §5.1 reflects Meta only; "
            "§5.2 remains intentionally blank pending Google Ads data."
        ),
        "section_5_1_facebook_ads_summary": {
            "title": "5.1 Facebook Ads Summary",
            "body": fb_summary or "—",
        },
        "section_5_2_google_ads_summary": {
            "title": "5.2 Google Ads Summary",
            "body": google_summary_text,
        },
        "section_5_3_recommended_actions": {
            "title": "5.3 Recommended Actions",
            "action_items": recs,
        },
    }

    exec_para = build_executive_summary_paragraph(ds, kpis)

    return {
        "document": {
            "report_title": "Paid Ads Performance Report",
            "report_subtitle": "Facebook Ads + Google Ads",
            "product": PRODUCT_NAME,
            "header_line": f"Report period: {date_range_label} | Prepared by: {PREPARED_BY}",
            "footer_attribution": f"Prepared by {PREPARED_BY}",
        },
        "section_1_report_overview": {
            "title": "1. Report Overview",
            "intro": OVERVIEW_INTRO,
            "executive_summary": exec_para,
            "overview_table": overview_table,
            "overview_table_headers": ["Metric", "Value"],
        },
        "section_2_facebook_meta_ads": {
            "title": "2. Facebook / Meta Ads",
            "subsection_2_1_core_kpis": {
                "title": "2.1 Core KPIs",
                "column_headers": ["Metric", "What it measures", "Period value", "Benchmark / target"],
                "rows": build_section_2_1_core_kpis(kpis, ds.currency),
            },
            "subsection_2_2_creative_engagement": section_2_2,
            "subsection_2_3_campaign_breakdown": {
                "title": "2.3 Campaign Breakdown",
                "instruction": (
                    "One row per campaign in the export. The TOTAL row aggregates the file. "
                    "CTR and CPC are shown for link-click optimization where applicable; other objectives show an em dash (—)."
                ),
                **build_section_2_3_campaign_breakdown(ds, kpis),
            },
        },
        "section_3_google_ads": section_3,
        "section_4_key_benchmarks": {
            "title": "4. Key Benchmarks",
            "intro": (
                "Reference thresholds from the Pedicel template for quick health checks. "
                "Facebook CPM bands are shown in Naira as in the source template; interpret cross-currency comparisons qualitatively."
            ),
            "reference_rows": KEY_BENCHMARKS_REFERENCE,
        },
        "section_5_insights_and_recommendations": section_5,
    }
