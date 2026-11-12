"""RadioID.net DMR user/repeater data. Free. Optional RADIOID_API_TOKEN (X-API-Token).

Note: this database is amateur radio (and some other) DMR IDs. It does not cover
UK business radio users. RadioID terms forbid mirroring or commercial use.
"""
from __future__ import annotations

import json
import os
import threading

import httpx

from ..cache import USER_AGENT, ensure_fresh

USERS_URL = "https://radioid.net/static/users.json"
USERS_FILE = "radioid_users.json"
MAX_AGE_HOURS = 24  # RadioID refreshes its dumps daily
API = "https://radioid.net/api"

_lock = threading.Lock()
_users: list[dict] | None = None
_mtime: float | None = None


def _headers() -> dict:
    h = {"User-Agent": USER_AGENT}
    tok = os.environ.get("RADIOID_API_TOKEN")
    if tok:
        h["X-API-Token"] = tok
    return h


def _load() -> tuple[list[dict], str]:
    global _users, _mtime
    with _lock:
        path, status = ensure_fresh(USERS_FILE, USERS_URL, MAX_AGE_HOURS)
        m = path.stat().st_mtime
        if _users is None or _mtime != m:
            with open(path, encoding="utf-8") as fh:
                _users = json.load(fh).get("users", [])
            _mtime = m
        return _users, status


def lookup_local(
    radio_id: int | None = None,
    callsign: str | None = None,
    country: str | None = None,
    limit: int = 25,
) -> dict:
    """Search the cached daily dump (fast, offline after first download)."""
    users, status = _load()
    cs = callsign.upper() if callsign else None
    ct = country.lower() if country else None
    out = []
    for u in users:
        if radio_id is not None and int(u.get("radio_id", u.get("id", -1))) != radio_id:
            continue
        if cs and cs not in str(u.get("callsign", "")).upper():
            continue
        if ct and ct != str(u.get("country", "")).lower():
            continue
        out.append(u)
        if len(out) >= limit:
            break
    return {"dump_status": status, "returned": len(out), "results": out}


def api_get(path: str, **params) -> dict:
    """Call the live REST API, e.g. api_get('users', callsign='M0ABC')."""
    r = httpx.get(f"{API}/{path}", params=params, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()
