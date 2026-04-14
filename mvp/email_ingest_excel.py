"""
Email export ingestion from Excel/CSV (MVP).

This expects email-campaign metrics such as:
- sent / delivered / opens / clicks / bounces / unsubscribes / complaints

If the input file is actually a Meta Ads export (as `Files/YOA Campaigns-1-Sep-2025-31-Mar-2026.xlsx` is),
this ingester will raise a clear error so we don't silently misreport.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from mvp.email_schema import EmailCampaignRow, EmailDataset


EMAIL_REQUIRED_ANY = {"sent", "delivered", "opens", "open", "click", "clicks"}
META_SIGNATURE = {"impressions", "reach", "result indicator", "amount spent"}


def ingest_email_excel_export(
    *,
    path: str | Path,
    client_id: str,
    client_display_name: str,
    period_start: date,
    period_end: date,
    sheet_name: str | int | None = 0,
) -> EmailDataset:
    path = Path(path)
    df = pd.read_excel(path, sheet_name=sheet_name or 0)
    cols = [str(c).strip().lower() for c in df.columns]

    # Guardrail: detect Meta export
    if any(sig in " ".join(cols) for sig in META_SIGNATURE):
        raise ValueError(
            "This Excel file looks like a Meta Ads campaign export (Impressions/Reach/Result indicator). "
            "Please provide an email/ESP export (Brevo) containing sent/delivered/opens/clicks/bounces/unsubs."
        )

    # Minimal heuristic mapping (extend once we see the real export)
    def find(*names: str) -> str | None:
        for n in names:
            if n in cols:
                return df.columns[cols.index(n)]
        return None

    col_name = find("campaign name", "name", "subject", "campaign")
    col_sent = find("sent", "emails sent")
    col_del = find("delivered", "deliveries")
    col_open = find("opens", "unique opens", "open")
    col_click = find("clicks", "unique clicks", "click")
    col_unsub = find("unsubscribes", "unsubs", "unsubscribe")

    if not col_name or not any(c is not None for c in (col_sent, col_del, col_open, col_click)):
        raise ValueError(
            "Could not detect required email columns. Expected campaign name and at least sent/delivered/opens/clicks."
        )

    rows: list[EmailCampaignRow] = []
    for i, r in enumerate(df.to_dict(orient="records"), start=2):
        name = str(r.get(col_name) or "").strip()
        if not name:
            continue
        rows.append(
            EmailCampaignRow(
                campaign_id=None,
                campaign_name=name,
                campaign_type="broadcast",
                sent_at=None,
                report_period_start=period_start,
                report_period_end=period_end,
                sent=int(r[col_sent]) if col_sent and pd.notna(r.get(col_sent)) else None,
                delivered=int(r[col_del]) if col_del and pd.notna(r.get(col_del)) else None,
                opens_unique=int(r[col_open]) if col_open and pd.notna(r.get(col_open)) else None,
                clicks_unique=int(r[col_click]) if col_click and pd.notna(r.get(col_click)) else None,
                hard_bounces=None,
                soft_bounces=None,
                unsubscribes=int(r[col_unsub]) if col_unsub and pd.notna(r.get(col_unsub)) else None,
                spam_complaints=None,
                source="excel",
                source_row_index=i,
            )
        )

    if not rows:
        raise ValueError("No campaign rows found in the provided email export.")

    return EmailDataset(
        client_id=client_id,
        client_display_name=client_display_name,
        report_period_start=period_start,
        report_period_end=period_end,
        rows=rows,
        source="excel",
        warnings=[],
        raw_path=str(path.resolve()),
    )

