#!/usr/bin/env python3
"""Verify Meta organic pages integration (Facebook Page + Instagram, if connected)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mvp.meta_pages_instagram_api import fetch_meta_organic_snapshot


def main() -> None:
    load_dotenv(ROOT / ".env", override=True)
    p = argparse.ArgumentParser(description="Fetch Meta organic insights for a Facebook Page (+ IG if connected)")
    p.add_argument("--page-id", default=(os.environ.get("META_PAGE_ID") or "").strip(), help="Facebook Page ID")
    p.add_argument(
        "--token",
        default=(
            (os.environ.get("META_ACCESS_TOKEN") or "").strip()
            or (os.environ.get("META_ISN_PAGES_ACCESS_TOKEN") or "").strip()
            or (os.environ.get("META_ISN_ACCESS_TOKEN") or "").strip()
        ),
        help="Access token (META_ACCESS_TOKEN, META_ISN_PAGES_ACCESS_TOKEN, or META_ISN_ACCESS_TOKEN)",
    )
    p.add_argument("--since", default=None, help="YYYY-MM-DD (default: 28 days ago)")
    p.add_argument("--until", default=None, help="YYYY-MM-DD (default: today)")
    p.add_argument("--no-instagram", action="store_true", help="Skip Instagram lookup/insights")
    args = p.parse_args()

    if not args.page_id or not args.token:
        print("Set --page-id and --token (or META_PAGE_ID + META_ACCESS_TOKEN in .env)", file=sys.stderr)
        raise SystemExit(1)

    end = date.fromisoformat(args.until) if args.until else date.today()
    start = date.fromisoformat(args.since) if args.since else (end - timedelta(days=27))

    data = fetch_meta_organic_snapshot(
        page_id=args.page_id,
        access_token=args.token,
        since=start,
        until=end,
        include_instagram=not args.no_instagram,
    )
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

