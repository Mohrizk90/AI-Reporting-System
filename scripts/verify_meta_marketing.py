#!/usr/bin/env python3
"""Verify Meta Marketing API: fetch campaign insights for an ad account."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from mvp.meta_marketing_api import fetch_campaign_insights


def _env_first(*names: str) -> str:
    for n in names:
        v = (os.environ.get(n) or "").strip()
        if v:
            return v
    return ""


def _meta_from_monthly_config(cfg_path: Path, client_id: str) -> tuple[str, str, str | None]:
    """Returns (ad_account_id, access_token, app_id_or_none) from one client's meta_marketing_api block."""
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    for c in cfg.get("clients", []) or []:
        if (c.get("client_id") or "").strip() != client_id:
            continue
        mm = c.get("meta_marketing_api")
        if not isinstance(mm, dict):
            break
        acct = (mm.get("ad_account_id") or "").strip()
        acct_e = (mm.get("ad_account_id_env") or "").strip()
        if not acct and acct_e:
            acct = _env_first(acct_e)
        token_env = (mm.get("access_token_env") or "").strip()
        token = _env_first(token_env) if token_env else (mm.get("access_token") or "").strip()
        app_id_env = (mm.get("app_id_env") or "").strip()
        app_id = _env_first(app_id_env) if app_id_env else (mm.get("app_id") or "").strip() or None
        return acct, token, app_id
    return "", "", None


def _meta_env_diag(cfg_path: Path, client_id: str) -> str:
    """Short hint: which *env* names from config are unset (does not print secret values)."""
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except OSError:
        return ""
    for c in cfg.get("clients", []) or []:
        if (c.get("client_id") or "").strip() != client_id:
            continue
        mm = c.get("meta_marketing_api")
        if not isinstance(mm, dict):
            return f"client {client_id!r} has no meta_marketing_api object in {cfg_path.name}"
        bits: list[str] = []
        for label, env_key in (
            ("ad account", (mm.get("ad_account_id_env") or "").strip()),
            ("token", (mm.get("access_token_env") or "").strip()),
        ):
            if not env_key:
                continue
            ok = bool((os.environ.get(env_key) or "").strip())
            bits.append(f"{env_key} ({label}): {'ok' if ok else 'missing or empty'}")
        return "; ".join(bits) if bits else "meta_marketing_api has no ad_account_id_env / access_token_env"
    return f"no client_id {client_id!r} in {cfg_path.name}"


def main() -> None:
    # Make runs deterministic: values in .env should override any pre-set terminal env vars.
    load_dotenv(ROOT / ".env", override=True)
    p = argparse.ArgumentParser(description="Fetch Meta Ads campaign insights (Marketing API)")
    p.add_argument(
        "--account",
        default=None,
        help="Ad account id, e.g. act_123 or 123 (if omitted, uses --client-id config, else env fallbacks)",
    )
    p.add_argument(
        "--token",
        default=None,
        help="Access token (if omitted, uses --client-id config, else env fallbacks)",
    )
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Monthly report JSON (e.g. monthly_report_config.json); use with --client-id to fill account/token from meta_marketing_api",
    )
    p.add_argument(
        "--client-id",
        default="",
        help="Client id inside --config (e.g. yoa); reads ad_account_id and access_token_env from meta_marketing_api",
    )
    p.add_argument(
        "--print-token-fingerprint",
        action="store_true",
        help="Print a non-reversible fingerprint of the resolved token (for debugging which token is being used).",
    )
    p.add_argument("--since", default=None, help="YYYY-MM-DD (default: 28 days ago)")
    p.add_argument("--until", default=None, help="YYYY-MM-DD (default: today)")
    args = p.parse_args()

    # If --client-id is provided, prefer the per-client meta_marketing_api block.
    # Explicit CLI flags should always win.
    account = (args.account or "").strip()
    token = (args.token or "").strip()
    cfg_path = args.config
    if args.client_id.strip():
        if cfg_path is None:
            default_cfg = ROOT / "monthly_report_config.json"
            if default_cfg.is_file():
                cfg_path = default_cfg
        if cfg_path and cfg_path.is_file():
            acct_mm, tok_mm, _app_mm = _meta_from_monthly_config(cfg_path, args.client_id.strip())
            if not account and acct_mm:
                account = acct_mm
            if not token and tok_mm:
                token = tok_mm

    # If still missing, fall back to generic env vars (useful for ad-hoc calls).
    if not account:
        account = _env_first("META_AD_ACCOUNT_ID", "META_YOA_AD_ACCOUNT_ID")
    if not token:
        token = _env_first("META_ACCESS_TOKEN", "META_YOA_ACCESS_TOKEN")

    if not account or not token:
        print(
            "Set --account and --token, or in .env: META_AD_ACCOUNT_ID + META_ACCESS_TOKEN, "
            "or META_YOA_AD_ACCOUNT_ID + META_YOA_ACCESS_TOKEN.\n"
            "Or put meta_marketing_api on a client in monthly_report_config.json and run:\n"
            "  python scripts/verify_meta_marketing.py --client-id yoa",
            file=sys.stderr,
        )
        cid = args.client_id.strip()
        cfg_try = args.config or (ROOT / "monthly_report_config.json")
        if cid and cfg_try.is_file():
            print(f"Diagnosis ({cfg_try.name}, client {cid!r}): {_meta_env_diag(cfg_try, cid)}", file=sys.stderr)
        sys.exit(1)

    if args.print_token_fingerprint:
        fp = hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]
        print(f"Token fingerprint (sha256[:12]): {fp}", file=sys.stderr)

    end = date.fromisoformat(args.until) if args.until else date.today()
    start = date.fromisoformat(args.since) if args.since else (end - timedelta(days=27))

    app_id = _env_first("META_APP_ID", "META_YOA_APP_ID") or None
    if args.client_id.strip() and cfg_path and cfg_path.is_file():
        _a, _t, app_from_cfg = _meta_from_monthly_config(cfg_path, args.client_id.strip())
        if app_from_cfg:
            app_id = app_from_cfg

    data = fetch_campaign_insights(
        ad_account_id=account,
        access_token=token,
        since=start,
        until=end,
        app_id=app_id,
    )
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
