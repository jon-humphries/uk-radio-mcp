"""Scanner import file export (Whistler EZ Scan text import: Alpha Tag, Frequency, Mode)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import httpx

from . import wtr
from .cache import USER_AGENT, cache_dir
from .geo import haversine_km

TAG_LEN = 16
_STRIP = (" Limited", " LIMITED", " Ltd.", " Ltd", " LTD", " Plc", " PLC", " P L C", " (uk)", " (UK)")


def make_tag(name: str, length: int = TAG_LEN) -> str:
    n = name.strip()
    for s in _STRIP:
        n = n.replace(s, "")
    n = re.sub(r"\s+", " ", n).strip() or "Unknown"
    if n.isupper():
        n = n.title()
    return n[:length]


def _district_cache() -> tuple[Path, dict]:
    p = cache_dir() / "site_districts.json"
    try:
        return p, json.loads(p.read_text())
    except (OSError, ValueError):
        return p, {}


def districts(points: dict[str, tuple[float, float]]) -> dict[str, str | None]:
    """Map site key -> admin district via postcodes.io bulk reverse geocoding (cached)."""
    path, known = _district_cache()
    todo = [k for k in points if k not in known]
    for i in range(0, len(todo), 100):
        chunk = todo[i : i + 100]
        body = {"geolocations": [
            {"latitude": points[k][0], "longitude": points[k][1], "radius": 2000, "limit": 1}
            for k in chunk
        ]}
        r = httpx.post("https://api.postcodes.io/postcodes", json=body,
                       headers={"User-Agent": USER_AGENT}, timeout=60)
        r.raise_for_status()
        for k, x in zip(chunk, r.json()["result"]):
            res = x["result"]
            known[k] = res[0]["admin_district"] if res else None
    if todo:
        path.write_text(json.dumps(known))
    return {k: known.get(k) for k in points}


def whistler_rows(
    centre: tuple[float, float],
    radius_km: float,
    counties: list[str] | None = None,
    freq_min_mhz: float = 400.0,
    freq_max_mhz: float = 470.0,
    freq_mhz: list[float] | None = None,
) -> list[tuple[float, str]]:
    """Return sorted (MHz, alpha tag) rows, one per frequency and licensee."""
    lo, hi = freq_min_mhz * 1e6, freq_max_mhz * 1e6
    only = {round(f * 1e6) for f in freq_mhz} if freq_mhz else None
    sites: dict[str, tuple[float, float]] = {}
    cand = []
    for r in wtr.load():
        try:
            hz = float(r["Frequency (Hz)"])
            la, lo_ = float(r["Latitude(Deg)"]), float(r["Longitude(Deg)"])
        except ValueError:
            continue
        if not lo <= hz <= hi or (only and round(hz) not in only):
            continue
        if haversine_km(centre[0], centre[1], la, lo_) > radius_km:
            continue
        key = f"{r['Licence Number']}|{r['NGR']}"
        sites[key] = (la, lo_)
        cand.append((key, hz, r))
    allowed = None
    if counties:
        want = {c.lower() for c in counties}
        dmap = districts(sites)
        allowed = {k for k, d in dmap.items() if d and d.lower() in want}
    seen: dict[tuple[float, str], str] = {}
    for key, hz, r in cand:
        if allowed is not None and key not in allowed:
            continue
        who = r["Licencee Company"].strip()
        if who in ("", "-"):
            who = r["Licencee Surname"].strip()
        seen.setdefault((round(hz / 1e6, 4), who), make_tag(who))
    return sorted((mhz, tag) for (mhz, _w), tag in seen.items())


def write_whistler(rows: list[tuple[float, str]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write("Alpha Tag,Frequency,Mode\r\n")
        for mhz, tag in rows:
            f.write(f'"{tag.replace(chr(34), "")}",{mhz:.4f},AUTO\r\n')
    return path
