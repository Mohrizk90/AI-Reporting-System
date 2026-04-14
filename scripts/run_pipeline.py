#!/usr/bin/env python3
"""CLI: run Paid Ads (Meta) and Email pipelines."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from mvp.pipeline import run_email_pipeline, run_pipeline


def main() -> None:
    load_dotenv(ROOT / ".env")
    p = argparse.ArgumentParser(description="Marketing report MVP (Pedicel template-aligned)")
    p.add_argument("--channel", default="paid_ads", choices=["paid_ads", "email"], help="Which report to run")
    p.add_argument("--source", default="excel", choices=["excel", "brevo"], help="For email: excel or brevo")
    p.add_argument("--input", type=Path, default=None, help="Input file path (paid_ads or email excel)")
    p.add_argument("--client-id", required=True, help="Short id, e.g. isn, yoa")
    p.add_argument("--client-name", required=True, help="Display name")
    p.add_argument("--output-dir", type=Path, default=None, help="Default: output/<client-id>")
    p.add_argument("--sheet", default=0, help="Excel sheet name or index (default 0)")
    p.add_argument("--period-start", default=None, help="Email period start YYYY-MM-DD (optional)")
    p.add_argument("--period-end", default=None, help="Email period end YYYY-MM-DD (optional)")
    p.add_argument("--no-ai", action="store_true", help="Skip OpenAI call")
    p.add_argument("--json-only", action="store_true", help="Print report JSON to stdout")
    args = p.parse_args()

    sheet: str | int = args.sheet
    if isinstance(sheet, str) and sheet.isdigit():
        sheet = int(sheet)

    if args.channel == "paid_ads":
        if not args.input:
            p.error("--input is required for paid_ads")
        result = run_pipeline(
            input_path=args.input,
            client_id=args.client_id,
            client_display_name=args.client_name,
            output_dir=args.output_dir,
            sheet_name=sheet,
            skip_ai=args.no_ai,
        )
    else:
        result = run_email_pipeline(
            source=args.source,
            client_id=args.client_id,
            client_display_name=args.client_name,
            output_dir=args.output_dir,
            skip_ai=args.no_ai,
            input_path=args.input,
            period_start=args.period_start,
            period_end=args.period_end,
            sheet_name=sheet,
        )
    if args.json_only:
        print(json.dumps(result["report"], indent=2, ensure_ascii=False))
    else:
        print("Written:", json.dumps(result["output_paths"], indent=2))


if __name__ == "__main__":
    main()
