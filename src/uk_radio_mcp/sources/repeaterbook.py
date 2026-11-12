"""RepeaterBook rest-of-world export API (approval/token required).

Env:
  REPEATERBOOK_TOKEN       token (app_... or per-user rbuapp_...) with scope api.export_row
  REPEATERBOOK_USER_AGENT  must match the approved application's User-Agent literally,
                           otherwise the API returns 403 ua_mismatch
Request access: https://www.repeaterbook.com/api/token_request.php
Per-user tokens: https://www.repeaterbook.com/user/api_apps.php
Data is for personal, non-commercial use. Attribution: "Data courtesy of RepeaterBook.com".
"""
from __future__ import annotations

import hashlib
import json
import os
import time

import httpx

from ..cache import cache_dir

BASE = "https://www.repeaterbook.com/api/exportROW.php"
CACHE_HOURS = 1.0  # response cache; refreshed on use after this age
FILTERS = ("callsign", "city", "landmark", "country", "region", "frequency", "mode")


def configured() -> bool:
    return bool(os.environ.get("REPEATERBOOK_TOKEN") and os.environ.get("REPEATERBOOK_USER_AGENT"))


def missing_message() -> str:
    return (
        "RepeaterBook is not configured. Set REPEATERBOOK_TOKEN and REPEATERBOOK_USER_AGENT "
        "(the UA must match your approved app). Request access at "
        "https://www.repeaterbook.com/api/token_request.php"
    )


def export_row(**filters: str) -> dict:
    q = {k: v for k, v in filters.items() if k in FILTERS and v}
    key = hashlib.sha1(json.dumps(q, sort_keys=True).encode()).hexdigest()[:16]
    f = cache_dir() / f"repeaterbook_{key}.json"
    if f.exists() and (time.time() - f.stat().st_mtime) / 3600 < CACHE_HOURS:
        return json.loads(f.read_text())
    r = httpx.get(
        BASE,
        params=q,
        headers={
            "X-RB-App-Token": os.environ["REPEATERBOOK_TOKEN"],
            "User-Agent": os.environ["REPEATERBOOK_USER_AGENT"],
        },
        follow_redirects=False,  # RepeaterBook asks clients to stop on any 3xx
        timeout=60,
    )
    if r.status_code == 429:
        raise RuntimeError("RepeaterBook rate limited (429). Back off and retry later.")
    if r.status_code != 200:
        raise RuntimeError(f"RepeaterBook returned {r.status_code}: {r.text[:300]}")
    data = r.json()
    f.write_text(json.dumps(data))
    return data
