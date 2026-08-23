import os
import ollama
from groq import Groq
from app.config import (
    MODEL_PROVIDER,
    OLLAMA_MODEL_NAME,
    GROQ_API_KEY,
    GROQ_MODEL_NAME,
)


def generate(
    prompt: str,
    model: str | None = None,
    system: str | None = None,
    format: str | None = None,
) -> str:
    """
    Generate text using the configured provider.
    """
    if MODEL_PROVIDER == "groq":
        return _generate_groq(prompt, model, system, format)
    else:
        return _generate_ollama(prompt, model, system, format)


def _generate_ollama(prompt, model=None, system=None, format=None):
    model = model or OLLAMA_MODEL_NAME
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if format:
        kwargs["format"] = format

    response = ollama.chat(**kwargs)
    return response["message"]["content"]


def _generate_groq(prompt, model=None, system=None, format=None):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Please check your .env file.")

    model = model or GROQ_MODEL_NAME
    client = Groq(api_key=GROQ_API_KEY)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
    }

    # For JSON mode, force the model to output plain JSON,
    # not native function calls.
    if format == "json":
        kwargs["response_format"] = {"type": "json_object"}
        

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content

            if content and content.strip():
                # Strip any accidental <think> blocks (not expected)
                if "</think>" in content:
                    content = content.split("</think>")[-1].strip()
                return content

            # Empty content, retry
            continue

        except Exception as e:
            error_str = str(e)

            # If JSON mode failed, retry without response_format
            if "json_validate_failed" in error_str and "response_format" in kwargs:
                kwargs.pop("response_format", None)
                continue

            # If tool_choice caused an error, remove it and retry
            if "tool_choice" in error_str and "tool_choice" in kwargs:
                kwargs.pop("tool_choice", None)
                kwargs.pop("tools", None)
                continue

            if attempt == max_retries - 1:
                raise e

            # Optional: small delay before retry
            # import time; time.sleep(0.5)

    return "The model returned an empty response. Please try again."