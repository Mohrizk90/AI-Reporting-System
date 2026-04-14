"""Load Excel/CSV Meta exports and map to unified schema."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from mvp.schema import CampaignRow, NormalizedDataset

# Aliases: lowercase stripped key -> canonical column intent
KNOWN_COLUMNS = {
    "reporting starts": "reporting_starts",
    "reporting ends": "reporting_ends",
    "campaign name": "campaign_name",
    "campaign delivery": "campaign_delivery",
    "results": "results",
    "result indicator": "result_indicator",
    "cost per results": "cost_per_result",
    "ad set budget": "ad_set_budget",
    "ad set budget type": "ad_set_budget_type",
    "ends": "campaign_ends",
    "attribution setting": "attribution_setting",
    "impressions": "impressions",
    "reach": "reach",
}

SPEND_PATTERN = re.compile(r"amount spent \((?P<cur>[A-Z]{3})\)", re.I)


def _normalize_column_name(c: str) -> str:
    return str(c).strip().strip('"').lower()


def _find_spend_column(columns: list[str]) -> tuple[str, str] | None:
    """Return (original_col_name, currency_code)."""
    for c in columns:
        m = SPEND_PATTERN.match(_normalize_column_name(c))
        if m:
            return c, m.group("cur").upper()
    return None


def _coerce_date(val: Any):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    ts = pd.to_datetime(val, errors="coerce")
    if pd.isna(ts):
        return None
    return ts.date()


def _coerce_float(val: Any) -> float | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _build_rename_map(df_columns: list[str]) -> dict[str, str]:
    rename: dict[str, str] = {}
    for c in df_columns:
        key = _normalize_column_name(c)
        if key in KNOWN_COLUMNS:
            rename[c] = KNOWN_COLUMNS[key]
        spend = SPEND_PATTERN.match(key)
        if spend:
            rename[c] = "amount_spent"
    return rename


def load_table(path: str | Path, sheet_name: str | int | None = 0) -> pd.DataFrame:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        return pd.read_excel(path, sheet_name=sheet_name or 0)
    if suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported format: {suffix}")


def normalize_meta_export(
    path: str | Path,
    client_id: str,
    client_display_name: str,
    sheet_name: str | int | None = 0,
) -> NormalizedDataset:
    """
    Load file and return NormalizedDataset.
    Expects Meta campaign export columns; spend column must be 'Amount spent (XXX)'.
    """
    path = Path(path)
    df = load_table(path, sheet_name=sheet_name)
    df.columns = [str(c).strip().strip('"') for c in df.columns]

    warnings: list[str] = []
    spend_info = _find_spend_column(list(df.columns))
    if not spend_info:
        raise ValueError(
            "No column matching 'Amount spent (CUR)'. Expected e.g. 'Amount spent (NGN)'."
        )
    spend_col, currency = spend_info

    rename = _build_rename_map(list(df.columns))
    df = df.rename(columns=rename)
    if "amount_spent" not in df.columns:
        df["amount_spent"] = df[spend_col]

    required = [
        "reporting_starts",
        "reporting_ends",
        "campaign_name",
        "campaign_delivery",
        "results",
        "result_indicator",
        "impressions",
        "reach",
        "amount_spent",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns after mapping: {missing}. Got: {list(df.columns)}")

    rows: list[CampaignRow] = []
    for i, rec in enumerate(df.to_dict(orient="records"), start=2):
        rs = _coerce_date(rec.get("reporting_starts"))
        re_ = _coerce_date(rec.get("reporting_ends"))
        if rs is None or re_ is None:
            warnings.append(f"Row {i}: invalid reporting dates; skipped.")
            continue

        ce = _coerce_date(rec.get("campaign_ends"))

        name = rec.get("campaign_name")
        if name is None or (isinstance(name, float) and pd.isna(name)):
            warnings.append(f"Row {i}: missing campaign name; skipped.")
            continue

        rows.append(
            CampaignRow(
                reporting_starts=rs,
                reporting_ends=re_,
                campaign_name=str(name).strip(),
                campaign_delivery=str(rec.get("campaign_delivery") or "").strip(),
                results=float(rec.get("results") or 0),
                result_indicator=str(rec.get("result_indicator") or "").strip(),
                cost_per_result=_coerce_float(rec.get("cost_per_result")),
                ad_set_budget=rec.get("ad_set_budget"),
                ad_set_budget_type=str(rec.get("ad_set_budget_type") or "").strip() or None,
                amount_spent=float(rec.get("amount_spent") or 0),
                currency=currency,
                impressions=float(rec.get("impressions") or 0),
                reach=float(rec.get("reach") or 0),
                campaign_ends=ce,
                attribution_setting=(
                    str(rec.get("attribution_setting")).strip()
                    if rec.get("attribution_setting") not in (None, "")
                    and not (isinstance(rec.get("attribution_setting"), float) and pd.isna(rec.get("attribution_setting")))
                    else None
                ),
                source_row_index=i,
            )
        )

    # Normalize Ends column: Excel may use "Ends" not mapped — check raw
    if not rows:
        raise ValueError("No valid rows after cleaning.")

    indicators = {r.result_indicator for r in rows if r.result_indicator}
    if len(indicators) > 1:
        warnings.append(
            "Multiple result_indicator values in file; summed 'results' are not one conversion type."
        )

    return NormalizedDataset(
        client_id=client_id,
        client_display_name=client_display_name,
        rows=rows,
        currency=currency,
        warnings=warnings,
        raw_path=str(path.resolve()),
    )


def dataset_to_json_serializable(ds: NormalizedDataset) -> dict[str, Any]:
    return ds.to_dict()
