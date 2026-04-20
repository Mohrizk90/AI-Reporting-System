# Scope statement — internal use

**Product:** Pedicel **Paid Ads reporting automation MVP** for **Meta Ads Manager campaign exports** (Excel/CSV).

**In scope**

- Ingest campaign-level files matching the agreed schema (`mvp/ingest.py`).
- KPI aggregation and campaign breakdown aligned to **`Files/Ads_Report_Template.docx.pdf`** (sections 1, 2, 4, 5 for Meta; §3 Google explicitly excluded).
- Deterministic **§1 executive summary** plus optional **LLM copy for §5.1 / §5.3** (Meta only).
- Outputs: JSON, TXT, MD, HTML.

**Out of scope (frozen for this MVP)**

- Google Ads, Google Search Console / SEO, organic Instagram/LinkedIn/TikTok, email ESP data.
- Template **§2.2** creative metrics (requires ad/asset-level sources).
- Revenue, purchases, or blended ROAS unless added to the data pipeline later.

**Positioning line (stakeholders):**  
*This MVP automates the Meta-paid slice of the Pedicel Paid Ads report from campaign exports; Google and other channels are intentionally not implemented yet.*

**Monthly report roadmap:** Target integrations (Meta Marketing API, Google Ads, Search Console, LinkedIn, Brevo, file fallback, etc.) are declared on every report as **`monthly_report_data_sources`** — see `mvp/monthly_report_sources.py` and `SOURCE_OF_TRUTH.md` §5.1.
