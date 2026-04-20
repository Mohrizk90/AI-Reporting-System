#!/usr/bin/env python3
"""CLI: build one combined monthly report for multiple clients.

Config file format (JSON):
{
  "title": "Monthly Marketing Report",
  "subtitle": "April 2026",
  "prepared_by": "Pedicel Marketing",
  "output_dir": "output/monthly",
  "clients": [
    {
      "client_id": "isn",
      "client_name": "ISN Medical",
      "meta_export_path": "Files/ISN-....csv",
      "gsc_site_url": "https://isnmedical.com/"
    },
    {
      "client_id": "yoa",
      "client_name": "YOA Insurance",
      "meta_export_path": "Files/YOA ....xlsx",
      "gsc_site_url": "https://yoainsurance.com/"
    }
  ]
}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from mvp.formatters import write_outputs
from mvp.google_search_console import get_credentials, search_analytics_query, token_path
from mvp.ingest import normalize_meta_export
from mvp.kpis import compute_aggregate_kpis
from mvp.monthly_combined_report import build_monthly_combined_report_payload
from mvp.paid_ads_template import build_paid_ads_template_report
from mvp.seo_gsc_report import build_gsc_seo_snapshot
from mvp.email_ingest_brevo import ingest_brevo_email_campaigns
from mvp.email_report_model import build_email_report_payload


def main() -> None:
    load_dotenv(ROOT / ".env")
    p = argparse.ArgumentParser(description="Build a combined monthly report (multi-client, multi-source)")
    p.add_argument("--config", type=Path, required=True, help="Path to JSON config file")
    args = p.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    title = cfg.get("title", "Monthly Marketing Report")
    subtitle = cfg.get("subtitle")
    prepared_by = cfg.get("prepared_by", "Pedicel Marketing")
    out_dir = Path(cfg.get("output_dir", "output/monthly"))

    if not token_path().exists():
        raise SystemExit("No GSC token. Run: python scripts/google_gsc_auth.py")

    creds = get_credentials()

    combined_clients: list[dict] = []
    connected: dict[str, dict[str, str]] = {}
    for c in cfg.get("clients", []):
        client_id = c["client_id"]
        client_name = c["client_name"]
        meta_path = Path(c["meta_export_path"])
        gsc_site = c.get("gsc_site_url", "").strip()

        ds = normalize_meta_export(meta_path, client_id=client_id, client_display_name=client_name, sheet_name=0)
        kpis = compute_aggregate_kpis(ds)
        paid_ads_report = build_paid_ads_template_report(ds, kpis, ai_block={})
        connected["meta_ads_campaign_export"] = {
            "id": "meta_ads_campaign_export",
            "name": "Meta Ads campaign export (CSV/XLSX)",
            "purpose": "Paid media performance from Meta Ads Manager export files",
        }

        seo = None
        if gsc_site:
            ps = ds.rows[0].reporting_starts if ds.rows else None
            pe = ds.rows[0].reporting_ends if ds.rows else None
            if ps and pe:
                try:
                    q = search_analytics_query(
                        creds,
                        gsc_site,
                        start_date=ps,
                        end_date=pe,
                        dimensions=["query"],
                        row_limit=25,
                    )
                    pg = search_analytics_query(
                        creds,
                        gsc_site,
                        start_date=ps,
                        end_date=pe,
                        dimensions=["page"],
                        row_limit=25,
                    )
                    seo = build_gsc_seo_snapshot(
                        site_url=gsc_site,
                        start_date=ps,
                        end_date=pe,
                        query_rows=list(q.get("rows", []) or []),
                        page_rows=list(pg.get("rows", []) or []),
                    ).to_dict()
                    connected["google_search_console_api"] = {
                        "id": "google_search_console_api",
                        "name": "Google Search Console API",
                        "purpose": "SEO / organic search performance",
                    }
                except Exception as e:
                    # Don't fail the entire monthly report if GSC is temporarily unreachable.
                    seo = {
                        "source": "google_search_console_api",
                        "site_url": gsc_site,
                        "start_date": ps.isoformat(),
                        "end_date": pe.isoformat(),
                        "error": f"GSC fetch failed: {type(e).__name__}: {e}",
                    }

        # Email (Brevo) — optional per client, uses global BREVO_API_KEY by default
        email_report = None
        brevo_key = (c.get("brevo_api_key") or "").strip() or (os.environ.get("BREVO_API_KEY") or "").strip()
        if brevo_key:
            try:
                ps = ds.rows[0].reporting_starts if ds.rows else None
                pe = ds.rows[0].reporting_ends if ds.rows else None
                if ps and pe:
                    email_ds = ingest_brevo_email_campaigns(
                        client_id=client_id,
                        client_display_name=client_name,
                        api_key=brevo_key,
                        period_start=ps,
                        period_end=pe,
                        limit=int(c.get("brevo_limit") or 50),
                    )
                    email_payload = build_email_report_payload(ds=email_ds, skip_ai=True)
                    email_report = email_payload.get("email_report")
                    connected["brevo_api"] = {
                        "id": "brevo_api",
                        "name": "Brevo API",
                        "purpose": "Email campaigns and related ESP metrics",
                    }
            except Exception as e:
                email_report = {
                    "document": {
                        "report_title": "Email Marketing Performance Report",
                        "report_subtitle": "",
                        "header_line": "",
                    },
                    "error": f"Brevo fetch failed: {type(e).__name__}: {e}",
                }

        combined_clients.append(
            {
                "client_id": client_id,
                "client_name": client_name,
                "paid_ads_report": paid_ads_report,
                "seo_search_console": seo,
                "email_report": email_report,
            }
        )

    payload = build_monthly_combined_report_payload(
        title=title,
        subtitle=subtitle,
        prepared_by=prepared_by,
        connected_sources=list(connected.values()),
        clients=combined_clients,
    )
    paths = write_outputs(payload, out_dir, base_name="monthly_report")
    print("Written:", json.dumps(paths, indent=2))


if __name__ == "__main__":
    main()

