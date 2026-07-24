"""
Ollama client for interacting with local LLMs.
"""

from __future__ import annotations

from ollama import Client, ResponseError

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "qwen3:8b"

_client = Client(host=OLLAMA_HOST)


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def ask(
    prompt: str,
    *,
    system: str | None = None,
    temperature: float = 0.0,
) -> str:
    """
    Send a prompt to Ollama and return the model response.

    Parameters
    ----------
    prompt : str
        User prompt.

    system : str | None
        Optional system prompt.

    temperature : float
        Model creativity.
        0.0 = deterministic (recommended for extraction)

    Returns
    -------
    str
        Raw model response.
    """

    messages = []

    if system:
        messages.append(
            {
                "role": "system",
                "content": system,
            }
        )

    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    try:

        response = _client.chat(
            model=MODEL_NAME,
            messages=messages,
            options={
                "temperature": temperature,
            },
        )

        return response["message"]["content"]

    except ResponseError as e:
        raise RuntimeError(
            f"Ollama API Error: {e}"
        ) from e

    except Exception as e:
        raise RuntimeError(
            f"Failed to communicate with Ollama: {e}"
        ) from e