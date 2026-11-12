"""Catalogue of data sources: what is free, what is paid, how to enable each."""
from __future__ import annotations

import os

from .sources import broadcastify, radioid, radioreference, repeaterbook

SOURCES = [
    {
        "name": "ofcom_wtr", "cost": "free", "api": "static CSV download",
        "env": [], "enabled": True,
        "url": "https://www.ofcom.org.uk/spectrum/frequencies/wtr",
        "notes": "Auto-refreshed weekly on use (UK_RADIO_REFRESH_HOURS overrides). Some licences withheld by Ofcom.",
    },
    {
        "name": "radioid", "cost": "free (token optional)", "api": "REST + daily JSON dump",
        "env": ["RADIOID_API_TOKEN (optional)"], "enabled": True,
        "url": "https://radioid.net/api/",
        "notes": "Amateur-focused DMR IDs. Does not identify UK business radio users. No mirroring or commercial use.",
    },
    {
        "name": "repeaterbook", "cost": "approval/token required", "api": "REST (exportROW.php)",
        "env": ["REPEATERBOOK_TOKEN", "REPEATERBOOK_USER_AGENT"],
        "enabled": repeaterbook.configured(),
        "url": "https://www.repeaterbook.com/api/token_request.php",
        "notes": "Amateur repeaters. Personal non-commercial use. Scope api.export_row.",
    },
    {
        "name": "radioreference", "cost": "Premium subscription + approved app key", "api": "SOAP",
        "env": ["RADIOREFERENCE_APP_KEY", "RADIOREFERENCE_USERNAME", "RADIOREFERENCE_PASSWORD"],
        "enabled": radioreference.configured(),
        "url": "https://www.radioreference.com/account/api/apply",
        "notes": "Strongest for US/Canada; limited UK coverage. Needs the [radioreference] extra.",
    },
    {
        "name": "broadcastify", "cost": "Catalog API $2,500/month; Calls API prepaid metered (min $5)",
        "api": "REST (docs behind bcfy.io/dev/docs)",
        "env": ["BROADCASTIFY_API_KEY", "BROADCASTIFY_BASE_URL", "BROADCASTIFY_AUTH_HEADER (optional)"],
        "enabled": broadcastify.configured(),
        "url": "https://bcfy.io/dev/apply/",
        "notes": "Passthrough only; endpoints come from the official docs.",
    },
    {
        "name": "ukafg", "cost": "GBP 5-100/yr", "api": "none (CSV/XLSX/XML exports)", "env": [],
        "enabled": False, "url": "https://ukafg.co.uk/",
        "notes": "Commercial licence forbids redistributing the raw database. Import exports manually.",
    },
    {
        "name": "radioreferenceuk", "cost": "GBP 16/yr", "api": "none (exports, Scanner Linker app)",
        "env": [], "enabled": False, "url": "https://radioreferenceuk.co.uk/subscribe.php",
        "notes": "50 mile / 1,000 result search caps. Blocks automated fetches.",
    },
    {
        "name": "scanlocaluk", "cost": "GBP 5.99 first year, then 9.99/yr", "api": "none (scanner file exports)",
        "env": [], "enabled": False, "url": "https://scanlocaluk.co.uk/subscribe",
        "notes": "Built from the same Ofcom WTR data this server reads for free.",
    },
]


def env_state() -> dict:
    keys = {k.split(" ")[0] for s in SOURCES for k in s["env"]}
    return {k: bool(os.environ.get(k)) for k in sorted(keys)}


_ = radioid  # imported for completeness of the catalogue
