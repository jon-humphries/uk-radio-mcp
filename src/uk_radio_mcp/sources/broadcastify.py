"""Broadcastify Developer Program APIs (paid, application reviewed).

Env:
  BROADCASTIFY_API_KEY   key issued at https://bcfy.io/dev/apply/
  BROADCASTIFY_BASE_URL  API base URL from https://bcfy.io/dev/docs/
  BROADCASTIFY_AUTH_HEADER  header name for the key (default: Authorization, sent as Bearer)

The public overview pages do not state the base URL, auth header or endpoint paths,
and the docs site refused automated access when this was written. So this module is a
thin authenticated GET passthrough: you supply the base URL and a path taken from the
official docs. Nothing here guesses endpoints.

Pricing (from Broadcastify support pages, check bcfy.io/dev/pricing/ for current):
  Live Audio Feed Catalog API: flat $2,500/month
  Calls Client API: prepaid, metered per record read, $5 minimum credit
"""
from __future__ import annotations

import os

import httpx

from ..cache import USER_AGENT


def configured() -> bool:
    return bool(os.environ.get("BROADCASTIFY_API_KEY") and os.environ.get("BROADCASTIFY_BASE_URL"))


def missing_message() -> str:
    return (
        "Broadcastify is not configured. Set BROADCASTIFY_API_KEY and BROADCASTIFY_BASE_URL "
        "(see https://bcfy.io/dev/docs/). Apply at https://bcfy.io/dev/apply/"
    )


def get(path: str, params: dict | None = None) -> dict:
    base = os.environ["BROADCASTIFY_BASE_URL"].rstrip("/")
    header = os.environ.get("BROADCASTIFY_AUTH_HEADER", "Authorization")
    key = os.environ["BROADCASTIFY_API_KEY"]
    value = f"Bearer {key}" if header.lower() == "authorization" else key
    r = httpx.get(
        f"{base}/{path.lstrip('/')}",
        params=params or {},
        headers={header: value, "User-Agent": USER_AGENT},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()
