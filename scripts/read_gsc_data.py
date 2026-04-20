#!/usr/bin/env python3
"""Read Search Console performance data (search analytics). Requires OAuth token + property URL."""

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

from mvp.google_search_console import (
    get_credentials,
    list_sites,
    search_analytics_last_days,
    token_path,
)


def main() -> None:
    load_dotenv(ROOT / ".env")
    p = argparse.ArgumentParser(
        description="Fetch Google Search Console search analytics (queries, clicks, impressions, etc.)",
    )
    p.add_argument(
        "--site",
        default=os.environ.get("GOOGLE_SEARCH_CONSOLE_SITE", "").strip(),
        help="Property URL as in GSC (e.g. https://www.example.com/ or sc-domain:example.com). "
        "Default: GOOGLE_SEARCH_CONSOLE_SITE in .env",
    )
    p.add_argument("--days", type=int, default=28, help="Last N days ending today (default 28)")
    p.add_argument(
        "--dimensions",
        default="query",
        help="Comma-separated API dimensions (default: query). Examples: query, page, date, country, device",
    )
    p.add_argument("--limit", type=int, default=50, help="Max rows (default 50, max 25000)")
    p.add_argument(
        "--list-sites-only",
        action="store_true",
        help="Only list properties you have access to (no analytics query)",
    )
    args = p.parse_args()

    if not os.environ.get("GOOGLE_CLIENT_ID") or not os.environ.get("GOOGLE_CLIENT_SECRET"):
        print("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env", file=sys.stderr)
        sys.exit(1)
    if not token_path().exists():
        print("No OAuth token. Run: python scripts/google_gsc_auth.py", file=sys.stderr)
        sys.exit(1)

    creds = get_credentials()
    if args.list_sites_only:
        sites = list_sites(creds)
        print(json.dumps(sites, indent=2, ensure_ascii=False))
        return

    site = args.site
    if not site:
        sites = list_sites(creds)
        print(
            "No --site and no GOOGLE_SEARCH_CONSOLE_SITE. Properties you can use:\n",
            file=sys.stderr,
        )
        for s in sites:
            print(f"  {s.get('siteUrl')}", file=sys.stderr)
        print(
            "\nSet GOOGLE_SEARCH_CONSOLE_SITE in .env or pass --site \"...\"",
            file=sys.stderr,
        )
        sys.exit(1)

    dims = [d.strip() for d in args.dimensions.split(",") if d.strip()]
    data = search_analytics_last_days(
        creds,
        site,
        days=args.days,
        dimensions=dims,
        row_limit=args.limit,
    )
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
