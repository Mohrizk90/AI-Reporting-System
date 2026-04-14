"""LLM layer: structured summary, insights, recommendations."""

from __future__ import annotations

import json
import os
from typing import Any

from mvp.kpis import AggregateKPIs
from mvp.schema import NormalizedDataset

# Prompt template — maps to Paid Ads template §5.1 (Facebook) + §5.3 (actions); Meta data only.
SYSTEM_PROMPT = """You write section "5.1 Facebook Ads Summary" (and bullets) for a Pedicel Paid Ads Performance Report. The JSON includes an "executive_summary" string for §1—do not repeat it verbatim; add qualitative commentary on Meta performance only.

Input is Meta Ads Manager campaign export aggregates ONLY.

Rules:
- Do NOT discuss Google Ads, SEO, email, or organic social (no data provided).
- Do not invent revenue, ROAS, or purchase value.
- If multiple optimization events exist, reinforce comparing like-for-like.

Respond ONLY with valid JSON:
{
  "summary": "2–4 sentences: Meta wins, risks, and next steps; reference period if given",
  "insights": ["bullet 1", "bullet 2"],
  "recommendations": ["action 1", "action 2", "action 3"],
  "caveats": ["optional data limitations"]
}"""


def build_user_prompt(ds: NormalizedDataset, kpis: AggregateKPIs) -> str:
    from mvp.paid_ads_template import build_executive_summary_paragraph

    exec_sum = build_executive_summary_paragraph(ds, kpis)
    payload = {
        "client": ds.client_display_name,
        "currency": ds.currency,
        "executive_summary_section_1": exec_sum,
        "period": {
            "start": ds.rows[0].reporting_starts.isoformat() if ds.rows else None,
            "end": ds.rows[0].reporting_ends.isoformat() if ds.rows else None,
        },
        "aggregates": kpis.to_dict(),
        "warnings": ds.warnings + kpis.notes,
        "campaign_names": [r.campaign_name for r in ds.rows[:20]],
    }
    return (
        "Produce copy for §5.1 Facebook Ads Summary and §5.3-style recommended actions. "
        "Meta-only; no other channels. Expand on §1 executive summary, do not duplicate it.\n\n"
        + json.dumps(payload, indent=2)
    )


def generate_ai_insights(
    ds: NormalizedDataset,
    kpis: AggregateKPIs,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Call OpenAI Chat Completions. If OPENAI_API_KEY is missing, return stub content.
    """
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    api_key = os.environ.get("OPENAI_API_KEY")

    user_content = build_user_prompt(ds, kpis)

    if not api_key:
        return {
            "summary": (
                f"[Stub — §5.1] See §1 executive summary for the period snapshot. "
                f"{ds.client_display_name}: {kpis.total_spend:,.2f} {ds.currency} spend / "
                f"{int(kpis.total_impressions):,} impressions in export. Set OPENAI_API_KEY for LLM narrative."
            ),
            "insights": [
                f"Portfolio CPM (from export): {kpis.cpm} {ds.currency}.",
                f"Optimization events present: {', '.join(kpis.unique_result_indicators) or 'n/a'}.",
            ],
            "recommendations": [
                "Align each campaign on a single primary optimization event when comparing results.",
                "If frequency exceeds 3.5 on scaling campaigns, refresh creatives or broaden audiences.",
                "Set OPENAI_API_KEY to generate final §5.1 and §5.3 narrative.",
            ],
            "caveats": ["LLM disabled: no API key."],
            "source": "stub",
            "raw_model": None,
        }

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.4,
        )
        text = resp.choices[0].message.content or "{}"
        data = json.loads(text)
        data["source"] = "openai"
        data["raw_model"] = model
        return data
    except Exception as e:
        return {
            "summary": "AI generation failed; see caveats.",
            "insights": [],
            "recommendations": ["Fix OpenAI configuration and re-run."],
            "caveats": [str(e)],
            "source": "error",
            "raw_model": model,
        }


def normalize_ai_block(raw: dict[str, Any]) -> dict[str, Any]:
    """Ensure keys expected by report_model."""
    return {
        "summary": raw.get("summary"),
        "insights": raw.get("insights") or [],
        "recommendations": raw.get("recommendations") or [],
        "caveats": raw.get("caveats") or [],
        "source": raw.get("source", "unknown"),
        "raw_model": raw.get("raw_model"),
    }
