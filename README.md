# uk-radio-mcp

An [MCP](https://modelcontextprotocol.io) server for UK radio frequency data. It reads Ofcom's
Wireless Telegraphy Register (free) and can add optional paid or approval-gated sources when you
supply API keys as environment variables.

Ask your assistant things like "who is licensed on 456.6375 MHz with a 12.5 kHz digital
emission?" or "list business radio licences within 15 km of SY1 1AA".

## Tools

| Tool | Source | Needs |
|---|---|---|
| `list_sources` | all | nothing. Shows what is enabled and what each paid source costs |
| `search_licences` | Ofcom WTR | nothing. Filter by frequency, range, emission code, licensee, postcode or lat/lon plus radius |
| `search_licensee` | Ofcom WTR | nothing |
| `refresh_register` | Ofcom WTR | nothing. Forces a re-download |
| `lookup_dmr_id` | RadioID dump | nothing |
| `radioid_api` | RadioID REST | optional `RADIOID_API_TOKEN` |
| `repeaterbook_search` | RepeaterBook | `REPEATERBOOK_TOKEN`, `REPEATERBOOK_USER_AGENT` |
| `radioreference_call` | RadioReference SOAP | `RADIOREFERENCE_APP_KEY`, `_USERNAME`, `_PASSWORD` |
| `broadcastify_get` | Broadcastify | `BROADCASTIFY_API_KEY`, `BROADCASTIFY_BASE_URL` |

Postcode lookups use the free [postcodes.io](https://postcodes.io) service.

## Install

```bash
git clone https://github.com/jon-humphries/uk-radio-mcp
cd uk-radio-mcp
uv venv && uv pip install -e .            # add ".[radioreference]" for the SOAP source
```

Add it to Claude Code:

```bash
claude mcp add uk-radio -- /path/to/uk-radio-mcp/.venv/bin/uk-radio-mcp
```

Or in an MCP client config:

```json
{
  "mcpServers": {
    "uk-radio": {
      "command": "/path/to/uk-radio-mcp/.venv/bin/uk-radio-mcp",
      "env": { "REPEATERBOOK_TOKEN": "rbuapp_...", "REPEATERBOOK_USER_AGENT": "..." }
    }
  }
}
```

## Static data and refresh

Static datasets download on first use into `~/.cache/uk-radio-mcp` and refresh automatically on a
later tool call once the cached copy is older than its interval. If a refresh fails, the stale copy
is used and the result says so.

| Dataset | Default refresh |
|---|---|
| Ofcom WTR.csv (about 54 MB) | 7 days |
| RadioID users.json (about 63 MB) | 24 hours |
| RepeaterBook responses | 1 hour |

| Variable | Purpose |
|---|---|
| `UK_RADIO_CACHE_DIR` | Cache location |
| `UK_RADIO_REFRESH_HOURS` | Overrides every refresh interval |
| `UK_RADIO_USER_AGENT` | User-Agent sent on downloads |

## Optional services

### With an API (set the variables to enable)

**RepeaterBook** (amateur repeaters, approval required)
- Request access: https://www.repeaterbook.com/api/token_request.php
- `REPEATERBOOK_TOKEN`: `app_...` for server use, or a per-user `rbuapp_...` token from https://www.repeaterbook.com/user/api_apps.php
- `REPEATERBOOK_USER_AGENT`: must match the approved app literally, or the API returns `403 ua_mismatch`
- Call: `GET https://www.repeaterbook.com/api/exportROW.php?country=United%20Kingdom` with header `X-RB-App-Token`. Needs scope `api.export_row`. Redirects are not followed.
- Personal, non-commercial use. Attribution: "Data courtesy of RepeaterBook.com".

**RadioReference** (SOAP, Premium subscription plus approved app key)
- Apply: https://www.radioreference.com/account/api/apply
- `RADIOREFERENCE_APP_KEY`, `RADIOREFERENCE_USERNAME`, `RADIOREFERENCE_PASSWORD` (your own login; credentials may not be shared)
- WSDL: `https://api.radioreference.com/soap2/?wsdl&v=latest&s=rpc`. Methods include `getCountyInfo(ctid)`, `getZipcodeInfo`, `getUserData`, `getCountyFreqsByTag`.
- Coverage is strongest in the US and Canada. UK data is limited.
- Install with `pip install -e ".[radioreference]"`.

**Broadcastify** (Developer Program, application reviewed)
- Apply: https://bcfy.io/dev/apply/ . Docs: https://bcfy.io/dev/docs/
- Live Audio Feed Catalog API: $2,500 per month. Calls Client API: prepaid, metered, $5 minimum.
- `BROADCASTIFY_API_KEY`, `BROADCASTIFY_BASE_URL`, optional `BROADCASTIFY_AUTH_HEADER`
- The public overview pages do not give endpoint paths or the auth header, and the docs site blocked automated access when this was written. `broadcastify_get` is therefore a passthrough: you give it a path from the official docs. It has not been tested against the live API.

**RadioID** (free) can take `RADIOID_API_TOKEN` (sent as `X-API-Token`). Without it, requests are anonymous. Its terms forbid mirroring, competing projects and commercial use.

### Subscriptions with no API

These sell file exports only, so there is nothing to call. Export from their sites and import into
your scanner software.

| Service | Price | Notes |
|---|---|---|
| [UKAFG](https://ukafg.co.uk/) | GBP 5 to 100 a year | CSV, XLSX, XML. The commercial licence forbids redistributing the raw data |
| [Radioreference UK](https://radioreferenceuk.co.uk/subscribe.php) | GBP 16 a year | 50 mile and 1,000 result caps |
| [ScanLocal UK](https://scanlocaluk.co.uk/subscribe) | GBP 5.99 first year, then 9.99 | Built from the same Ofcom data this server reads for free |

## Limits

- Ofcom withholds some licences, so absence from the register is not proof of no licence.
- The register gives frequency, site and emission code. It does not say which protocol (DMR, NXDN, analogue) is in use, and it holds no radio IDs.
- Listening is generally legal in the UK, but acting on or disclosing what you hear is restricted by the Wireless Telegraphy Act 2006.

## Development

```bash
uv pip install -e ".[dev]" && pytest
```

## Licence

MIT. Data from each source remains subject to that source's terms.
