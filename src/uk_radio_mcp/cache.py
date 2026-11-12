"""Download cache with refresh-on-use for static datasets.

Every static dataset is fetched lazily. When a tool needs it, we check the age of
the cached copy and re-download if it is older than the refresh interval.
If a refresh fails, a stale copy is still used so tools keep working offline.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import httpx

USER_AGENT = os.environ.get(
    "UK_RADIO_USER_AGENT", "uk-radio-mcp/0.1 (+https://github.com/jon-humphries/uk-radio-mcp)"
)


def cache_dir() -> Path:
    d = Path(os.environ.get("UK_RADIO_CACHE_DIR", Path.home() / ".cache" / "uk-radio-mcp"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def refresh_hours(default: float) -> float:
    """Global override UK_RADIO_REFRESH_HOURS, else the dataset default."""
    raw = os.environ.get("UK_RADIO_REFRESH_HOURS")
    try:
        return float(raw) if raw else default
    except ValueError:
        return default


def age_hours(path: Path) -> float | None:
    if not path.exists():
        return None
    return (time.time() - path.stat().st_mtime) / 3600


def ensure_fresh(name: str, url: str, max_age_hours: float, force: bool = False) -> tuple[Path, str]:
    """Return (path, status). Status is 'fresh', 'downloaded' or 'stale (reason)'."""
    path = cache_dir() / name
    age = age_hours(path)
    limit = refresh_hours(max_age_hours)
    if not force and age is not None and age < limit:
        return path, "fresh"
    tmp = path.with_suffix(path.suffix + ".part")
    try:
        with httpx.stream(
            "GET", url, headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=300
        ) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r.iter_bytes(1 << 16):
                    f.write(chunk)
        tmp.replace(path)
        return path, "downloaded"
    except Exception as exc:  # network or HTTP failure
        tmp.unlink(missing_ok=True)
        if path.exists():
            return path, f"stale (refresh failed: {exc})"
        raise RuntimeError(f"Could not download {url}: {exc}") from exc
