"""Text, JSON, HTML/Markdown — aligned to Pedicel Paid Ads template layout."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _lines_monthly_report_data_sources_text(report: dict[str, Any]) -> list[str]:
    b = report.get("monthly_report_data_sources")
    if not b:
        return []
    out: list[str] = [
        "--- Monthly report: target data sources ---",
        "",
    ]
    for s in b.get("sources", []):
        out.append(f"  • {s.get('name', '')}: {s.get('purpose', '')}")
    fn = b.get("fallback_note")
    if fn:
        out.extend(["", f"  {fn}"])
    out.append("")
    return out


def _lines_monthly_report_data_sources_markdown(report: dict[str, Any]) -> list[str]:
    b = report.get("monthly_report_data_sources")
    if not b:
        return []
    lines: list[str] = ["## Monthly report — target data sources", ""]
    for s in b.get("sources", []):
        lines.append(f"- **{s.get('name', '')}:** {s.get('purpose', '')}")
    if b.get("fallback_note"):
        lines.extend(["", f"*{b['fallback_note']}*"])
    lines.append("")
    return lines


def _lines_gsc_seo_text(report: dict[str, Any]) -> list[str]:
    seo = report.get("seo_search_console")
    if not seo:
        return []
    out: list[str] = [
        "--- SEO (Google Search Console) ---",
        f"  Property: {seo.get('site_url')}",
        f"  Period: {seo.get('start_date')} to {seo.get('end_date')}",
    ]
    if seo.get("error"):
        out.append(f"  Error: {seo.get('error')}")
        out.append("")
        return out
    totals = seo.get("totals") or {}
    if totals:
        out.append(
            "  Totals: "
            f"clicks={totals.get('clicks')} "
            f"impressions={totals.get('impressions')} "
            f"ctr={totals.get('ctr')} "
            f"position={totals.get('position')}"
        )
    tq = seo.get("top_queries") or []
    if tq:
        out.append("  Top queries:")
        for r in tq[:10]:
            k = (r.get("keys") or ["—"])[0]
            out.append(
                f"    - {k} | clicks={r.get('clicks')} | impressions={r.get('impressions')} | "
                f"ctr={r.get('ctr')} | pos={r.get('position')}"
            )
    tp = seo.get("top_pages") or []
    if tp:
        out.append("  Top pages:")
        for r in tp[:10]:
            k = (r.get("keys") or ["—"])[0]
            out.append(
                f"    - {k} | clicks={r.get('clicks')} | impressions={r.get('impressions')} | "
                f"ctr={r.get('ctr')} | pos={r.get('position')}"
            )
    out.append("")
    return out


def _lines_gsc_seo_markdown(report: dict[str, Any]) -> list[str]:
    seo = report.get("seo_search_console")
    if not seo:
        return []
    lines: list[str] = [
        "## SEO — Google Search Console",
        "",
        f"- **Property:** `{seo.get('site_url')}`",
        f"- **Period:** {seo.get('start_date')} to {seo.get('end_date')}",
    ]
    if seo.get("error"):
        lines.extend(["", f"**Error:** {seo.get('error')}", ""])
        return lines
    totals = seo.get("totals") or {}
    if totals:
        lines.extend(
            [
                "",
                "### Totals",
                f"- **Clicks:** {totals.get('clicks')}",
                f"- **Impressions:** {totals.get('impressions')}",
                f"- **CTR:** {totals.get('ctr')}",
                f"- **Avg position (impression-weighted):** {totals.get('position')}",
            ]
        )
    tq = seo.get("top_queries") or []
    if tq:
        lines.extend(["", "### Top queries (sample)", ""])
        for r in tq[:10]:
            q = (r.get("keys") or ["—"])[0]
            lines.append(
                f"- **{q}** — clicks: {r.get('clicks')} · impressions: {r.get('impressions')} · "
                f"ctr: {r.get('ctr')} · pos: {r.get('position')}"
            )
    tp = seo.get("top_pages") or []
    if tp:
        lines.extend(["", "### Top pages (sample)", ""])
        for r in tp[:10]:
            p = (r.get("keys") or ["—"])[0]
            lines.append(
                f"- `{p}` — clicks: {r.get('clicks')} · impressions: {r.get('impressions')} · "
                f"ctr: {r.get('ctr')} · pos: {r.get('position')}"
            )
    lines.append("")
    return lines


def report_to_text(report: dict[str, Any]) -> str:
    mon = report.get("monthly_report")
    if mon:
        return _text_from_monthly_report(report, mon)
    pad = report.get("paid_ads_report")
    if pad:
        return _text_from_paid_ads_template(report, pad)
    em = report.get("email_report")
    if em:
        return _text_from_email_template(report, em)
    return _text_generic(report)


def _text_generic(report: dict[str, Any]) -> str:
    lines = [json.dumps(report, indent=2, ensure_ascii=False)]
    return "\n".join(lines)


def _text_from_email_template(report: dict[str, Any], em: dict[str, Any]) -> str:
    doc = em["document"]
    lines: list[str] = []
    lines.append(doc["report_title"])
    lines.append(doc["report_subtitle"])
    lines.append(doc["header_line"])
    lines.append("")
    lines.extend(_lines_monthly_report_data_sources_text(report))
    lines.extend(_lines_gsc_seo_text(report))

    # topline
    lines.append("Topline (template header table)")
    for r in em.get("section_0_topline_table", []):
        lines.append(f"  {r['label']}: {r['value']}")
    lines.append("")

    # sections in template order
    s1 = em["section_1_report_overview"]
    lines.append(s1["title"])
    lines.append(s1["body"])
    lines.append("")

    s2 = em["section_2_list_health"]
    lines.append(s2["title"])
    lines.append(f"  {s2['status_label']}. {s2['explanation']}")
    lines.append("")

    s3 = em["section_3_core_kpis"]
    lines.append(s3["title"])
    lines.append("  Metric | How calculated | Value | Benchmark")
    for r in s3["rows"]:
        lines.append(f"  {r['metric']} | {r['how_calculated']} | {r['value']} | {r['benchmark']}")
    lines.append("")

    s4 = em["section_4_campaign_breakdown"]
    lines.append(s4["title"])
    sub = s4["subsection_4_1_broadcast"]
    lines.append(sub["title"])
    for r in sub["rows"]:
        lines.append(
            f"  {r['campaign_name'][:70]} | sent={r.get('sent')} | open_rate={r.get('open_rate_pct')} | "
            f"ctr={r.get('ctr_pct')} | ctor={r.get('ctor_pct')} | unsubs={r.get('unsubs')}"
        )
    lines.append(s4.get("note", ""))
    lines.append("")

    s8 = em["section_8_key_benchmarks"]
    lines.append(s8["title"])
    for b in s8["reference"]:
        lines.append(f"  {b['metric']}: {b['target']} (watch: {b['watch']})")
    lines.append("")

    s9 = em["section_9_insights_and_recommendations"]
    lines.append(s9["title"])
    lines.append("9.1 Newsletter / Broadcast Summary")
    lines.append("  " + (s9.get("newsletter_broadcast_summary") or "—"))
    lines.append("")
    lines.append("9.2 Sequence / Automation Summary")
    lines.append("  " + (s9.get("sequence_automation_summary") or "—"))
    lines.append("")
    lines.append("9.3 Cold Outreach Summary")
    lines.append("  " + (s9.get("cold_outreach_summary") or "—"))
    lines.append("")
    lines.append("9.4 Recommended Actions")
    for i, a in enumerate(s9.get("recommended_actions") or [], 1):
        lines.append(f"  {i}. {a}")
    if s9.get("caveats"):
        lines.append("")
        lines.append("Caveats")
        for c in s9["caveats"]:
            lines.append(f"  • {c}")

    return "\n".join(lines)


def _text_from_paid_ads_template(report: dict[str, Any], pad: dict[str, Any]) -> str:
    lines: list[str] = []
    doc = pad["document"]
    m = report.get("meta", {})
    scope = report.get("scope", {})

    lines.append(doc.get("report_title", "Paid Ads Performance Report"))
    lines.append(doc.get("report_subtitle", ""))
    lines.append(doc.get("header_line", ""))
    lines.append("")
    lines.extend(_lines_monthly_report_data_sources_text(report))
    lines.extend(_lines_gsc_seo_text(report))
    lines.append("--- MVP scope: supported ---")
    for s in scope.get("supported_now", []):
        lines.append(f"  • {s.get('channel')}: {s.get('description')}")
    lines.append("")
    lines.append("--- MVP scope: intentionally out of scope ---")
    for s in scope.get("not_implemented", []):
        lines.append(f"  • {s.get('channel')}: {s.get('reason')}")
    lines.append("")

    s1 = pad["section_1_report_overview"]
    lines.append(s1["title"])
    lines.append(s1["intro"])
    lines.append("")
    lines.append("Executive summary")
    lines.append(s1.get("executive_summary", ""))
    lines.append("")
    for row in s1["overview_table"]:
        line = f"  {row['label']}: {row['value']}"
        if row.get("note"):
            line += f" ({row['note']})"
        lines.append(line)
    lines.append("")

    s2 = pad["section_2_facebook_meta_ads"]
    lines.append(s2["title"])
    sub = s2["subsection_2_1_core_kpis"]
    lines.append(sub["title"])
    lines.append("  " + " | ".join(sub["column_headers"]))
    for r in sub["rows"]:
        note = f" [{r['notes']}]" if r.get("notes") else ""
        lines.append(
            f"  {r['metric']} | {r['what_it_measures']} | {r['period_value']} | {r['benchmark_target']}{note}"
        )
    lines.append("")

    ce = s2["subsection_2_2_creative_engagement"]
    lines.append(ce["title"])
    lines.append(ce["intro"])
    lines.append("")
    lines.append(f"  {ce.get('status_label', 'Not available')}.")
    lines.append(f"  {ce['explanation']}")
    lines.append("")

    cb = s2["subsection_2_3_campaign_breakdown"]
    lines.append(cb["title"])
    lines.append(cb.get("instruction", ""))
    lines.append(
        "  Campaign | Objective | Spend | Impressions | Clicks/Results | CTR | CPC | CPM"
    )
    for c in cb["campaigns"]:
        ctr = c.get("ctr_display") or "—"
        cpc = c.get("cpc_display") or "—"
        cpm_v = c.get("cpm_display") or "—"
        lines.append(
            f"  {c['campaign_name'][:70]} | {c['objective']} | {c['spend_display']} | "
            f"{c['impressions_display']} | {c['clicks_label']}={c['clicks_or_results']} | {ctr} | {cpc} | {cpm_v}"
        )
    tr = cb["total_row"]
    lines.append(
        f"  TOTAL | — | {tr['spend_display']} | {tr['impressions_display']} | — | "
        f"{tr.get('ctr_display', '—')} | {tr.get('cpc_display', '—')} | {tr.get('cpm_display', '—')}"
    )
    lines.append(cb.get("footnote", ""))
    lines.append("")

    s3 = pad["section_3_google_ads"]
    lines.append(s3["title"])
    lines.append(f"  {s3.get('status_label', 'Not included')}: {s3['reason']}")
    lines.append("")

    s4 = pad["section_4_key_benchmarks"]
    lines.append(s4["title"])
    lines.append(s4["intro"])
    for br in s4["reference_rows"]:
        lines.append(f"  [{br['context']}] {br['metric']}: {br['target']}")
    lines.append("")

    s5 = pad["section_5_insights_and_recommendations"]
    lines.append(s5["title"])
    lines.append(s5["instruction"])
    lines.append("")
    lines.append(s5["section_5_1_facebook_ads_summary"]["title"])
    lines.append("  " + (s5["section_5_1_facebook_ads_summary"]["body"] or "—"))
    lines.append("")
    lines.append(s5["section_5_2_google_ads_summary"]["title"])
    lines.append("  " + s5["section_5_2_google_ads_summary"]["body"])
    lines.append("")
    lines.append(s5["section_5_3_recommended_actions"]["title"])
    for i, a in enumerate(s5["section_5_3_recommended_actions"]["action_items"], 1):
        lines.append(f"  {i}. {a}")

    ins = report.get("insights", {})
    if ins.get("caveats"):
        lines.append("")
        lines.append("--- Caveats (model) ---")
        for x in ins["caveats"]:
            lines.append(f"  • {x}")

    warn_all = report.get("ingestion", {}).get("warnings") or []
    if warn_all:
        lines.append("")
        lines.append("--- Data warnings ---")
        for w in warn_all:
            lines.append(f"  ! {w}")

    lines.append("")
    lines.append(doc.get("footer_attribution", ""))
    lines.append(f"Generated: {m.get('generated_at')}")
    return "\n".join(lines)


def report_to_json(report: dict[str, Any], indent: int = 2) -> str:
    return json.dumps(report, indent=indent, ensure_ascii=False)


def report_to_html(report: dict[str, Any], template_dir: Path, template_name: str = "report.html.j2") -> str:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = env.get_template(template_name)
    return tpl.render(report=report)


def report_to_markdown(report: dict[str, Any]) -> str:
    mon = report.get("monthly_report")
    if mon:
        return _md_from_monthly_report(report, mon)
    pad = report.get("paid_ads_report")
    if not pad:
        em = report.get("email_report")
        if em:
            return _md_from_email_template(report, em)
        return f"```json\n{report_to_json(report)}\n```"

    doc = pad["document"]
    m = report.get("meta", {})
    lines = [
        f"# {doc['report_title']}",
        f"*{doc['report_subtitle']}*",
        "",
        doc["header_line"],
        "",
    ]
    lines.extend(_lines_monthly_report_data_sources_markdown(report))
    lines.extend(_lines_gsc_seo_markdown(report))
    lines.extend(
        [
        "## Scope",
        "### Supported now",
        ]
    )
    for s in report.get("scope", {}).get("supported_now", []):
        lines.append(f"- **{s['channel']}:** {s['description']}")
    lines.extend(["", "### Intentionally out of scope (this MVP)", ""])
    for s in report.get("scope", {}).get("not_implemented", []):
        lines.append(f"- **{s['channel']}:** {s['reason']}")

    s1 = pad["section_1_report_overview"]
    lines.extend(
        [
            "",
            f"## {s1['title']}",
            "",
            s1["intro"],
            "",
            "### Executive summary",
            "",
            s1.get("executive_summary", ""),
            "",
        ]
    )
    oh = s1.get("overview_table_headers") or ["Metric", "Value"]
    lines.append("| " + " | ".join(oh) + " |")
    lines.append("| --- | --- |")
    for row in s1["overview_table"]:
        extra = f" *({row['note']})*" if row.get("note") else ""
        lines.append(f"| {row['label']} | {row['value']}{extra} |")
    lines.append("")

    s2 = pad["section_2_facebook_meta_ads"]
    sub = s2["subsection_2_1_core_kpis"]
    lines.extend([f"## {s2['title']}", f"### {sub['title']}", ""])
    lines.append("| " + " | ".join(sub["column_headers"]) + " |")
    lines.append("| --- | --- | --- | --- |")
    for r in sub["rows"]:
        lines.append(
            f"| {r['metric']} | {r['what_it_measures']} | {r['period_value']} | {r['benchmark_target']} |"
        )

    ce = s2["subsection_2_2_creative_engagement"]
    lines.extend(["", f"### {ce['title']}", "", ce["intro"], ""])
    lines.append(f"**{ce.get('status_label', 'Not available')}.** {ce['explanation']}")

    cb = s2["subsection_2_3_campaign_breakdown"]
    lines.extend(["", f"### {cb['title']}", "", cb.get("instruction", ""), ""])
    lines.append("| Campaign | Objective | Spend | Impressions | CTR | CPC | CPM |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for c in cb["campaigns"]:
        ctr = c.get("ctr_display") or (
            f"{c['ctr_pct']:.4f}%" if c.get("ctr_pct") is not None else "—"
        )
        cpc = c.get("cpc_display") or "—"
        cpm_v = c.get("cpm_display") or "—"
        spd = c.get("spend_display") or f"{c['spend']:,.2f} {c['currency']}"
        lines.append(
            f"| {c['campaign_name'][:80]} | {c['objective']} | {spd} | "
            f"{c.get('impressions_display', c['impressions'])} | {ctr} | {cpc} | {cpm_v} |"
        )
    tr = cb["total_row"]
    lines.append(
        f"| **TOTAL** | — | {tr.get('spend_display', tr['spend'])} | {tr.get('impressions_display', tr['impressions'])} | "
        f"{tr.get('ctr_display', '—')} | {tr.get('cpc_display', '—')} | {tr.get('cpm_display', '—')} |"
    )
    lines.extend(["", f"*{cb.get('footnote', '')}*", ""])

    s3 = pad["section_3_google_ads"]
    lines.extend(
        [
            f"## {s3['title']}",
            "",
            f"**{s3.get('status_label', 'Not included')}:** {s3['reason']}",
            "",
        ]
    )

    s4 = pad["section_4_key_benchmarks"]
    lines.extend([f"## {s4['title']}", "", s4["intro"], ""])
    for br in s4["reference_rows"]:
        lines.append(f"- **{br['context']} — {br['metric']}:** {br['target']}")

    s5 = pad["section_5_insights_and_recommendations"]
    lines.extend(
        [
            "",
            f"## {s5['title']}",
            "",
            s5["instruction"],
            "",
            f"### {s5['section_5_1_facebook_ads_summary']['title']}",
            "",
            s5["section_5_1_facebook_ads_summary"]["body"] or "—",
            "",
            f"### {s5['section_5_2_google_ads_summary']['title']}",
            "",
            s5["section_5_2_google_ads_summary"]["body"],
            "",
            f"### {s5['section_5_3_recommended_actions']['title']}",
            "",
        ]
    )
    for i, a in enumerate(s5["section_5_3_recommended_actions"]["action_items"], 1):
        lines.append(f"{i}. {a}")

    if report.get("insights", {}).get("caveats"):
        lines.extend(["", "### Caveats", ""])
        for x in report["insights"]["caveats"]:
            lines.append(f"- {x}")

    lines.extend(["", f"---", doc.get("footer_attribution", ""), f"*Generated {m.get('generated_at')}*"])
    return "\n".join(lines)


def _md_from_email_template(report: dict[str, Any], em: dict[str, Any]) -> str:
    doc = em["document"]
    lines = [
        f"# {doc['report_title']}",
        f"*{doc['report_subtitle']}*",
        "",
        doc["header_line"],
        "",
    ]
    lines.extend(_lines_monthly_report_data_sources_markdown(report))
    lines.extend(_lines_gsc_seo_markdown(report))
    lines.extend(
        [
        "## Topline",
        ]
    )
    for r in em.get("section_0_topline_table", []):
        lines.append(f"- **{r['label']}:** {r['value']}")

    s1 = em["section_1_report_overview"]
    lines.extend(["", f"## {s1['title']}", "", s1["body"]])

    s2 = em["section_2_list_health"]
    lines.extend(["", f"## {s2['title']}", "", f"**{s2['status_label']}.** {s2['explanation']}"])

    s3 = em["section_3_core_kpis"]
    lines.extend(["", f"## {s3['title']}", ""])
    lines.append("| Metric | How calculated | Value | Benchmark |")
    lines.append("| --- | --- | --- | --- |")
    for r in s3["rows"]:
        lines.append(f"| {r['metric']} | {r['how_calculated']} | {r['value']} | {r['benchmark']} |")

    s4 = em["section_4_campaign_breakdown"]
    sub = s4["subsection_4_1_broadcast"]
    lines.extend(["", f"## {s4['title']}", "", f"### {sub['title']}", ""])
    for r in sub["rows"]:
        lines.append(f"- **{r['campaign_name']}** — sent: {r.get('sent')} · open_rate: {r.get('open_rate_pct')} · ctr: {r.get('ctr_pct')}")
    if s4.get("note"):
        lines.extend(["", f"*{s4['note']}*"])

    s8 = em["section_8_key_benchmarks"]
    lines.extend(["", f"## {s8['title']}", ""])
    for b in s8["reference"]:
        lines.append(f"- **{b['metric']}**: {b['target']} (watch: {b['watch']})")

    s9 = em["section_9_insights_and_recommendations"]
    lines.extend(["", f"## {s9['title']}", ""])
    lines.append("### 9.1 Newsletter / Broadcast Summary")
    lines.append(s9.get("newsletter_broadcast_summary") or "—")
    lines.append("")
    lines.append("### 9.4 Recommended Actions")
    for i, a in enumerate(s9.get("recommended_actions") or [], 1):
        lines.append(f"{i}. {a}")
    if s9.get("caveats"):
        lines.extend(["", "### Caveats", ""])
        for c in s9["caveats"]:
            lines.append(f"- {c}")
    return "\n".join(lines)


def _text_from_monthly_report(report: dict[str, Any], mon: dict[str, Any]) -> str:
    meta = report.get("meta", {})
    lines: list[str] = []
    lines.append(mon.get("title", "Monthly Marketing Report"))
    sub = mon.get("subtitle")
    if sub:
        lines.append(sub)
    lines.append(f"Generated: {meta.get('generated_at')}")
    lines.append("")
    lines.extend(_lines_monthly_report_data_sources_text(report))
    if mon.get("connected_sources"):
        lines.append("--- Connected in this run ---")
        for s in mon["connected_sources"]:
            lines.append(f"  • {s.get('name')}: {s.get('purpose')}")
        lines.append("")

    clients = mon.get("clients", []) or []
    for c in clients:
        lines.append(f"=== Client: {c.get('client_name')} ({c.get('client_id')}) ===")
        seo = c.get("seo_search_console")
        if seo:
            # Reuse helper by wrapping into a report-like dict
            lines.extend(_lines_gsc_seo_text({"seo_search_console": seo}))
        pad = c.get("paid_ads_report")
        if pad:
            # Minimal paid-ads excerpt for combined run
            doc = pad.get("document", {})
            lines.append(doc.get("report_title", "Paid Ads Performance Report"))
            s1 = pad.get("section_1_report_overview", {})
            if s1.get("executive_summary"):
                lines.append("Executive summary")
                lines.append(s1["executive_summary"])
                lines.append("")
        lines.append("")
    return "\n".join(lines)


def _md_from_monthly_report(report: dict[str, Any], mon: dict[str, Any]) -> str:
    meta = report.get("meta", {})
    lines: list[str] = [
        f"# {mon.get('title', 'Monthly Marketing Report')}",
        "",
    ]
    if mon.get("subtitle"):
        lines.append(f"*{mon['subtitle']}*")
        lines.append("")
    if meta.get("generated_at"):
        lines.append(f"*Generated {meta['generated_at']}*")
        lines.append("")

    lines.extend(_lines_monthly_report_data_sources_markdown(report))
    if mon.get("connected_sources"):
        lines.extend(["## Connected in this run", ""])
        for s in mon["connected_sources"]:
            lines.append(f"- **{s.get('name')}:** {s.get('purpose')}")
        lines.append("")

    for c in mon.get("clients", []) or []:
        lines.extend(
            [
                "",
                f"## Client — {c.get('client_name')} ({c.get('client_id')})",
                "",
            ]
        )
        seo = c.get("seo_search_console")
        if seo:
            lines.extend(_lines_gsc_seo_markdown({"seo_search_console": seo}))
        pad = c.get("paid_ads_report")
        if pad:
            lines.extend(["## Paid ads — Meta export", ""])

            s1 = pad.get("section_1_report_overview", {})
            if s1.get("executive_summary"):
                lines.extend(["### Executive summary", "", s1["executive_summary"], ""])

            s2 = pad.get("section_2_facebook_meta_ads", {}) or {}

            # 2.1 Core KPIs (full table)
            core = (s2.get("subsection_2_1_core_kpis") or {})
            if core.get("rows"):
                lines.extend(["### 2.1 Core KPIs", ""])
                lines.append("| Metric | What it measures | Period value | Benchmark / target |")
                lines.append("| --- | --- | --- | --- |")
                for r in core["rows"]:
                    note = f" ({r.get('notes')})" if r.get("notes") else ""
                    lines.append(
                        f"| {r.get('metric')} | {r.get('what_it_measures')} | {r.get('period_value')}{note} | {r.get('benchmark_target')} |"
                    )
                lines.append("")

            # 2.3 Campaign breakdown (full table)
            cb = (s2.get("subsection_2_3_campaign_breakdown") or {})
            if cb.get("campaigns"):
                lines.extend(["### 2.3 Campaign Breakdown", ""])
                lines.append("| Campaign | Objective | Spend | Impressions | Clicks/Results | CTR | CPC | CPM |")
                lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
                for row in cb["campaigns"]:
                    lines.append(
                        f"| {row.get('campaign_name')} | {row.get('objective')} | {row.get('spend_display')} | "
                        f"{row.get('impressions_display')} | {row.get('clicks_label')}={row.get('clicks_or_results')} | "
                        f"{row.get('ctr_display') or '—'} | {row.get('cpc_display') or '—'} | {row.get('cpm_display') or '—'} |"
                    )
                tr = cb.get("total_row") or {}
                if tr:
                    lines.append(
                        f"| **TOTAL** | — | {tr.get('spend_display')} | {tr.get('impressions_display')} | — | "
                        f"{tr.get('ctr_display') or '—'} | {tr.get('cpc_display') or '—'} | {tr.get('cpm_display') or '—'} |"
                    )
                if cb.get("footnote"):
                    lines.extend(["", f"*{cb['footnote']}*", ""])

        em = c.get("email_report")
        if em:
            lines.extend(["## Email — Brevo", ""])
            if em.get("error"):
                lines.extend([f"**Error:** {em.get('error')}", ""])
            else:
                # Topline
                lines.extend(["### Topline", ""])
                for r in em.get("section_0_topline_table", []) or []:
                    lines.append(f"- **{r.get('label')}:** {r.get('value')}")
                # Core KPIs
                s3 = em.get("section_3_core_kpis") or {}
                if s3.get("rows"):
                    lines.extend(["", "### Core KPIs", ""])
                    lines.append("| Metric | How calculated | Value | Benchmark |")
                    lines.append("| --- | --- | --- | --- |")
                    for r in s3["rows"]:
                        lines.append(f"| {r.get('metric')} | {r.get('how_calculated')} | {r.get('value')} | {r.get('benchmark')} |")
                # Campaign breakdown (full rows now)
                s4 = em.get("section_4_campaign_breakdown") or {}
                sub = s4.get("subsection_4_1_broadcast") or {}
                if sub.get("rows"):
                    lines.extend(["", "### Campaign breakdown", ""])
                    lines.append("| Campaign | Sent | Open rate | CTR | CTOR | Unsubs |")
                    lines.append("| --- | --- | --- | --- | --- | --- |")
                    for r in sub["rows"]:
                        lines.append(
                            f"| {r.get('campaign_name')} | {r.get('sent')} | {r.get('open_rate_pct')} | {r.get('ctr_pct')} | {r.get('ctor_pct')} | {r.get('unsubs')} |"
                        )
    lines.append("")
    return "\n".join(lines)


def write_outputs(
    report: dict[str, Any],
    output_dir: Path,
    base_name: str = "report",
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    p_json = output_dir / f"{base_name}.json"
    p_json.write_text(report_to_json(report), encoding="utf-8")
    paths["json"] = str(p_json)

    p_txt = output_dir / f"{base_name}.txt"
    p_txt.write_text(report_to_text(report), encoding="utf-8")
    paths["txt"] = str(p_txt)

    p_md = output_dir / f"{base_name}.md"
    p_md.write_text(report_to_markdown(report), encoding="utf-8")
    paths["md"] = str(p_md)

    tpl_dir = _PROJECT_ROOT / "templates"
    if (tpl_dir / "report.html.j2").exists():
        p_html = output_dir / f"{base_name}.html"
        p_html.write_text(report_to_html(report, tpl_dir), encoding="utf-8")
        paths["html"] = str(p_html)

    return paths
