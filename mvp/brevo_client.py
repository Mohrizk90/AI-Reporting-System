"""
Brevo API client (minimal) for email reporting.

Auth: API key in HTTP header `api-key`.
Docs: https://developers.brevo.com/reference/get-email-campaign
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Iterable

import httpx


@dataclass
class BrevoConfig:
    api_key: str
    base_url: str = "https://api.brevo.com/v3"
    timeout_s: float = 30.0


class BrevoClient:
    def __init__(self, cfg: BrevoConfig):
        self._cfg = cfg
        self._client = httpx.Client(
            base_url=cfg.base_url,
            timeout=cfg.timeout_s,
            headers={"api-key": cfg.api_key, "accept": "application/json"},
        )

    def close(self) -> None:
        self._client.close()

    def _get_with_retry(self, url: str, *, params: dict[str, Any] | None = None, max_retries: int = 10) -> httpx.Response:
        """
        Retry on 429 with exponential backoff.
        Uses Retry-After header if provided; otherwise backs off 5,10,20,40,... seconds (capped).
        """
        attempt = 0
        while True:
            r = self._client.get(url, params=params)
            if r.status_code != 429:
                return r
            attempt += 1
            if attempt > max_retries:
                return r
            retry_after = r.headers.get("retry-after")
            if retry_after and retry_after.isdigit():
                sleep_s = int(retry_after)
            else:
                sleep_s = min(120, 5 * (2 ** (attempt - 1)))
            time.sleep(sleep_s)

    def list_email_campaigns(
        self,
        *,
        limit: int = 50,
        status: str | None = None,
        start_date_utc: str | None = None,
        end_date_utc: str | None = None,
        statistics: str | None = "globalStats",
        exclude_html_content: bool = True,
    ) -> Iterable[dict[str, Any]]:
        """
        Returns campaigns from GET /emailCampaigns with pagination.
        The API provides `count` and `campaigns` in response.
        """
        offset = 0
        while True:
            params: dict[str, Any] = {"limit": limit, "offset": offset}
            if status:
                params["status"] = status
            if start_date_utc:
                params["startDate"] = start_date_utc
            if end_date_utc:
                params["endDate"] = end_date_utc
            if statistics:
                params["statistics"] = statistics
            if exclude_html_content:
                params["excludeHtmlContent"] = True

            r = self._get_with_retry("/emailCampaigns", params=params)
            r.raise_for_status()
            data = r.json() or {}
            campaigns = data.get("campaigns") or []
            for c in campaigns:
                yield c
            if len(campaigns) < limit:
                break
            offset += limit

    def get_email_campaign_report(self, campaign_id: int) -> dict[str, Any]:
        r = self._get_with_retry(
            f"/emailCampaigns/{campaign_id}",
            params={"statistics": "globalStats", "excludeHtmlContent": True},
        )
        r.raise_for_status()
        return r.json() or {}

