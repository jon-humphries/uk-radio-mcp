"""Location helpers: haversine distance and postcode lookup (postcodes.io, free, no key)."""
from __future__ import annotations

import math

import httpx

from .cache import USER_AGENT


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def postcode_to_latlon(postcode: str) -> tuple[float, float]:
    pc = postcode.strip().replace(" ", "").upper()
    r = httpx.get(
        f"https://api.postcodes.io/postcodes/{pc}",
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    if r.status_code != 200:
        raise ValueError(f"Postcode {postcode!r} not found")
    res = r.json()["result"]
    return float(res["latitude"]), float(res["longitude"])


def resolve_location(
    lat: float | None, lon: float | None, postcode: str | None
) -> tuple[float, float] | None:
    if lat is not None and lon is not None:
        return lat, lon
    if postcode:
        return postcode_to_latlon(postcode)
    return None
