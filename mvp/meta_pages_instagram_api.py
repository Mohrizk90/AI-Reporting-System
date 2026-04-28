"""Meta Pages + Instagram insights via Graph API (organic reporting).

This module focuses on *organic* metrics for:
- Facebook Pages
- Instagram Business/Creator accounts (usually connected to a Page)
"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Any

import httpx

DEFAULT_GRAPH_VERSION = "v21.0"


def graph_api_version() -> str:
    return (os.environ.get("META_GRAPH_API_VERSION") or DEFAULT_GRAPH_VERSION).strip().lstrip("/")


def _as_date(d: date) -> str:
    return d.isoformat()


def _sum_insights_values(insights: Any) -> float:
    """Sum {values:[{value:..}]} for the common Graph insights shape."""
    if not isinstance(insights, list):
        return 0.0
    total = 0.0
    for row in insights:
        if not isinstance(row, dict):
            continue
        for v in row.get("values") or []:
            if not isinstance(v, dict):
                continue
            val = v.get("value")
            if isinstance(val, (int, float)):
                total += float(val)
            elif isinstance(val, dict):
                # Some metrics return a dict breakdown; sum numeric entries.
                for _, sub in val.items():
                    if isinstance(sub, (int, float)):
                        total += float(sub)
    return total


def _graph_get(client: httpx.Client, url: str, *, params: dict[str, Any]) -> dict[str, Any]:
    resp = client.get(url, params=params)
    body = resp.json()
    if resp.status_code != 200:
        err = body.get("error", {}) if isinstance(body, dict) else {}
        msg = err.get("message", resp.text[:800])
        code = err.get("code")
        subcode = err.get("error_subcode")
        etype = err.get("type")
        fbtrace = err.get("fbtrace_id")
        bits = []
        if etype:
            bits.append(f"type={etype}")
        if code is not None:
            bits.append(f"code={code}")
        if subcode is not None:
            bits.append(f"subcode={subcode}")
        if fbtrace:
            bits.append(f"fbtrace_id={fbtrace}")
        details = f" ({', '.join(bits)})" if bits else ""
        raise RuntimeError(f"Meta Graph API {resp.status_code}: {msg}{details}")
    if not isinstance(body, dict):
        raise RuntimeError("Meta Graph API returned unexpected non-object JSON")
    return body


def fetch_page_profile(
    *,
    page_id: str,
    access_token: str,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Fetch basic Page profile + connected IG business account if present."""
    ver = graph_api_version()
    url = f"https://graph.facebook.com/{ver}/{page_id}"
    fields = "id,name,instagram_business_account{id,username}"
    with httpx.Client(timeout=timeout) as client:
        return _graph_get(client, url, params={"access_token": access_token, "fields": fields})


def fetch_page_access_token(
    *,
    page_id: str,
    user_access_token: str,
    timeout: float = 60.0,
) -> str:
    """Get a Page access token from a user token via /me/accounts.

    Requires the user to have appropriate Page permissions (e.g. pages_show_list) and tasks.
    """
    ver = graph_api_version()
    url = f"https://graph.facebook.com/{ver}/me/accounts"
    params = {
        "access_token": user_access_token,
        "fields": "id,access_token",
        "limit": 200,
    }
    with httpx.Client(timeout=timeout) as client:
        body = _graph_get(client, url, params=params)
    data = body.get("data") or []
    if isinstance(data, list):
        for row in data:
            if not isinstance(row, dict):
                continue
            if str(row.get("id") or "") == str(page_id):
                tok = (row.get("access_token") or "").strip()
                if tok:
                    return tok
    raise RuntimeError("Could not resolve Page access token from /me/accounts (is the user an admin of this Page?)")


