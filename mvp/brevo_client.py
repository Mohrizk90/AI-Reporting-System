"""
Brevo API client (minimal) for email reporting.

Auth: API key in HTTP header `api-key`.
Docs: https://developers.brevo.com/reference/get-email-campaign
"""

from __future__ import annotations

from dataclasses import dataclass
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

    def list_email_campaigns(self, limit: int = 50) -> Iterable[dict[str, Any]]:
        """
        Returns campaigns from GET /emailCampaigns with pagination.
        The API provides `count` and `campaigns` in response.
        """
        offset = 0
        while True:
            r = self._client.get("/emailCampaigns", params={"limit": limit, "offset": offset})
            r.raise_for_status()
            data = r.json() or {}
            campaigns = data.get("campaigns") or []
            for c in campaigns:
                yield c
            if len(campaigns) < limit:
                break
            offset += limit

    def get_email_campaign_report(self, campaign_id: int) -> dict[str, Any]:
        r = self._client.get(
            f"/emailCampaigns/{campaign_id}",
            params={"statistics": "globalStats", "excludeHtmlContent": True},
        )
        r.raise_for_status()
        return r.json() or {}

