from pathlib import Path

KNOWLEDGE_DIR = "/knowledge"


def load_examples() -> str:
    examples_dir = Path(KNOWLEDGE_DIR) / "examples"
    if not examples_dir.exists():
        return "# No examples available"
    parts = []
    for f in sorted(examples_dir.glob("*.md")):
        parts.append(f.read_text(encoding="utf-8"))
    return "\n\n".join(parts) if parts else "# No examples available"


def _common_header(retrieved: str, examples: str) -> str:
    return f"""You are a WhatsApp Flows generator. You take a form description
(from text, PDF, or image) and generate WhatsApp Flows artifacts.

## CRITICAL RULES
- Never hallucinate. If you don't have context for something, leave a TODO placeholder.
- Never invent component properties, action names, or API calls.
- Every pattern you use must come from the knowledge base or examples below.
- Accuracy over completeness — a clean TODO is better than a confident wrong answer.

## KNOWLEDGE BASE
{retrieved}

## EXAMPLES (use these as structural references)
{examples}
"""


def build_system_prompt(chunks: list[dict], phase: str = "json") -> str:
    """phase='json'    -> generate ONLY the Flow JSON (phase 1, the validated loop)
    phase='backend' -> generate ONLY the FastAPI handler for an already-final JSON
    phase='both'    -> legacy single-shot (JSON + Python together)
    """
    retrieved = "\n\n---\n\n".join(
        f"[{c['source']}] {c['title']}\n{c['text']}" for c in chunks
    )
    examples = load_examples()
    header = _common_header(retrieved, examples)

    if phase == "json":
        return (
            header
            + """
## OUTPUT FORMAT (PHASE 1 — JSON ONLY)
Output EXACTLY ONE code block: the complete Flow JSON.
```json ... ```
Do NOT generate any Python or backend code in this phase. The backend handler is
generated in a separate later step, after this JSON is validated. Output only the
JSON block, then (optionally) one or two sentences noting any TODOs in the JSON.
"""
        )

    if phase == "backend":
        return (
            header
            + """
## TODO PLACEHOLDERS
- Unknown API call: `# TODO: call API to get {field} data`
- Unknown message key: `get_all_messages("TODO_KEY", user_language)`
- Unknown business logic: `# TODO: add logic here`

## OUTPUT FORMAT (PHASE 2 — BACKEND ONLY)
You are given a FINAL, validated Flow JSON. Generate the complete FastAPI backend
handler that serves exactly that flow. The handler's triggers, footers, screen ids,
and submit key MUST match the provided JSON precisely — do not invent screens or
fields that aren't in it, and handle every trigger/footer the JSON references.
Output EXACTLY ONE code block:
```python ... ```
After the code block, briefly explain any TODOs you left and why.
"""
        )

    # phase == "both" (legacy)
    return (
        header
        + """
## TODO PLACEHOLDERS
- Unknown API call: `# TODO: call API to get {field} data`
- Unknown message key: `get_all_messages("TODO_KEY", user_language)`
- Unknown business logic: `# TODO: add logic here`
- Unknown screen fields: screen stub with `# TODO: add components`

## OUTPUT FORMAT
Output exactly two code blocks:
1. ```json ... ``` — the complete Flow JSON
2. ```python ... ``` — the complete FastAPI backend handler
After the code blocks, briefly explain any TODOs you left and why.
"""
    )


def build_user_message(user_input: str, extracted_text: str | None = None) -> str:
    if extracted_text:
        return f"""Form content extracted from uploaded file:

{extracted_text}

User instruction: {user_input}

Generate the WhatsApp Flow JSON for this form."""
    return f"""{user_input}

Generate the WhatsApp Flow JSON for this."""


def build_backend_user_message(final_flow_json: str) -> str:
    """Phase 2 user message — hand the model the final validated JSON."""
    return f"""Here is the FINAL, validated Flow JSON. Generate the complete FastAPI
backend handler that serves exactly this flow:

```json
{final_flow_json}
```

Generate ONLY the FastAPI backend handler for this flow."""
