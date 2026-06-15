"""AiSensy BSP client — full WhatsApp Flow lifecycle.

Owns the AiSensy bearer token (from env, never hardcoded) and the draft-flow
draft validation behaviour. Lives inside generation-service, which is the only
service that talks to AiSensy.

Operations (mirror the 6 standalone scripts):
    create_flow(name, category)            -> {"id", "validation_errors", ...}
    update_flow_json(flow_id, flow_json)   -> {"validation_errors": [...]} (validates)
    get_preview(flow_id)                   -> preview_url | None
    set_endpoint(flow_id, endpoint_uri)    -> raw json
    publish_flow(flow_id)                  -> raw json
    list_flows()                           -> raw json   (debug/helper)
"""

import json
import os

import httpx

AISENSY_TOKEN = os.environ["AISENSY_TOKEN"]
BASE_URL = os.getenv(
    "AISENSY_BASE_URL", "https://backend.aisensy.com/direct-apis/t1/flows"
)

# Meta's fixed category enum. Anything the user doesn't provide falls back to OTHER.
VALID_CATEGORIES = {
    "SIGN_UP",
    "SIGN_IN",
    "APPOINTMENT_BOOKING",
    "LEAD_GENERATION",
    "CONTACT_US",
    "CUSTOMER_SUPPORT",
    "SURVEY",
    "OTHER",
}
DEFAULT_CATEGORY = "OTHER"

_TIMEOUT = httpx.Timeout(30.0)


def _headers(json_content: bool = False) -> dict:
    h = {
        "Accept": "application/json",
        "Authorization": f"Bearer {AISENSY_TOKEN}",
    }
    if json_content:
        h["Content-Type"] = "application/json"
    return h


def _normalize_category(category: str | None) -> str:
    if category and category.upper() in VALID_CATEGORIES:
        return category.upper()
    return DEFAULT_CATEGORY


async def create_flow(name: str, category: str | None = None) -> dict:
    """Create a new flow shell. Returns the raw response including 'id'.

    On name collision AiSensy returns an OAuthException with error_subcode
    4016019 — the caller should retry with a more unique name. We uuid-suffix
    names upstream so this should not normally happen.
    """
    payload = {"name": name, "categories": [_normalize_category(category)]}
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            BASE_URL, json=payload, headers=_headers(json_content=True)
        )
    return resp.json()


async def update_flow_json(flow_id: str, flow_json: dict) -> dict:
    """Overwrite the flow's JSON asset. This is the VALIDATION step.

    Returns the raw response; the important field is 'validation_errors'
    (empty list == valid). Uploading also persists the JSON on the draft flow,
    which is what makes the preview reflect the latest push.
    """
    json_string = json.dumps(flow_json)
    files = {"file": ("data.json", json_string, "application/json")}
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{BASE_URL}/{flow_id}/assets", files=files, headers=_headers()
        )
    return resp.json()


async def get_preview(flow_id: str) -> str | None:
    """Fetch the hosted Meta preview URL for the current draft JSON."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/{flow_id}/web-preview", headers=_headers())
    data = resp.json()
    return (data.get("preview") or {}).get("preview_url")


async def set_endpoint(flow_id: str, endpoint_uri: str) -> dict:
    """Set the flow's data-exchange endpoint_uri (step 5)."""
    payload = {"endpoint_uri": endpoint_uri}
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.patch(
            f"{BASE_URL}/{flow_id}", json=payload, headers=_headers(json_content=True)
        )
    return resp.json()


async def publish_flow(flow_id: str) -> dict:
    """Publish the flow (step 6)."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{BASE_URL}/{flow_id}/publish", headers=_headers(json_content=True)
        )
    return resp.json()


async def list_flows() -> dict:
    """List all flows on the WABA (debug/helper)."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(BASE_URL, headers=_headers())
    return resp.json()
