"""LLM insights for Email reporting (Brevo/ESP exports)."""

from __future__ import annotations

import json
import os
from typing import Any

from mvp.email_kpis import EmailAggregateKPIs
from mvp.email_schema import EmailDataset


SYSTEM_PROMPT = """You are a senior email marketing strategist writing client-facing reporting insights.
Input is JSON for email campaign performance only.

Rules:
- Do NOT invent revenue unless explicitly present.
- Do not overclaim causality.
- If data is missing (list health, sequences, cold outreach), state 'not available' briefly.

Respond ONLY with valid JSON:
{
  "summary": "2–4 sentences executive summary",
  "insights": ["bullet 1", "bullet 2"],
  "recommendations": ["action 1", "action 2", "action 3"],
  "caveats": ["optional limitations"]
}
"""


def build_user_prompt(ds: EmailDataset, kpis: EmailAggregateKPIs) -> str:
    payload = {
        "client": ds.client_display_name,
        "period": {"start": ds.report_period_start.isoformat(), "end": ds.report_period_end.isoformat()},
        "source": ds.source,
        "aggregate_kpis": kpis.to_dict(),
        "warnings": ds.warnings,
        "sample_campaigns": [r.campaign_name for r in ds.rows[:10]],
    }
    return "Write §9 insights for this email report. Return JSON only.\n\n" + json.dumps(payload, indent=2)


def generate_email_ai_insights(ds: EmailDataset, kpis: EmailAggregateKPIs) -> dict[str, Any]:
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {
            "summary": "AI disabled (no OPENAI_API_KEY). Review the KPI table and top campaigns, then add narrative in §9.",
            "insights": [],
            "recommendations": [
                "Improve subject lines for campaigns below target open rate.",
                "Strengthen CTAs/content for campaigns below CTR benchmarks.",
                "Monitor unsubscribe and complaint rates; adjust frequency if elevated.",
            ],
            "caveats": ["LLM not invoked (no API key)."],
            "source": "stub",
        }

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(ds, kpis)},
        ],
        temperature=0.4,
    )
    text = resp.choices[0].message.content or "{}"
    data = json.loads(text)
    data["source"] = "openai"
    data["raw_model"] = model
    return data

