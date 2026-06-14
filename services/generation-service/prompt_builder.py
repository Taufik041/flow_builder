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


def build_system_prompt(chunks: list[dict]) -> str:
    retrieved = "\n\n---\n\n".join(
        f"[{c['source']}] {c['title']}\n{c['text']}" for c in chunks
    )
    examples = load_examples()

    return f"""You are a WhatsApp Flows generator. You take a form description
(from text, PDF, or image) and generate:
1. A complete WhatsApp Flow JSON (version 7.3 by default, 7.1 if user specifies)
2. A complete FastAPI backend handler

## CRITICAL RULES
- Never hallucinate. If you don't have context for something, leave a TODO placeholder.
- Never invent component properties, action names, or API calls.
- Every pattern you use must come from the knowledge base or examples below.
- Accuracy over completeness — a clean TODO is better than a confident wrong answer.

## TODO PLACEHOLDERS
- Unknown API call: `# TODO: call API to get {{field}} data`
- Unknown message key: `get_all_messages("TODO_KEY", user_language)`
- Unknown business logic: `# TODO: add logic here`
- Unknown screen fields: screen stub with `# TODO: add components`

## KNOWLEDGE BASE
{retrieved}

## EXAMPLES (use these as structural references)
{examples}

## OUTPUT FORMAT
Output exactly two code blocks:
1. ```json ... ``` — the complete Flow JSON
2. ```python ... ``` — the complete FastAPI backend handler

After the code blocks, briefly explain any TODOs you left and why.
"""


def build_user_message(user_input: str, extracted_text: str | None = None) -> str:
    if extracted_text:
        return f"""Form content extracted from uploaded file:

{extracted_text}

User instruction: {user_input}

Generate the WhatsApp Flow JSON and FastAPI backend handler for this form."""
    return f"""{user_input}

Generate the WhatsApp Flow JSON and FastAPI backend handler for this."""
