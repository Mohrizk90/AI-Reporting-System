# KPI logic — Meta campaign export (MVP)

Source columns: Meta Ads Manager **campaign** export (`mvp/ingest.py`). All portfolio metrics sum **campaign rows** in the file.

| Output | Formula / rule | Label in report |
|--------|----------------|-----------------|
| **Spend** | Sum of `Amount spent (CUR)` | Total ad spend (Meta); per-campaign spend |
| **Impressions** | Sum of `Impressions` | Impressions |
| **Reach** | Sum of `Reach` | Reach |
| **Frequency** | Total impressions ÷ total reach | Portfolio average (Meta definition at campaign aggregate level) |
| **CPM** | Total spend ÷ total impressions × 1000 | Cost per 1,000 impressions |
| **CTR (link)** | Sum of results where `result_indicator == actions:link_click` → **link_click_results**; CTR = link_click_results ÷ **sum of impressions on those rows** × 100 | Shown as **link-click rows only**; not blended with other objectives |
| **CPC (link)** | Sum of spend on link-click rows ÷ link_click_results | Link-click rows only |
| **Total results** | Sum of platform `Results` column | “Meta optimization events” — **not** one conversion type if indicators differ |
| **CPL/CPA (portfolio)** | Total spend ÷ total results | Interpret with caution when events are mixed; note in §2.1 |
| **ROAS / conversion rate / lead CVR** | *Not computed* — no revenue or funnel fields in export | “Not available in current export” |

**Not inferred:** revenue, Google metrics, organic social, SEO, ad-level creative metrics (§2.2).
