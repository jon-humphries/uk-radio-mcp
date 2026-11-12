"""MCP server entry point."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import catalogue, wtr
from .geo import resolve_location
from .sources import radioid, radioreference, repeaterbook

mcp = FastMCP("uk-radio")


@mcp.tool()
def list_sources() -> dict:
    """List every data source (free and paid), whether it is enabled, its cost, and the
    environment variables needed to enable it."""
    return {"sources": catalogue.SOURCES, "env_vars_set": catalogue.env_state()}


@mcp.tool()
def refresh_register(force: bool = True) -> dict:
    """Re-download the Ofcom Wireless Telegraphy Register now. Normally this happens
    automatically on use when the cached copy is older than a week."""
    rows = wtr.load(force=force)
    return {"rows": len(rows), "status": wtr.status()}


@mcp.tool()
def search_licences(
    freq_mhz: float | None = None,
    freq_min_mhz: float | None = None,
    freq_max_mhz: float | None = None,
    emission: str | None = None,
    licensee: str | None = None,
    postcode: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
    limit: int = 50,
) -> dict:
    """Search Ofcom's register of licensed UK radio sites (free). Filters are combined.
    freq_mhz: exact channel, e.g. 456.6375. freq_min_mhz/freq_max_mhz: a range.
    emission: e.g. 12K5G7W (12.5 kHz digital). licensee: name substring.
    postcode or lat/lon plus radius_km: only sites within that distance, nearest first.
    Returns licensee, grid ref, lat/lon, licence type and frequencies per site."""
    centre = resolve_location(lat, lon, postcode)
    if centre and radius_km is None:
        radius_km = 25.0
    return wtr.search(
        freq_mhz=freq_mhz, freq_min_mhz=freq_min_mhz, freq_max_mhz=freq_max_mhz,
        emission=emission, licensee=licensee, centre=centre, radius_km=radius_km, limit=limit,
    )


@mcp.tool()
def search_licensee(name: str, limit: int = 50) -> dict:
    """Find every licence and frequency held by a licensee whose name contains `name`."""
    return wtr.search(licensee=name, limit=limit)


@mcp.tool()
def lookup_dmr_id(
    radio_id: int | None = None, callsign: str | None = None, country: str | None = None,
    limit: int = 25,
) -> dict:
    """Look up DMR radio IDs in RadioID.net's daily dump (free). Amateur-focused: UK business
    radio IDs are not in it."""
    return radioid.lookup_local(radio_id, callsign, country, limit)


@mcp.tool()
def radioid_api(path: str, params: dict | None = None) -> dict:
    """Call the live RadioID REST API, e.g. path='repeaters/dmr' params={'country':'United Kingdom'}.
    Uses RADIOID_API_TOKEN if set. per_page is capped at 200 by the service."""
    return radioid.api_get(path.strip("/"), **(params or {}))


@mcp.tool()
def repeaterbook_search(
    country: str = "United Kingdom", callsign: str | None = None, city: str | None = None,
    frequency: str | None = None, mode: str | None = None, region: str | None = None,
    landmark: str | None = None,
) -> dict:
    """Search RepeaterBook's rest-of-world export (needs REPEATERBOOK_TOKEN and
    REPEATERBOOK_USER_AGENT). mode: analog, DMR, NXDN, P25 or tetra. % is a wildcard."""
    if not repeaterbook.configured():
        return {"error": repeaterbook.missing_message()}
    return repeaterbook.export_row(
        country=country, callsign=callsign, city=city, frequency=frequency,
        mode=mode, region=region, landmark=landmark,
    )


@mcp.tool()
def radioreference_call(method: str, params: dict | None = None) -> dict:
    """Call a RadioReference SOAP method, e.g. getCountyInfo with {'ctid': 1234}. Needs
    RADIOREFERENCE_APP_KEY, _USERNAME, _PASSWORD and the [radioreference] extra."""
    if not radioreference.configured():
        return {"error": radioreference.missing_message()}
    return {"result": radioreference.call(method, **(params or {}))}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
