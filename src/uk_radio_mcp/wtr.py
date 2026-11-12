"""Ofcom Wireless Telegraphy Register (WTR) loader and search. Free, public data."""
from __future__ import annotations

import csv
import threading
from dataclasses import dataclass, field

from .cache import ensure_fresh
from .geo import haversine_km

WTR_URL = "https://static.ofcom.org.uk/static/radiolicensing/html/register/WTR.csv"
WTR_FILE = "WTR.csv"
WTR_MAX_AGE_HOURS = 24 * 7  # Ofcom refreshes regularly; weekly is plenty

_lock = threading.Lock()
_rows: list[dict] | None = None
_loaded_mtime: float | None = None
_status = ""


@dataclass
class Licence:
    licence: str
    licensee: str
    ngr: str
    lat: float | None
    lon: float | None
    product: str
    issued: str
    status: str
    entries: set = field(default_factory=set)  # (freq_mhz, station_type, emission)
    dist: float | None = None

    def as_dict(self, distance_km: float | None = None) -> dict:
        d = {
            "licence": self.licence,
            "licensee": self.licensee,
            "grid_ref": self.ngr,
            "lat": self.lat,
            "lon": self.lon,
            "licence_type": self.product,
            "issued": self.issued,
            "status": self.status,
            "frequencies": sorted(
                {(f, e) for f, _t, e in self.entries}, key=lambda x: (x[0], x[1])
            ),
        }
        d["frequencies"] = [{"mhz": f, "emission": e} for f, e in d["frequencies"]]
        if distance_km is not None:
            d["distance_km"] = round(distance_km, 1)
        return d


def _f(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load(force: bool = False) -> list[dict]:
    """Load WTR rows, refreshing the cached file if it is older than the interval."""
    global _rows, _loaded_mtime, _status
    with _lock:
        path, status = ensure_fresh(WTR_FILE, WTR_URL, WTR_MAX_AGE_HOURS, force=force)
        mtime = path.stat().st_mtime
        if _rows is None or _loaded_mtime != mtime:
            with open(path, encoding="latin-1", newline="") as fh:
                _rows = list(csv.DictReader(fh))
            _loaded_mtime = mtime
        _status = status
        return _rows


def status() -> str:
    return _status


def search(
    freq_mhz: float | None = None,
    freq_min_mhz: float | None = None,
    freq_max_mhz: float | None = None,
    emission: str | None = None,
    licensee: str | None = None,
    centre: tuple[float, float] | None = None,
    radius_km: float | None = None,
    bbox: tuple[float, float, float, float] | None = None,  # lat0, lat1, lon0, lon1
    limit: int = 100,
) -> dict:
    """Filter the register. All filters are ANDed. Rows are grouped per licence+site."""
    rows = load()
    want_hz = round(freq_mhz * 1e6) if freq_mhz is not None else None
    lo = round(freq_min_mhz * 1e6) if freq_min_mhz is not None else None
    hi = round(freq_max_mhz * 1e6) if freq_max_mhz is not None else None
    name = licensee.lower() if licensee else None
    emi = emission.upper() if emission else None
    groups: dict[tuple, Licence] = {}
    for r in rows:
        hz = _f(r["Frequency (Hz)"])
        if hz is None:
            continue
        if want_hz is not None and round(hz) != want_hz:
            continue
        if lo is not None and hz < lo:
            continue
        if hi is not None and hz > hi:
            continue
        if emi and r["Emission Code"].upper() != emi:
            continue
        company = r["Licencee Company"].strip()
        who = company if company not in ("", "-") else r["Licencee Surname"].strip()
        if name and name not in who.lower():
            continue
        lat, lon = _f(r["Latitude(Deg)"]), _f(r["Longitude(Deg)"])
        if bbox and (
            lat is None or lon is None
            or not (bbox[0] <= lat <= bbox[1] and bbox[2] <= lon <= bbox[3])
        ):
            continue
        dist = None
        if centre and radius_km is not None:
            if lat is None or lon is None:
                continue
            dist = haversine_km(centre[0], centre[1], lat, lon)
            if dist > radius_km:
                continue
        key = (r["Licence Number"], r["NGR"])
        g = groups.get(key)
        if g is None:
            g = groups[key] = Licence(
                r["Licence Number"], who if who != "-" else "(name withheld)", r["NGR"],
                lat, lon, r["Product Description"], r["License Issue Date"][:10], r["Status"],
            )
        g.entries.add((hz / 1e6, r["Station Type"], r["Emission Code"]))
        g.dist = dist
    found = sorted(groups.values(), key=lambda g: (g.dist is None, g.dist or 0, g.licensee))
    return {
        "register_status": _status,
        "total_matches": len(found),
        "returned": min(len(found), limit),
        "results": [g.as_dict(g.dist) for g in found[:limit]],
    }
