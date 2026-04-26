"""Meta Marketing API — campaign-level insights via Graph API (read-only style GETs)."""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Any

import httpx

DEFAULT_GRAPH_VERSION = "v21.0"


def graph_api_version() -> str:
    return (os.environ.get("META_GRAPH_API_VERSION") or DEFAULT_GRAPH_VERSION).strip().lstrip("/")


def normalize_ad_account_id(raw: str) -> str:
    s = raw.strip()
    if not s:
        raise ValueError("ad_account_id is empty")
    if s.startswith("act_"):
        return s
    return f"act_{s}"


def _float(v: Any) -> float:
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _link_clicks_from_actions(actions: Any) -> int | None:
    if not isinstance(actions, list):
        return None
    for a in actions:
        if not isinstance(a, dict):
            continue
        if a.get("action_type") == "link_click":
            try:
                return int(float(a.get("value", 0)))
            except (TypeError, ValueError):
                return None
    return None


def fetch_campaign_insights(
    *,
    ad_account_id: str,
    access_token: str,
    since: date,
    until: date,
    app_id: str | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """
    Pull campaign-level insights for ``since``–``until`` (inclusive dates, YYYY-MM-DD).

    Requires a user/system token with ``ads_read`` (and access to the ad account).
    ``app_id`` is optional metadata only (not sent on every request).
    """
    acct = normalize_ad_account_id(ad_account_id)
    ver = graph_api_version()
    base = f"https://graph.facebook.com/{ver}/{acct}/insights"

    time_range = json.dumps({"since": since.isoformat(), "until": until.isoformat()})
    fields = ",".join(
        [
            "campaign_id",
            "campaign_name",
            "spend",
            "impressions",
            "clicks",
            "reach",
            "actions",
        ]
    )

    rows: list[dict[str, Any]] = []
    next_url: str | None = None
    first_params = {
        "access_token": access_token,
        "level": "campaign",
        "fields": fields,
        "time_range": time_range,
        "limit": 500,
    }

    with httpx.Client(timeout=timeout) as client:
        while True:
            if next_url:
                resp = client.get(next_url)
            else:
                resp = client.get(base, params=first_params)
            body = resp.json()
            if resp.status_code != 200:
                err = body.get("error", {}) if isinstance(body, dict) else {}
                msg = err.get("message", resp.text[:800])
                code = err.get("code")
                subcode = err.get("error_subcode")
                etype = err.get("type")
                fbtrace = err.get("fbtrace_id")
                detail_bits = []
                if etype:
                    detail_bits.append(f"type={etype}")
                if code is not None:
                    detail_bits.append(f"code={code}")
                if subcode is not None:
                    detail_bits.append(f"subcode={subcode}")
                if fbtrace:
                    detail_bits.append(f"fbtrace_id={fbtrace}")
                details = f" ({', '.join(detail_bits)})" if detail_bits else ""
                raise RuntimeError(f"Meta Graph API {resp.status_code}: {msg}{details}")
            chunk = body.get("data") or []
            if isinstance(chunk, list):
                rows.extend(chunk)
            paging = body.get("paging") or {}
            next_url = paging.get("next") if isinstance(paging, dict) else None
            if not next_url:
                break

    normalized: list[dict[str, Any]] = []
    total_spend = 0.0
    total_impressions = 0.0
    total_clicks = 0.0
    total_reach = 0.0  # sum of row reach is not additive across campaigns; still useful as rough sum
    for r in rows:
        spend = _float(r.get("spend"))
        imp = _float(r.get("impressions"))
        clk = _float(r.get("clicks"))
        reach = _float(r.get("reach"))
        lc = _link_clicks_from_actions(r.get("actions"))
        normalized.append(
            {
                "campaign_id": r.get("campaign_id"),
                "campaign_name": r.get("campaign_name"),
                "spend": spend,
                "impressions": int(imp) if imp else 0,
                "clicks": int(clk) if clk else 0,
                "reach": int(reach) if reach else 0,
                "link_clicks": lc,
            }
        )
        total_spend += spend
        total_impressions += imp
        total_clicks += clk
        total_reach += reach

    ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0.0
    cpm = (total_spend / total_impressions * 1000.0) if total_impressions > 0 else 0.0

    return {
        "source": "meta_marketing_api",
        "graph_api_version": ver,
        "app_id": app_id,
        "ad_account_id": acct,
        "time_range": {"since": since.isoformat(), "until": until.isoformat()},
        "row_count": len(normalized),
        "campaigns": normalized,
        "totals": {
            "spend": total_spend,
            "impressions": total_impressions,
            "clicks": total_clicks,
            "reach_sum_rows": total_reach,
            "ctr": ctr,
            "cpm": cpm,
        },
    }
