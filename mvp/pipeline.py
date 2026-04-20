"""End-to-end run: ingest → KPIs → AI → report dict → files.

This module keeps the existing Paid Ads (Meta export) MVP intact, and adds
an Email channel pipeline entrypoint.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import os
from datetime import date

from mvp.ai_insights import generate_ai_insights, normalize_ai_block
from mvp.formatters import write_outputs
from mvp.google_search_console import get_credentials, search_analytics_query, token_path
from mvp.ingest import normalize_meta_export
from mvp.kpis import compute_aggregate_kpis
from mvp.report_model import build_report_payload
from mvp.email_ingest_brevo import ingest_brevo_email_campaigns
from mvp.email_ingest_excel import ingest_email_excel_export
from mvp.email_report_model import build_email_report_payload
from mvp.seo_gsc_report import build_gsc_seo_snapshot


def run_pipeline(
    input_path: str | Path,
    client_id: str,
    client_display_name: str,
    output_dir: str | Path | None = None,
    sheet_name: str | int | None = 0,
    skip_ai: bool = False,
    base_name: str = "report",
) -> dict[str, Any]:
    """
    Full pipeline. Returns final report dict and writes json/txt/md/html under output_dir.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir) if output_dir else Path("output") / client_id
    output_dir.mkdir(parents=True, exist_ok=True)

    ds = normalize_meta_export(
        input_path,
        client_id=client_id,
        client_display_name=client_display_name,
        sheet_name=sheet_name,
    )
    kpis = compute_aggregate_kpis(ds)

    # Optional: attach SEO snapshot from Google Search Console if token + site are available.
    gsc_site = os.environ.get("GOOGLE_SEARCH_CONSOLE_SITE", "").strip()
    seo_snapshot = None
    if gsc_site and token_path().exists():
        # Use Meta export reporting window to align the month/period across channels.
        ps = ds.rows[0].reporting_starts if ds.rows else date.today().replace(day=1)
        pe = ds.rows[0].reporting_ends if ds.rows else date.today()
        creds = get_credentials()
        q = search_analytics_query(
            creds,
            gsc_site,
            start_date=ps,
            end_date=pe,
            dimensions=["query"],
            row_limit=25,
        )
        p = search_analytics_query(
            creds,
            gsc_site,
            start_date=ps,
            end_date=pe,
            dimensions=["page"],
            row_limit=25,
        )
        seo_snapshot = build_gsc_seo_snapshot(
            site_url=gsc_site,
            start_date=ps,
            end_date=pe,
            query_rows=list(q.get("rows", []) or []),
            page_rows=list(p.get("rows", []) or []),
        ).to_dict()

    if skip_ai:
        ai_raw = {
            "summary": (
                "Automated narrative disabled (--no-ai). See §1 executive summary for the period snapshot; "
                "use §5.3 for next-step prompts, or re-run with OPENAI_API_KEY for a full §5.1 write-up."
            ),
            "insights": [],
            "recommendations": [
                "Compare campaigns that share the same optimization event before judging blended totals.",
                "If portfolio frequency exceeds 3.5 on scaling spend, schedule creative or audience refreshes.",
                "Re-run without --no-ai when OPENAI_API_KEY is set for LLM-generated §5.1 / §5.3 copy.",
            ],
            "caveats": ["LLM not invoked (--no-ai)."],
            "source": "skipped",
        }
    else:
        ai_raw = generate_ai_insights(ds, kpis)

    ai_block = normalize_ai_block(ai_raw)

    report = build_report_payload(ds, kpis, ai_block=ai_block, seo_search_console=seo_snapshot)
    paths = write_outputs(report, output_dir, base_name=base_name)

    return {"report": report, "output_paths": paths, "dataset": ds.to_dict()}


def run_email_pipeline(
    *,
    source: str,
    client_id: str,
    client_display_name: str,
    output_dir: str | Path | None,
    skip_ai: bool,
    input_path: str | Path | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    sheet_name: str | int | None = 0,
) -> dict[str, Any]:
    """
    Email channel runner.

    source:
      - excel: requires input_path
      - brevo: uses BREVO_API_KEY from env

    period_start/end default to last 30 days if omitted.
    """
    out = Path(output_dir) if output_dir else Path("output") / client_id / "email"
    out.mkdir(parents=True, exist_ok=True)

    today = date.today()
    ps = date.fromisoformat(period_start) if period_start else (today.replace(day=1))
    pe = date.fromisoformat(period_end) if period_end else today

    if source == "excel":
        if not input_path:
            raise ValueError("Email excel source requires --input")
        ds = ingest_email_excel_export(
            path=input_path,
            client_id=client_id,
            client_display_name=client_display_name,
            period_start=ps,
            period_end=pe,
            sheet_name=sheet_name,
        )
    elif source == "brevo":
        api_key = os.environ.get("BREVO_API_KEY")
        if not api_key:
            raise ValueError("Missing BREVO_API_KEY in environment/.env")
        ds = ingest_brevo_email_campaigns(
            client_id=client_id,
            client_display_name=client_display_name,
            api_key=api_key,
            period_start=ps,
            period_end=pe,
        )
    else:
        raise ValueError("Email source must be one of: excel, brevo")

    report = build_email_report_payload(ds=ds, skip_ai=skip_ai)
    # Optional: same period SEO snapshot (aligns to email runner period window).
    gsc_site = os.environ.get("GOOGLE_SEARCH_CONSOLE_SITE", "").strip()
    if gsc_site and token_path().exists():
        creds = get_credentials()
        q = search_analytics_query(
            creds,
            gsc_site,
            start_date=ps,
            end_date=pe,
            dimensions=["query"],
            row_limit=25,
        )
        p = search_analytics_query(
            creds,
            gsc_site,
            start_date=ps,
            end_date=pe,
            dimensions=["page"],
            row_limit=25,
        )
        report["seo_search_console"] = build_gsc_seo_snapshot(
            site_url=gsc_site,
            start_date=ps,
            end_date=pe,
            query_rows=list(q.get("rows", []) or []),
            page_rows=list(p.get("rows", []) or []),
        ).to_dict()
    paths = write_outputs(report, out, base_name="report")
    return {"report": report, "output_paths": paths, "dataset": ds.to_dict()}
