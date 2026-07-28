"""
Ollama client for interacting with local LLMs.
"""

from __future__ import annotations

import time

from src.reasoning.prompts import JSON_SCHEMA
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
    """

    print("\n" + "=" * 80)
    print("OLLAMA REQUEST")
    print("=" * 80)
    print(f"Model              : {MODEL_NAME}")
    print(f"Host               : {OLLAMA_HOST}")
    print(f"Temperature        : {temperature}")
    print(f"Prompt characters  : {len(prompt):,}")
    print(f"Approx. tokens     : {len(prompt) // 4:,}")

    if system:
        print(f"System prompt size : {len(system):,} characters")

    print("Output format      : JSON")
    print("=" * 80)

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

        print("Connecting to Ollama...")

        start = time.perf_counter()

        stream = _client.chat(
            model=MODEL_NAME,
            messages=messages,
            format="json",
            options={
                "temperature": temperature,
                 "num_ctx": 8192,
            },
            stream=True,
        )

        print("Connection established.")
        print("Waiting for first token...\n")
        print("-" * 80)

        chunks = []
        first_token = None

        for chunk in stream:

            if first_token is None:
                first_token = time.perf_counter()
                print(
                    f"\n\nFirst token after {first_token - start:.2f} sec\n"
                )

            text = chunk["message"]["content"]

            print(text, end="", flush=True)

            chunks.append(text)

        total = time.perf_counter() - start

        print("\n")
        print("-" * 80)
        print(f"Generation finished in {total:.2f} sec")

        content = "".join(chunks)

        print(f"Total response length : {len(content):,} characters")
        print("=" * 80)

        return content

    except ResponseError as e:

        raise RuntimeError(
            f"Ollama API Error: {e}"
        ) from e

    except Exception as e:

        raise RuntimeError(
            f"Failed to communicate with Ollama: {e}"
        ) from e