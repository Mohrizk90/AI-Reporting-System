"""Google Search Console API — OAuth2 user credentials (read-only webmasters scope)."""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TOKEN_PATH = ROOT / "google_gsc_token.json"

# Fixed loopback port so "Web application" OAuth clients can register one redirect URI.
_DEFAULT_LOOPBACK_PORT = 8765


def _oauth_client_type() -> str:
    v = os.environ.get("GOOGLE_OAUTH_CLIENT_TYPE", "installed").strip().lower()
    if v in ("web", "web_app", "installed", "desktop"):
        if v in ("desktop",):
            return "installed"
        if v in ("web_app",):
            return "web"
        return v
    return "installed"


def _loopback_port() -> int:
    if os.environ.get("GOOGLE_OAUTH_USE_DYNAMIC_PORT", "").strip() in ("1", "true", "yes"):
        return 0
    raw = os.environ.get("GOOGLE_OAUTH_REDIRECT_PORT", "").strip()
    if raw:
        return int(raw)
    return _DEFAULT_LOOPBACK_PORT


def _client_config() -> dict[str, Any]:
    cid = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    sec = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
    if not cid or not sec:
        raise ValueError("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")

    common = {
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    }

    client_type = _oauth_client_type()
    if client_type == "web":
        port = _loopback_port()
        if port == 0:
            raise ValueError(
                "GOOGLE_OAUTH_USE_DYNAMIC_PORT is not compatible with GOOGLE_OAUTH_CLIENT_TYPE=web. "
                "Set a fixed GOOGLE_OAUTH_REDIRECT_PORT (default 8765) and add "
                f"http://127.0.0.1:{_DEFAULT_LOOPBACK_PORT}/ to Authorized redirect URIs."
            )
        redirect = f"http://127.0.0.1:{port}/"
        return {
            "web": {
                "client_id": cid,
                "client_secret": sec,
                **common,
                "redirect_uris": [redirect],
            }
        }

    return {
        "installed": {
            "client_id": cid,
            "client_secret": sec,
            **common,
            "redirect_uris": ["http://localhost"],
        }
    }


def token_path() -> Path:
    return Path(os.environ.get("GOOGLE_GSC_TOKEN_PATH", str(DEFAULT_TOKEN_PATH)))


_AUTH_PROMPT = (
    "\nIf nothing opens, copy this link into your browser:\n{url}\n"
)


def _print_oauth_hint(port: int) -> None:
    if port == 0:
        print(
            "\nUsing a random loopback port (Desktop OAuth client only). "
            "If you see redirect_uri_mismatch, create a Desktop app client or switch to fixed port — see .env.example.\n",
            file=sys.stderr,
        )
        return
    print(
        f"\nRedirect URI (must match Google Cloud → Credentials → your OAuth client):\n"
        f"  http://127.0.0.1:{port}/\n"
        f"For 'Web application' clients, add exactly that under Authorized redirect URIs.\n",
        file=sys.stderr,
    )