def fetch_facebook_page_insights(
    *,
    page_id: str,
    access_token: str,
    since: date,
    until: date,
    metrics: list[str] | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Fetch day-granular Page insights and return summed totals for the range."""
    ver = graph_api_version()
    url = f"https://graph.facebook.com/{ver}/{page_id}/insights"
    m = metrics or [
        # Avoid deprecated Page Insights metrics (Meta has been removing many legacy metrics).
        # See: https://developers.facebook.com/docs/platforminsights/page/deprecated-metrics
        "page_media_view",
        "page_total_media_view_unique",
        "page_fan_adds_by_paid_non_paid_unique",
    ]
    params = {
        "access_token": access_token,
        "metric": ",".join(m),
        "period": "day",
        "since": _as_date(since),
        "until": _as_date(until),
    }
    with httpx.Client(timeout=timeout) as client:
        body = _graph_get(client, url, params=params)
    data = body.get("data") or []
    totals: dict[str, float] = {}
    if isinstance(data, list):
        for row in data:
            if not isinstance(row, dict):
                continue
            name = row.get("name")
            if not name:
                continue
            totals[str(name)] = _sum_insights_values([row])
    return {
        "source": "meta_pages_instagram",
        "graph_api_version": ver,
        "page_id": page_id,
        "time_range": {"since": _as_date(since), "until": _as_date(until)},
        "facebook_page": {
            "metrics": m,
            "totals": totals,
        },
    }


def fetch_instagram_account_insights(
    *,
    ig_user_id: str,
    access_token: str,
    since: date,
    until: date,
    metrics: list[str] | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Fetch day-granular Instagram insights and return summed totals for the range."""
    ver = graph_api_version()
    url = f"https://graph.facebook.com/{ver}/{ig_user_id}/insights"
    m = metrics or [
        "impressions",
        "reach",
        "profile_views",
    ]
    params = {
        "access_token": access_token,
        "metric": ",".join(m),
        "period": "day",
        "since": _as_date(since),
        "until": _as_date(until),
    }
    with httpx.Client(timeout=timeout) as client:
        body = _graph_get(client, url, params=params)
    data = body.get("data") or []
    totals: dict[str, float] = {}
    if isinstance(data, list):
        for row in data:
            if not isinstance(row, dict):
                continue
            name = row.get("name")
            if not name:
                continue
            totals[str(name)] = _sum_insights_values([row])
    return {
        "source": "meta_pages_instagram",
        "graph_api_version": ver,
        "ig_user_id": ig_user_id,
        "time_range": {"since": _as_date(since), "until": _as_date(until)},
        "instagram": {
            "metrics": m,
            "totals": totals,
        },
    }


def fetch_meta_organic_snapshot(
    *,
    page_id: str,
    access_token: str,
    since: date,
    until: date,
    include_instagram: bool = True,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Convenience wrapper: Page profile + FB Page totals + IG totals (if connected)."""
    # Page insights must be called with a Page access token. If the caller provided a user token,
    # we can derive a Page token via /me/accounts. If the caller already provided a Page token,
    # /me/accounts will generally fail; in that case we keep the original token.
    page_token = access_token
    try:
        page_token = fetch_page_access_token(page_id=page_id, user_access_token=access_token, timeout=timeout)
    except Exception:
        page_token = access_token

    profile = fetch_page_profile(page_id=page_id, access_token=page_token, timeout=timeout)
    fb = fetch_facebook_page_insights(
        page_id=page_id,
        access_token=page_token,
        since=since,
        until=until,
        timeout=timeout,
    )
    out: dict[str, Any] = {
        "source": "meta_pages_instagram",
        "graph_api_version": fb.get("graph_api_version"),
        "time_range": fb.get("time_range"),
        "token_type": "page",
        "page": {"id": profile.get("id"), "name": profile.get("name")},
        "facebook_page": fb.get("facebook_page"),
    }
    if include_instagram:
        ig = (profile.get("instagram_business_account") or {}) if isinstance(profile, dict) else {}
        ig_id = ig.get("id") if isinstance(ig, dict) else None
        if ig_id:
            try:
                ig_block = fetch_instagram_account_insights(
                    ig_user_id=str(ig_id),
                    access_token=page_token,
                    since=since,
                    until=until,
                    timeout=timeout,
                )
                out["instagram"] = {
                    "id": ig_id,
                    "username": ig.get("username"),
                    **(ig_block.get("instagram") or {}),
                }
            except Exception as e:
                out["instagram"] = {
                    "id": ig_id,
                    "username": ig.get("username"),
                    "error": f"Instagram insights fetch failed: {type(e).__name__}: {e}",
                }
        else:
            out["instagram"] = {"error": "No instagram_business_account connected to this Page."}
    return out

