#!/usr/bin/env python3
"""Verify Google Custom Search JSON API credentials from .env (GOOGLE_API_KEY + GOOGLE_CSE_ID)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

import httpx


def main() -> None:
    load_dotenv(ROOT / ".env")
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    cx = os.environ.get("GOOGLE_CSE_ID", "").strip()
    if not key:
        print("Missing GOOGLE_API_KEY in .env", file=sys.stderr)
        sys.exit(1)
    if not cx:
        print(
            "Missing GOOGLE_CSE_ID in .env (Search engine ID from programmablesearchengine.google.com).",
            file=sys.stderr,
        )
        sys.exit(1)

    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": key, "cx": cx, "q": "test", "num": 1}
    try:
        r = httpx.get(url, params=params, timeout=30.0)
    except httpx.RequestError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        sys.exit(1)

    if r.status_code != 200:
        try:
            body = r.json()
            err = body.get("error", {})
            msg = err.get("message", r.text[:500])
        except Exception:
            msg = r.text[:500]
        print(f"API returned {r.status_code}: {msg}", file=sys.stderr)
        sys.exit(1)

    data = r.json()
    n = int(data.get("searchInformation", {}).get("totalResults", 0) or 0)
    print("OK: Custom Search API accepted the key and cx.")
    print(f"Sample query totalResults (approx): {n}")


if __name__ == "__main__":
    main()
