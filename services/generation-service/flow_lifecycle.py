"""Helpers for the generate -> validate -> repair -> preview loop.

Pure functions (no I/O) so they're trivially unit-testable. The AiSensy calls
live in aisensy_client.py; the orchestration lives in main.py's stream.
"""

import json
import os
import re
import uuid

# Endpoint convention:  https://{host}/api/v1/flow/{service}/{service}
# Host (and port) come from env so it's not hardcoded per deployment.
FLOW_ENDPOINT_HOST = os.getenv("FLOW_ENDPOINT_HOST", "whatsapp.bipros.com:10443")
FLOW_ENDPOINT_PREFIX = os.getenv("FLOW_ENDPOINT_PREFIX", "/api/v1/flow")

_JSON_BLOCK = re.compile(r"```json\s*(.*?)```", re.DOTALL)
_PY_BLOCK = re.compile(r"```python\s*(.*?)```", re.DOTALL)
_SLUG = re.compile(r"[^a-z0-9]+")


def extract_json_block(text: str) -> str | None:
    """Return the raw text of the last ```json ...``` block, or None."""
    matches = _JSON_BLOCK.findall(text)
    return matches[-1].strip() if matches else None


def extract_python_block(text: str) -> str | None:
    matches = _PY_BLOCK.findall(text)
    return matches[-1].strip() if matches else None


def parse_flow_json(text: str) -> dict | None:
    """Extract + parse the JSON block. Returns None if missing or unparseable."""
    raw = extract_json_block(text)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def slugify(text: str, max_len: int = 30) -> str:
    s = _SLUG.sub("-", text.lower()).strip("-")
    return s[:max_len].strip("-") or "flow"


def build_flow_name(user_message: str, provided_name: str | None = None) -> str:
    """Identifiable + globally-unique. User name if given, else derived; always
    uuid-suffixed because AiSensy requires unique names per WABA."""
    base = slugify(provided_name) if provided_name else slugify(user_message)
    return f"{base}_{uuid.uuid4().hex[:8]}"


def build_default_endpoint_uri(service: str) -> str:
    """https://{host}{prefix}/{service}/{service}"""
    service = slugify(service)
    return f"https://{FLOW_ENDPOINT_HOST}{FLOW_ENDPOINT_PREFIX}/{service}/{service}"


def guess_service_name(flow_json: dict | None, user_message: str) -> str:
    """Best-guess service slug for the endpoint URL. Prefer a hint from the
    flow's first screen id, else derive from the prompt."""
    if flow_json:
        screens = flow_json.get("screens", [])
        if screens:
            first_id = screens[0].get("id", "")
            if first_id:
                return slugify(first_id)
    return slugify(user_message)


def format_errors_for_retry(validation_errors: list[dict]) -> str:
    """Turn AiSensy/Meta validation_errors into a compact, model-readable list."""
    lines = []
    for e in validation_errors:
        pointers = e.get("pointers") or [{}]
        path = pointers[0].get("path", "?")
        code = e.get("error", "ERROR")
        msg = e.get("message", "")
        lines.append(f"- [{code}] {msg} (at {path})")
    return "\n".join(lines)


def build_repair_prompt(flow_json: dict, validation_errors: list[dict]) -> str:
    """User-message for a repair attempt. Feeds Meta's exact errors back."""
    return (
        "The Flow JSON you generated failed Meta's validation with these "
        "errors:\n\n"
        + format_errors_for_retry(validation_errors)
        + "\n\nFix ONLY these errors. Keep everything else identical. "
        + "Return the COMPLETE corrected Flow JSON, not a diff."
        + "\n\nCurrent Flow JSON:\n```json\n"
        + json.dumps(flow_json, indent=2)
        + "\n```"
    )
