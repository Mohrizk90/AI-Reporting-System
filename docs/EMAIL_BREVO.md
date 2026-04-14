# Email reporting (Brevo) — MVP

## Summary

This module generates a **template-aligned Email Marketing Performance Report** from **Brevo** campaign statistics:

- Template: `Files/Email_Report_Template.docx.pdf`
- Source: Brevo API v3 `emailCampaigns` + per-campaign `globalStats`
- Output: `report.json`, `report.txt`, `report.md`, `report.html`

**Important:** `Files/YOA Campaigns-1-Sep-2025-31-Mar-2026.xlsx` is a **Meta Ads export**, not an email export.
Email Excel ingestion is intentionally a placeholder until a real ESP email export is provided.

## Setup

1. Copy `.env.example` → `.env`
2. Set:
   - `BREVO_API_KEY=...`
   - optional `OPENAI_API_KEY=...` (for §9 narrative)

### Important: MCP/base64 wrapper vs raw key

If you have a base64 string like `eyJ...==` (often labeled “MCP API”), **do not** paste that into `BREVO_API_KEY`.
It’s a wrapper (base64-encoded JSON) containing the real key in a field like `"api_key"`.

`BREVO_API_KEY` must contain the raw Brevo key only (typically starting with `xkeysib-...`).

### Security note

If you pasted a key in chat or into any shared doc, assume it was exposed and **rotate it** after testing.

## Run (Brevo)

```powershell
python scripts/run_pipeline.py `
  --channel email --source brevo `
  --client-id yoa --client-name "YOA" `
  --period-start 2026-03-01 --period-end 2026-03-31 --no-ai
```

Outputs land in `output/<client_id>/email/` by default.

## Brevo endpoints used (why)

- **List campaigns:** `GET /v3/emailCampaigns` — to discover campaign IDs.
- **Campaign report:** `GET /v3/emailCampaigns/{campaignId}?statistics=globalStats` — provides the core metrics needed for template §3 and campaign breakdowns.

These endpoints are the best fit because they expose **sent/delivered/opens/clicks/bounces/unsubs/complaints** at campaign level.

## Template coverage (supported vs not)

### Supported now (Brevo `globalStats`)

- **Template topline:** Emails sent, open rate, CTR, unsubscribe rate (computed from delivered/sent/open/click/unsub fields)
- **§3 Core Email KPIs:** Delivered, Opens, Clicks, Delivery rate, Open rate, CTR, CTOR, Unsubscribe rate, Bounce rate, Complaint rate
- **§4.1 Campaign Breakdown (Broadcast / Newsletter):** top campaigns by delivered volume (MVP view)
- **§8 Key Benchmarks:** reference table
- **§9 Insights & Recommendations:** AI-generated or deterministic fallback

### Not included in current source (explicitly labeled)

- **§2 List Health & Subscriber Metrics:** requires list/subscriber endpoints or an export of subscriber counts
- **§4.2 Automated sequences (flows):** only partially covered unless the source identifies flow metrics distinctly
- **§5 Cold outreach performance:** requires reply/meeting data (not in Brevo campaign stats)
- **Revenue / conversion attribution:** requires commerce/CRM linkage

## Notes for future unified 360 report

The normalized structures (`mvp/email_schema.py`) are designed so Email can later feed a cross-channel 360 report via:

- channel = `email`
- period
- headline KPIs
- findings/recommendations/caveats

