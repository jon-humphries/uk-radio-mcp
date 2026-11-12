"""RadioReference Database Web Service (SOAP). Requires an approved application key
and a Premium subscription for the end user. Mostly US/Canada coverage; UK data is
limited, so treat this as an optional extra.

Env:
  RADIOREFERENCE_APP_KEY   application key (apply: https://www.radioreference.com/account/api/apply)
  RADIOREFERENCE_USERNAME  your own RadioReference username
  RADIOREFERENCE_PASSWORD  your own password (credentials must not be shared or pooled)
Install the extra: pip install "uk-radio-mcp[radioreference]"
WSDL: https://api.radioreference.com/soap2/?wsdl&v=latest&s=rpc
"""
from __future__ import annotations

import os

WSDL = "https://api.radioreference.com/soap2/?wsdl&v=latest&s=rpc"
ENV = ("RADIOREFERENCE_APP_KEY", "RADIOREFERENCE_USERNAME", "RADIOREFERENCE_PASSWORD")


def configured() -> bool:
    return all(os.environ.get(k) for k in ENV)


def missing_message() -> str:
    return (
        "RadioReference is not configured. Set RADIOREFERENCE_APP_KEY, RADIOREFERENCE_USERNAME "
        "and RADIOREFERENCE_PASSWORD (Premium subscription and approved app key required)."
    )


def _client():
    try:
        from zeep import Client
        from zeep.helpers import serialize_object  # noqa: F401
    except ImportError as exc:
        raise RuntimeError('Install the extra: pip install "uk-radio-mcp[radioreference]"') from exc
    return Client(WSDL)


def _auth() -> dict:
    return {
        "appKey": os.environ["RADIOREFERENCE_APP_KEY"],
        "username": os.environ["RADIOREFERENCE_USERNAME"],
        "password": os.environ["RADIOREFERENCE_PASSWORD"],
        "version": "latest",
        "style": "rpc",
    }


def call(method: str, **params):
    """Call any Web Service method, e.g. call('getCountyInfo', ctid=1234)."""
    from zeep.helpers import serialize_object

    client = _client()
    fn = getattr(client.service, method)
    return serialize_object(fn(**params, authInfo=_auth()), dict)
