import ollama
from app.config import MODEL_NAME

def generate(prompt: str, model: str = MODEL_NAME, system: str | None = None, format: str | None = None):
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