def get_credentials(*, force_reauth: bool = False, open_browser: bool = True) -> Credentials:
    """
    Load or obtain OAuth credentials. First run opens a browser; token is saved for later runs.

    **OAuth client types (Google Cloud Console → Credentials):**

    - **Desktop app** — use ``GOOGLE_OAUTH_CLIENT_TYPE=installed`` (default). Dynamic or fixed port both work.
    - **Web application** — set ``GOOGLE_OAUTH_CLIENT_TYPE=web`` and register redirect
      ``http://127.0.0.1:8765/`` (or your ``GOOGLE_OAUTH_REDIRECT_PORT``) under Authorized redirect URIs.

    Uses ``prompt=consent`` so Google returns a **refresh_token** reliably.
    """
    path = token_path()
    creds: Credentials | None = None
    if path.exists() and not force_reauth:
        creds = Credentials.from_authorized_user_file(str(path), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(creds.to_json(), encoding="utf-8")
        return creds

    flow = InstalledAppFlow.from_client_config(_client_config(), SCOPES)
    prompt = _AUTH_PROMPT if open_browser else (
        "\nOpen this URL in your browser, then sign in and approve:\n{url}\n"
    )

    port = _loopback_port()
    _print_oauth_hint(port)

    oauth_kwargs: dict[str, Any] = {
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
    }

    try:
        creds = flow.run_local_server(
            host="127.0.0.1",
            port=port,
            open_browser=open_browser,
            authorization_prompt_message=prompt,
            **oauth_kwargs,
        )
    except OSError as e:
        msg = str(e).lower()
        addr_in_use = port != 0 and (
            getattr(e, "errno", None) in (98, 10048, 48)
            or "address already in use" in msg
            or "only one usage of each socket address" in msg
        )
        if addr_in_use:
            print(
                f"Port {port} in use; retrying with a random port (Desktop OAuth client only).\n",
                file=sys.stderr,
            )
            flow = InstalledAppFlow.from_client_config(_client_config(), SCOPES)
            creds = flow.run_local_server(
                host="127.0.0.1",
                port=0,
                open_browser=open_browser,
                authorization_prompt_message=prompt,
                **oauth_kwargs,
            )
        else:
            raise

    if getattr(creds, "refresh_token", None) is None:
        print(
            "Warning: no refresh_token in response. Delete the token file and re-run with --reauth; "
            "ensure prompt=consent is allowed and you use access_type=offline.\n",
            file=sys.stderr,
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def build_search_console_service(creds: Credentials):
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def _http_error_message(err: HttpError) -> str:
    try:
        import json as _json

        if err.content:
            data = _json.loads(err.content.decode("utf-8", errors="replace"))
            return str(data.get("error", {}).get("message") or data)[:800]
    except Exception:
        pass
    return str(err)[:800]


def list_sites(creds: Credentials) -> list[dict[str, Any]]:
    service = build_search_console_service(creds)
    try:
        resp = service.sites().list().execute()
    except HttpError as e:
        raise RuntimeError(
            f"Search Console API error ({e.resp.status}): {_http_error_message(e)}. "
            "Enable 'Google Search Console API' for this Cloud project and ensure the OAuth "
            "consent screen includes scope webmasters.readonly."
        ) from e
    return list(resp.get("siteEntry", []) or [])


def search_analytics_query(
    creds: Credentials,
    site_url: str,
    *,
    start_date: date,
    end_date: date,
    dimensions: list[str] | None = None,
    row_limit: int = 250,
    search_type: str = "web",
) -> dict[str, Any]:
    """
    Performance report (same core metrics as Search Console → Performance).

    site_url must match a property in Search Console exactly, e.g.:
      https://www.example.com/  or  sc-domain:example.com

    dimensions: e.g. ['query'], ['page'], ['date'], ['country'], ['device'],
      or combinations like ['date', 'query'] (see API docs for limits).
    """
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")
    dims = dimensions if dimensions is not None else ["query"]
    body: dict[str, Any] = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": dims,
        "rowLimit": min(max(row_limit, 1), 25_000),
        "searchType": search_type,
    }
    service = build_search_console_service(creds)
    try:
        return (
            service.searchanalytics()
            .query(siteUrl=site_url, body=body)
            .execute()
        )
    except HttpError as e:
        raise RuntimeError(
            f"Search analytics error ({e.resp.status}) for siteUrl={site_url!r}: {_http_error_message(e)}"
        ) from e


def search_analytics_last_days(
    creds: Credentials,
    site_url: str,
    *,
    days: int = 28,
    dimensions: list[str] | None = None,
    row_limit: int = 250,
) -> dict[str, Any]:
    """Convenience: last `days` days ending today (inclusive)."""
    end = date.today()
    start = end - timedelta(days=max(days - 1, 0))
    return search_analytics_query(
        creds,
        site_url,
        start_date=start,
        end_date=end,
        dimensions=dimensions,
        row_limit=row_limit,
    )
