import os
from collections.abc import AsyncGenerator

import anthropic
import openai

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

anthropic_client = (
    anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
)
openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

MODELS = {
    "claude-sonnet": "claude-sonnet-4-20250514",
    "claude-haiku": "claude-haiku-4-5-20251001",
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
}


def _openai_user_content(text: str, images: list[dict] | None):
    """OpenAI user content: plain string if no images, else a multimodal array."""
    if not images:
        return text
    content: list[dict] = [{"type": "text", "text": text}]
    for img in images:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{img['media_type']};base64,{img['data']}"},
            }
        )
    return content


def _anthropic_user_content(text: str, images: list[dict] | None):
    """Anthropic user content: plain string if no images, else a content-block array."""
    if not images:
        return text
    content: list[dict] = []
    for img in images:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img["media_type"],
                    "data": img["data"],
                },
            }
        )
    content.append({"type": "text", "text": text})
    return content


async def stream_generation(
    system_prompt: str,
    user_message: str,
    chat_history: list[dict],
    model: str = "gpt-4o",
    images: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    messages = [
        *chat_history,
        {"role": "user", "content": _anthropic_user_content(user_message, images)},
    ]

    if model.startswith("claude"):
        if not anthropic_client:
            raise ValueError("ANTHROPIC_API_KEY not set")
        model_id = MODELS.get(model, model)
        with anthropic_client.messages.stream(
            model=model_id,
            max_tokens=8000,
            system=system_prompt,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    elif model.startswith("gpt"):
        if not openai_client:
            raise ValueError("OPENAI_API_KEY not set")
        model_id = MODELS.get(model, model)
        messages = [
            *chat_history,
            {"role": "user", "content": _openai_user_content(user_message, images)},
        ]
        stream = await openai_client.chat.completions.create(
            model=model_id,
            max_tokens=8000,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            stream=True,
        )
        async for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                yield token

    else:
        raise ValueError(
            f"""Unknown model: {model}. Use claude-sonnet,
            claude-haiku, gpt-4o, or gpt-4o-mini"""
        )
