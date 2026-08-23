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
        "temperature": 0.2,
    }

    # Try to disable reasoning for Qwen models (may not be supported)
    if "qwen3.6" in model:
        kwargs["reasoning"] = {"enabled": False}

    if format == "json":
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
    except Exception as e:
        # If reasoning parameter caused an error, retry without it
        if "reasoning" in kwargs:
            kwargs.pop("reasoning")
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
        else:
            raise e

    # ── Simple and reliable stripping of chain-of-thought ──
    if "</think>" in content:
        # Keep everything after the LAST </think> tag
        content = content.split("</think>")[-1].strip()
    elif "<think>" in content:
        # If only opening tag (unlikely), remove from there
        content = content.split("<think>")[0].strip()

    return content