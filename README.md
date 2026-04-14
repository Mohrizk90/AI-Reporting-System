# AI Marketing Reporting — MVP

This repo currently supports two template-aligned MVP modules:

- **Paid Ads (Meta campaign exports)** aligned to `Files/Ads_Report_Template.docx.pdf`
- **Email (Brevo API)** aligned to `Files/Email_Report_Template.docx.pdf`

Both generate JSON / TXT / MD / HTML, with optional OpenAI narrative sections.

**Positioning:** *Pedicel Paid Ads reporting automation MVP — Meta campaign exports only.* (See [docs/SCOPE_STATEMENT.md](docs/SCOPE_STATEMENT.md).)

| Doc | Purpose |
|-----|---------|
| [docs/MVP_ARCHITECTURE.md](docs/MVP_ARCHITECTURE.md) | Architecture, prompts, n8n |
| [docs/DEMO_CHECKLIST.md](docs/DEMO_CHECKLIST.md) | How to run, outputs, demo flow |
| [docs/KPI_LOGIC.md](docs/KPI_LOGIC.md) | Validated formulas for Meta KPIs |
| [docs/SCOPE_STATEMENT.md](docs/SCOPE_STATEMENT.md) | Internal scope line for stakeholders |
| [docs/EMAIL_BREVO.md](docs/EMAIL_BREVO.md) | Email module (Brevo) + template coverage |

## 1. Architecture overview

| Layer | Module | Role |
|-------|--------|------|
| Schema | `mvp/schema.py` | `CampaignRow`, `NormalizedDataset`, `SCHEMA` dict |
| Ingestion | `mvp/ingest.py` | Load `.xlsx` / `.csv`, map columns, detect currency from `Amount spent (XXX)` |
| KPIs | `mvp/kpis.py` | CPM, frequency, CTR/CPC for `actions:link_click` rows, aggregates |
| Template body | `mvp/paid_ads_template.py` | Sections 1–5 like the Ads PDF; §3 Google excluded; §2.2 creative N/A without ad-level data |
| Report model | `mvp/report_model.py` | `paid_ads_report` + `scope` (what is / is not implemented) |
| AI | `mvp/ai_insights.py` | Meta-only copy for template §5.1 / §5.3; stub if no key |
| Output | `mvp/formatters.py` | `.json`, `.txt`, `.md`, `.html` (Jinja) |
| Orchestration | `mvp/pipeline.py` | Single `run_pipeline()` |

**Folder layout**

```
data/raw/          # drop client exports (optional)
clients/           # client_id + display_name JSON
Files/             # original samples (CSV/XLSX)
mvp/               # Python package
output/<client_id>/ # generated reports
scripts/run_pipeline.py
templates/report.html.j2
```

## 2. How to run

```powershell
cd "d:\Code_Space\Pedicel_WorkSpace\AI Reporting System"
python -m pip install -r requirements.txt
copy .env.example .env
# Edit .env: OPENAI_API_KEY=sk-...
```

**Example (ISN CSV, no AI):**

```powershell
python scripts/run_pipeline.py "Files\ISN-Medical-Ad_euro-Campaigns-Mar-11-2026-Apr-9-2026.csv" `
  --channel paid_ads --input "Files\ISN-Medical-Ad_euro-Campaigns-Mar-11-2026-Apr-9-2026.csv" `
  --client-id isn --client-name "ISN Medical" --no-ai
```

**Email (Brevo API, MVP):**

```powershell
python scripts/run_pipeline.py `
  --channel email --source brevo `
  --client-id yoa --client-name "YOA" `
  --period-start 2026-03-01 --period-end 2026-03-31
```

Set `BREVO_API_KEY` in `.env` (see `.env.example`). Do not commit secrets.

**Important:** The file `Files/YOA Campaigns-1-Sep-2025-31-Mar-2026.xlsx` is a Meta Ads export, not an email export.

**With AI:** omit `--no-ai` and set `OPENAI_API_KEY`.

**Print JSON to stdout:**

```powershell
python scripts/run_pipeline.py "Files\..." --client-id yoa --client-name "YOA Insurance" --json-only
```

Outputs: `output/<client_id>/report.json`, `report.txt`, `report.md`, `report.html`.

## 3. Unified input schema

Defined in `mvp/schema.py` as `SCHEMA` and `CampaignRow`. Currency is inferred from the spend column name.

**Normalized row (example):**

```json
{
  "reporting_starts": "2026-03-11",
  "reporting_ends": "2026-04-09",
  "campaign_name": "ISNxChowdeck ad Campaign",
  "campaign_delivery": "inactive",
  "results": 3904.0,
  "result_indicator": "actions:link_click",
  "cost_per_result": 0.00779201,
  "amount_spent": 30.42,
  "currency": "EUR",
  "impressions": 279002,
  "reach": 175691,
  "campaign_ends": "2026-05-01",
  "attribution_setting": "7-day click or 1-day view"
}
```

## 4. KPI notes

- **CTR / CPC (link):** computed on rows where `result_indicator == actions:link_click` (subset may be one row).
- **CPM / frequency:** portfolio-level from summed spend, impressions, reach.
- **Conversion rate / SEO:** helpers exist in `kpis.py`; GSC and conversion columns are **not** in the Meta file — SEO block is `no_data` until you add another ingest path.

## 5. AI prompt (exact system prompt)

See `mvp/ai_insights.py` — `SYSTEM_PROMPT` and `build_user_prompt()` (user message = JSON aggregates + campaign names + warnings).

Model default: `gpt-4o-mini` (override with `OPENAI_MODEL` in `.env`).

## 6. n8n integration (light)

1. **Trigger:** Schedule (cron) or Webhook (file uploaded to Drive/Dropbox) or Manual.
2. **Move file** to a path the runner can read, or pass URL and a small step to download to `data/raw/`.
3. **Execute Command** node:  
   `python scripts/run_pipeline.py "data/raw/latest.xlsx" --client-id yoa --client-name "YOA Insurance"`  
   (set working directory to repo root; inject env vars for `OPENAI_API_KEY`).
4. **Read Binary / Read File** on `output/yoa/report.json` or attach `report.html`.
5. **Send Email** node: body from `.txt` or `.html`, or Slack with summary field from JSON `insights.summary`.
6. Optional: **OpenAI** node in n8n instead of in-app AI — then use `--no-ai` and pass KPI JSON to n8n’s LLM step.

## 7. Extending later

- Add `ingest_gsc.py` and merge into `channel_performance.seo`.
- Map more `result_indicator` values to named KPI blocks.
- Replace Jinja HTML with PDF (Playwright/WeasyPrint).

## 8. License / ops

Internal MVP; store `.env` only locally (see `.gitignore`).
