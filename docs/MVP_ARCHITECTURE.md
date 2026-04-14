# MVP — Architecture & operations reference

Single-page reference for the reporting pipeline: modules, prompts, examples, CLI, and n8n.

---

## 1. Architecture overview

A small Python package **`mvp/`** runs the flow:

**Excel/CSV (Meta export) → unified rows → KPIs → report JSON → text / Markdown / HTML**, with optional **OpenAI** for **§5.1 Facebook Ads Summary** and **§5.3 Recommended Actions** (aligned to `Files/Ads_Report_Template.docx.pdf`).

**Multi-client** is handled by `--client-id` / `--client-name` (and optional `clients/*.json` for reference).

| Step | Location |
|------|----------|
| Schema | `mvp/schema.py` — `SCHEMA`, `CampaignRow`, `NormalizedDataset` |
| Ingest & clean | `mvp/ingest.py` — `normalize_meta_export()` |
| KPIs | `mvp/kpis.py` — CPM, frequency, link CTR/CPC, aggregates |
| Paid Ads template body | `mvp/paid_ads_template.py` — sections 1–5 mirroring Pedicel Ads PDF |
| Report assembly | `mvp/report_model.py` — `paid_ads_report` + explicit `scope` (supported vs not implemented) |
| AI | `mvp/ai_insights.py` — Meta-only prompts for §5.1 / §5.3 |
| Outputs | `mvp/formatters.py` — JSON, TXT, MD, HTML (Jinja) |
| CLI | `scripts/run_pipeline.py` |
| Docs | `README.md` |

**Layout:** `data/raw/`, `clients/`, `mvp/`, `output/<client_id>/`, `scripts/`, `templates/`.

---

## 2. Code implementation

| Module | Responsibility |
|--------|------------------|
| `mvp/schema.py` | Canonical fields and `example_normalized_rows()`. |
| `mvp/ingest.py` | Loads `.xlsx` / `.csv`, maps columns (including `Amount spent (CUR)` → currency), normalizes Impressions / Reach / Ends / Attribution setting. |
| `mvp/kpis.py` | Modular metrics; CTR/CPC for `actions:link_click` rows; `conversion_rate_pct()` helper when conversions + clicks exist later; SEO helpers stubbed for future GSC. |
| `mvp/report_model.py` | `executive_summary`, `channel_performance` (Meta + SEO + social organic placeholders), `key_metrics_table`, `insights`. |
| `mvp/ai_insights.py` | OpenAI JSON mode; stub if `OPENAI_API_KEY` is missing. |
| `mvp/pipeline.py` | `run_pipeline()`. |

---

## 3. AI prompt (exact)

**System** (`mvp/ai_insights.py`):

```text
You are a senior performance marketer. You receive JSON with Meta Ads campaign aggregates and per-campaign facts. Respond ONLY with valid JSON matching this shape:
{
  "summary": "2-4 sentences executive summary",
  "insights": ["bullet 1", "bullet 2"],
  "recommendations": ["action 1", "action 2", "action 3"],
  "caveats": ["optional data limitations"]
}
Do not invent revenue or ROAS. If data is thin, say so in caveats.
```

**User message:** JSON built by `build_user_prompt()` — client, currency, period, `kpis.to_dict()`, warnings, campaign names.

---

## 4. Example input & output

- **Input:** `Files/ISN-Medical-Ad_euro-Campaigns-Mar-11-2026-Apr-9-2026.csv` (and YOA `.xlsx`).
- **Output:** `output/isn/report.json`, `report.txt`, `report.md`, `report.html` (after a successful run).

**Sample headline (from a real run):**

`ISN Medical: 2 campaigns, 33.65 EUR spend, 297,644 impressions in period.`

---

## 5. How to run

```powershell
cd "d:\Code_Space\Pedicel_WorkSpace\AI Reporting System"
python -m pip install -r requirements.txt
copy .env.example .env
# set OPENAI_API_KEY in .env for real LLM output

python scripts/run_pipeline.py "Files\ISN-Medical-Ad_euro-Campaigns-Mar-11-2026-Apr-9-2026.csv" --client-id isn --client-name "ISN Medical"
```

- **`--no-ai`** — skip the API call (stub or “skipped” text).
- **`--json-only`** — print the final report JSON to stdout.

---

## 6. n8n integration plan

1. **Trigger:** Cron or Webhook (e.g. file dropped in storage).
2. **Save file** to `data/raw/<name>.xlsx` or `.csv`.
3. **Execute Command:**  
   `python scripts/run_pipeline.py "data/raw/..." --client-id yoa --client-name "YOA Insurance"`  
   (working directory = repo root; pass env with `OPENAI_API_KEY`).
4. **Read file** `output/yoa/report.json` or attach `report.html`.
5. **Email / Slack:** map `insights.summary` and recommendations, or send HTML.

**Alternative:** run with **`--no-ai`** and let an **n8n OpenAI** node consume the KPI JSON.

---

## Notes

- **Output shape:** JSON `schema_version` **1.2**+ includes **`paid_ads_report`** — same section numbering and titles as `Ads_Report_Template.docx.pdf` (overview + executive summary → Facebook/Meta → Google excluded → benchmarks reference → insights).
- **Truth in labeling:** `scope.supported_now` lists only **Meta campaign export** ingestion. `scope.not_implemented` lists Google Ads, SEO, organic social, email, and **§2.2** creative metrics until the corresponding files/APIs exist.
- Conversion rate and SEO are not populated from Meta-only exports; extend ingest when you add sources.
- See also `SOURCE_OF_TRUTH.md` for evidence-based scope from client files.
