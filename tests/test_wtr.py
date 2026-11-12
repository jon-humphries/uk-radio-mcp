import csv

import pytest

from uk_radio_mcp import cache, wtr
from uk_radio_mcp.geo import haversine_km

HEADER = [
    "Licence Number", "License Issue Date", "NGR", "Frequency (Hz)", "Station Type",
    "Emission Code", "Licencee Surname", "Licencee Company", "Status",
    "Product Description", "Latitude(Deg)", "Longitude(Deg)",
]


def row(num, freq, emi, company, lat, lon, st="T"):
    return [num, "2026-01-01 00:00:00", "SU 0 0", str(freq), st, emi, "-", company, "Live",
            "BR Tech Assigned", str(lat), str(lon)]


@pytest.fixture()
def register(tmp_path, monkeypatch):
    monkeypatch.setenv("UK_RADIO_CACHE_DIR", str(tmp_path))
    with open(tmp_path / "WTR.csv", "w", newline="", encoding="latin-1") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER)
        w.writerow(row("1/1", 456637500, "12K5G7W", "Acme Ltd", 51.6, -1.3))
        w.writerow(row("1/1", 456637500, "12K5G7W", "Acme Ltd", 51.6, -1.3, "R"))
        w.writerow(row("2/1", 456637500, "8K30F1W", "Far Away plc", 57.0, -4.0))
        w.writerow(row("3/1", 453012500, "8K30F1W", "Marches Academy Trust", 52.84, -2.72))
    monkeypatch.setattr(cache, "ensure_fresh", lambda *a, **k: (tmp_path / "WTR.csv", "fresh"))
    monkeypatch.setattr(wtr, "ensure_fresh", lambda *a, **k: (tmp_path / "WTR.csv", "fresh"))
    wtr._rows = None
    return tmp_path


def test_frequency_and_emission(register):
    res = wtr.search(freq_mhz=456.6375, emission="12K5G7W")
    assert res["total_matches"] == 1
    assert res["results"][0]["licensee"] == "Acme Ltd"


def test_licensee_search(register):
    assert wtr.search(licensee="marches")["results"][0]["frequencies"][0]["mhz"] == 453.0125


def test_radius_sorted_and_filtered(register):
    res = wtr.search(freq_mhz=456.6375, centre=(51.5, -1.2), radius_km=50)
    assert [r["licensee"] for r in res["results"]] == ["Acme Ltd"]
    assert res["results"][0]["distance_km"] < 20


def test_haversine():
    assert haversine_km(51.5, 0, 51.5, 0) == 0
    assert 110 < haversine_km(51, 0, 52, 0) < 112


def test_stale_cache_used_when_refresh_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("UK_RADIO_CACHE_DIR", str(tmp_path))
    (tmp_path / "x.csv").write_text("old")
    import os, time
    old = time.time() - 99999
    os.utime(tmp_path / "x.csv", (old, old))
    path, status = cache.ensure_fresh("x.csv", "http://127.0.0.1:1/none", 1)
    assert path.read_text() == "old" and status.startswith("stale")
