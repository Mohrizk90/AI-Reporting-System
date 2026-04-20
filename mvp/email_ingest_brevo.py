"""Ingest email reporting data from Brevo API into EmailDataset."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from mvp.brevo_client import BrevoClient, BrevoConfig
from mvp.email_schema import EmailCampaignRow, EmailDataset


def _parse_dt(val: Any) -> datetime | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except Exception:
        return None


def ingest_brevo_email_campaigns(
    *,
    client_id: str,
    client_display_name: str,
    api_key: str,
    period_start: date,
    period_end: date,
    base_url: str = "https://api.brevo.com/v3",
    limit: int = 50,
) -> EmailDataset:
    """
    MVP approach:
    - list campaigns WITH globalStats in the listing response (reduces API calls)
    - classify campaign type: classic→broadcast, trigger→sequence

    Filtering by period uses Brevo list API startDate/endDate where supported.
    """
    cfg = BrevoConfig(api_key=api_key, base_url=base_url)
    c = BrevoClient(cfg)
    warnings: list[str] = []
    rows: list[EmailCampaignRow] = []
    try:
        start_utc = f"{period_start.isoformat()}T00:00:00.000Z"
        end_utc = f"{period_end.isoformat()}T23:59:59.999Z"
        for camp in c.list_email_campaigns(limit=limit, start_date_utc=start_utc, end_date_utc=end_utc, statistics="globalStats"):
            cid = camp.get("id")
            if cid is None:
                continue
            sent_at = _parse_dt(camp.get("sentDate") or camp.get("scheduledAt"))
            # stats may be nested under `statistics.globalStats` in list response
            gs = (camp.get("statistics") or {}).get("globalStats") or camp.get("globalStats") or {}

            # Brevo fields (per docs): sent, delivered, uniqueViews, uniqueClicks, hardBounces, softBounces,
            # unsubscriptions, complaints, etc.
            sent = gs.get("sent")
            delivered = gs.get("delivered")
            opens_unique = gs.get("uniqueViews") or gs.get("uniqueOpens") or gs.get("viewed")
            clicks_unique = gs.get("uniqueClicks")
            hard_bounces = gs.get("hardBounces")
            soft_bounces = gs.get("softBounces")
            unsub = gs.get("unsubscriptions")
            complaints = gs.get("complaints")

            typ = camp.get("type")
            if typ == "classic":
                camp_type = "broadcast"
            elif typ == "trigger":
                camp_type = "sequence"
            else:
                camp_type = "unknown"

            rows.append(
                EmailCampaignRow(
                    campaign_id=str(cid),
                    campaign_name=str(camp.get("name") or f"Campaign {cid}"),
                    campaign_type=camp_type,
                    sent_at=sent_at,
                    report_period_start=period_start,
                    report_period_end=period_end,
                    sent=int(sent) if sent is not None else None,
                    delivered=int(delivered) if delivered is not None else None,
                    opens_unique=int(opens_unique) if opens_unique is not None else None,
                    clicks_unique=int(clicks_unique) if clicks_unique is not None else None,
                    hard_bounces=int(hard_bounces) if hard_bounces is not None else None,
                    soft_bounces=int(soft_bounces) if soft_bounces is not None else None,
                    unsubscribes=int(unsub) if unsub is not None else None,
                    spam_complaints=int(complaints) if complaints is not None else None,
                    source="brevo_api",
                )
            )
    finally:
        c.close()

    if not rows:
        warnings.append("No Brevo campaigns found in the specified period.")

    return EmailDataset(
        client_id=client_id,
        client_display_name=client_display_name,
        report_period_start=period_start,
        report_period_end=period_end,
        rows=rows,
        source="brevo_api",
        warnings=warnings,
        raw_path=None,
    )

