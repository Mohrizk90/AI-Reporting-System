#!/usr/bin/env python3
"""Verify Google Search Console API: lists verified properties after OAuth token exists."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from mvp.google_search_console import get_credentials, list_sites, token_path


def main() -> None:
    load_dotenv(ROOT / ".env")
    if not os.environ.get("GOOGLE_CLIENT_ID") or not os.environ.get("GOOGLE_CLIENT_SECRET"):
        print("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env", file=sys.stderr)
        sys.exit(1)
    if not token_path().exists():
        print(
            "No token yet. Run: python scripts/google_gsc_auth.py",
            file=sys.stderr,
        )
        sys.exit(1)

    creds = get_credentials()
    sites = list_sites(creds)
    print("OK: Search Console API — properties you can access:")
    print(json.dumps(sites, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
