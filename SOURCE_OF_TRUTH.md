# AI Client Reporting — Analysis Source of Truth

**Purpose:** Single reference for what was discovered in the project `Files` folder, agreed MVP boundaries, and implementation contracts. Update this file when inputs, scope, or schema change.

**Last updated:** 2026-04-11  
**Analyzed path:** `Files/` (contents as of analysis date)

---

## 1. Scope of evidence

This document is **evidence-based** from files present under `Files/`. Items marked **Assumption** are not proven by those files.

**Contained in `Files/`:**

| File | Type |
|------|------|
| `Ads_Report_Template.docx.pdf` | PDF template |
| `Email_Report_Template.docx.pdf` | PDF template |
| `Instagram_Report_Template.docx.pdf` | PDF template |
| `LinkedIn_Report_Template.docx.pdf` | PDF template |
| `SEO_Report_Template.docx.pdf` | PDF template |
| `TikTok_Report_Template.docx.pdf` | PDF template |
| `YOA Campaigns-1-Sep-2025-31-Mar-2026.xlsx` | Excel data export |
| `ISN-Medical-Ad_euro-Campaigns-Mar-11-2026-Apr-9-2026.csv` | CSV data export |

**Not found in folder:** standalone Word/Excel source templates, written briefs, sample *filled* client reports, non-Meta channel raw data, branding packs, API credentials, approval workflow docs.

---

## 2. File inventory

| File name | Type | Purpose | Client (if any) | Category |
|-----------|------|---------|-----------------|----------|
| `Ads_Report_Template.docx.pdf` | PDF | Paid ads (Meta + Google) report structure, `{{placeholders}}` | Agency (Pedicel Marketing) | Template |
| `Email_Report_Template.docx.pdf` | PDF | Email/ESP performance | Agency | Template |
| `Instagram_Report_Template.docx.pdf` | PDF | Instagram organic + paid | Agency | Template |
| `LinkedIn_Report_Template.docx.pdf` | PDF | LinkedIn organic + paid | Agency | Template |
| `SEO_Report_Template.docx.pdf` | PDF | SEO / Google Search Console | Agency | Template |
| `TikTok_Report_Template.docx.pdf` | PDF | TikTok organic + paid | Agency | Template |
| `YOA Campaigns-1-Sep-2025-31-Mar-2026.xlsx` | `.xlsx` | Meta-style campaign export | **YOA Insurance** (URLs/names) | Raw input data |
| `ISN-Medical-Ad_euro-Campaigns-Mar-11-2026-Apr-9-2026.csv` | `.csv` | Meta-style campaign export | **ISN / ISN Medical** (filename + campaigns) | Raw input data |

---

## 3. Tabular data specification (Meta exports)

Both YOA (Excel) and ISN (CSV) share the **same logical schema** (column names align; currency differs in the spend column).

### 3.1 YOA Excel

- **Sheet:** `Worksheet` only.
- **Shape (sample):** 14 rows × 14 columns including header → **13 campaign rows**.
- **Reporting window (file sample):** `2025-09-01`–`2026-03-31` (repeated per row).
- **Currency:** NGN — column `Amount spent (NGN)`.

### 3.2 ISN CSV

- **Rows:** 2 data rows + header (sample).
- **Reporting window (file sample):** `2026-03-11`–`2026-04-09`.
- **Currency:** EUR — column `Amount spent (EUR)`.

### 3.3 Shared columns (canonical names for ingestion)

| Source column | Role |
|---------------|------|
| Reporting starts / ends | Export reporting period |
| Campaign name | Dimension |
| Campaign delivery | Status (e.g. inactive, completed) |
| Results | Metric (count) |
| Result indicator | Action/optimization event type (e.g. `actions:link_click`) |
| Cost per results | Metric |
| Ad set budget / Ad set budget type | Context |
| Amount spent (CUR) | Spend metric; **CUR** varies (NGN, EUR, …) |
| Impressions | Metric |
| Reach | Metric |
| Ends | Campaign end date |
| Attribution setting | e.g. 7-day click or 1-day view |

**Classification:** Raw platform **campaign-level** export — not a finished narrative report, not blended cross-channel.

**Important:** `Result indicator` can differ across rows (clicks, profile visits, video metrics, likes, etc.). Summing `Results` across types is **not** a single “conversion” definition without business rules.

---

## 4. Template pattern (all channel PDFs)

Reusable structure:

1. Title, `{{date_range}}`, “Prepared by: Pedicel Marketing”
2. Overview / headline KPIs
3. Educational KPI tables (definitions + benchmarks)
4. Breakdown tables (campaigns, posts, keywords, …)
5. Key benchmarks
6. Insights & recommendations — often **`{{AI-generated or manually written}}`** plus numbered actions

**Channels covered by templates:** Paid Ads (Meta + Google), Email, Instagram, LinkedIn, SEO (GSC), TikTok.

