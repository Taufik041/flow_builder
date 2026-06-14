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


async def stream_generation(
    system_prompt: str,
    user_message: str,
    chat_history: list[dict],
    model: str = "gpt-4o",
) -> AsyncGenerator[str, None]:
    messages = [
        *chat_history,
        {"role": "user", "content": user_message},
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
