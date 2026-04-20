#!/usr/bin/env python3
"""Run OAuth once: opens browser, saves token for Search Console API (see mvp/google_search_console.py)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from mvp.google_search_console import get_credentials, token_path


def main() -> None:
    load_dotenv(ROOT / ".env")
    p = argparse.ArgumentParser(description="Authorize Google Search Console (OAuth) and save token")
    p.add_argument(
        "--reauth",
        action="store_true",
        help="Ignore existing token and sign in again",
    )
    p.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not launch a browser — copy the printed URL into Chrome/Edge manually",
    )
    args = p.parse_args()

    if not args.no_browser:
        print(
            "Starting local OAuth (leave this window open until you see 'Saved:').\n"
            "If the browser does not open: Ctrl+C and re-run with --no-browser\n"
            "If you see redirect_uri_mismatch: set GOOGLE_OAUTH_CLIENT_TYPE=web and add "
            "http://127.0.0.1:8765/ to Authorized redirect URIs (or create a Desktop OAuth client).\n"
        )

    get_credentials(force_reauth=args.reauth, open_browser=not args.no_browser)
    print("Saved:", token_path())


if __name__ == "__main__":
    main()