**Facts from templates:** Narrative sections explicitly allow AI or manual copy.

---

## 5. MVP definition (locked for v1)

**In scope**

- Ingest Meta campaign files (CSV/XLSX) matching §3.
- Normalize currency and column aliases (`Amount spent (XXX)`).
- Aggregate: spend, impressions, reach, results, cost per result; breakdown by campaign and by `result_indicator` where useful.
- Render **Ads report — Facebook/Meta sections** (and overlapping “Instagram paid” KPI themes if product chooses one artifact).
- **LLM:** narrative summary + recommended actions + caveats when mixing result types.
- Output: structured JSON (see §8) + HTML and/or PDF.

**Out of scope for v1 (unless new inputs appear)**

- Google Ads, GSC, email ESP, LinkedIn, TikTok native data.
- Live API connectors.
- Full multi-channel dashboard.
- **ROAS / revenue** — not present in provided Meta exports; template fields that require revenue stay empty or “N/A” with disclaimer.

---

## 6. Architecture (v1)

| Layer | Responsibility |
|-------|----------------|
| **Ingestion** | Accept CSV/XLSX; validate schema; store raw immutably; optional checksum |
| **Normalization** | Map to canonical columns; attach `currency` from column name or config |
| **Metrics** | Aggregations, per-campaign tables, flags (e.g. mixed result types) |
| **AI narrative** | Structured prompts; JSON output for summary + actions |
| **Rendering** | Template (HTML → PDF optional); static benchmark text from product copy |

**Rule-based:** sums, ratios from existing columns, validation, static benchmark tables.

**AI:** summaries, recommendations, wording of caveats.

---

## 7. Repository layout (suggested)

```text
clients/
  yoa/config.yaml    # display name, default currency, timezone
  isn/config.yaml
ingest/raw/          # dated uploads, do not overwrite
processed/normalized/
reports/runs/<date>_<client>/
  meta.json
  report.html
  report.pdf
templates/           # Jinja/HTML or future docx
```

---

## 8. JSON pipeline output (contract)

**Current implementation:** The pipeline writes `schema_version` **1.1** with **`paid_ads_report`** (sections 1–5 aligned to `Ads_Report_Template.docx.pdf`), **`scope.supported_now`** / **`scope.not_implemented`**, plus flat **`insights`** for automation. Inspect `output/<client_id>/report.json` for the exact tree.

The sketch below is a simplified legacy view of aggregates + narrative; prefer `paid_ads_report` for UI mapping.

Top-level shape for automation and future dashboard consumption:

```json
{
  "meta": {
    "schema_version": "1.0",
    "generated_at": "ISO-8601",
    "client_id": "string",
    "client_name": "string",
    "source_files": [{ "path": "string", "sha256": "string" }],
    "reporting_period": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" },
    "currency": "NGN"
  },
  "ingestion": {
    "row_count": 0,
    "warnings": ["string"]
  },
  "aggregates": {
    "total_amount_spent": 0,
    "total_impressions": 0,
    "total_reach": 0,
    "by_result_indicator": [
      {
        "result_indicator": "string",
        "results": 0,
        "amount_spent": 0,
        "impressions": 0,
        "reach": 0
      }
    ]
  },
  "campaigns": [
    {
      "campaign_name": "string",
      "campaign_delivery": "string",
      "amount_spent": 0,
      "impressions": 0,
      "reach": 0,
      "results": 0,
      "result_indicator": "string",
      "cost_per_result": 0,
      "campaign_ends": "YYYY-MM-DD",
      "attribution_setting": "string"
    }
  ],
  "narrative": {
    "facebook_meta_summary": "string",
    "google_ads_summary": "string",
    "recommended_actions": [{ "priority": 1, "text": "string" }],
    "model": "string",
    "disclaimer": "string"
  }
}
```

**Note:** `google_ads_summary` may be empty in v1 with disclaimer until Google data exists.

---

## 9. Open questions (for client / team)

- Reporting cadence and delivery deadline per cycle.
- Per-client channel priority (360 vs Meta-first).
- Rules for reporting when `Result indicator` mixes incompatible actions.
- Revenue/conversion value for ROAS (if ever required).
- Exports or API access for Google, GSC, email, other networks.
- PDF branding per client; approval owner and process.
- ISN: reporting currency and stakeholder expectations (EUR vs other).

---

## 10. Risks and assumptions

**Risks**

- Expectation mismatch if stakeholders assume full 360 automation while only Meta files exist.
- Mixing result types without disclosure misleads readers.
- Automated PDF may not match original Word layout pixel-perfect.

**Assumptions (validate in product)**

- v1 ships Meta-only if no other exports are provided.
- “Total conversions” in Ads template is not populated from summed `Results` without explicit business sign-off.

---

## 11. Change log

| Date | Change |
|------|--------|
| 2026-04-11 | Initial documentation from folder analysis |
