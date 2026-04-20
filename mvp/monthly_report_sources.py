"""Target data sources for the full monthly marketing report (roadmap + contract for JSON outputs)."""

from __future__ import annotations

from typing import Any


def build_monthly_report_data_sources_payload() -> dict[str, Any]:
    """
    Declares which APIs / inputs the monthly report is designed to use.
    Individual report runs may still be MVP-limited; see ``scope`` on the same payload.
    """
    return {
        "intent": "monthly_marketing_report_target_integrations",
        "sources": [
            {
                "id": "meta_marketing_api",
                "name": "Meta Marketing API",
                "purpose": "Facebook/Instagram paid media",
            },
            {
                "id": "meta_pages_instagram",
                "name": "Meta Pages / Instagram APIs",
                "purpose": "Page/account-level social metrics where applicable",
            },
            {
                "id": "google_search_console_api",
                "name": "Google Search Console API",
                "purpose": "SEO / organic search performance",
            },
            {
                "id": "linkedin_marketing",
                "name": "LinkedIn Marketing APIs",
                "purpose": "Ads, reporting, and page-related marketing data (subject to access and permissions)",
            },
            {
                "id": "brevo_api",
                "name": "Brevo API",
                "purpose": "Email campaigns and related ESP metrics",
            },
        ],
        "fallback_note": (
            "Optional CSV/Excel import for any source when API access is delayed or unavailable."
        ),
    }
