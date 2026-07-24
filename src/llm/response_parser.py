"""
Utilities for parsing LLM responses.
"""

from __future__ import annotations

import json
import re


class LLMResponseParser:
    """
    Parses Ollama responses into Python dictionaries.

    Handles:
    - Markdown code fences
    - <think>...</think> blocks (Qwen)
    - Extra explanatory text
    - Plain JSON responses
    """

    @staticmethod
    def parse(response: str) -> dict:
        """
        Parse an Ollama response and return a Python dictionary.

        Parameters
        ----------
        response : str
            Raw response from Ollama.

        Returns
        -------
        dict
            Parsed JSON object.

        Raises
        ------
        ValueError
            If no valid JSON object is found.
        """

        if not response:
            raise ValueError("Empty response from Ollama.")

        response = response.strip()

        # ---------------------------------------------------------
        # Remove Qwen thinking block
        # ---------------------------------------------------------
        response = re.sub(
            r"<think>.*?</think>",
            "",
            response,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # ---------------------------------------------------------
        # Remove Markdown code fences
        # ---------------------------------------------------------
        response = re.sub(
            r"```json",
            "",
            response,
            flags=re.IGNORECASE,
        )

        response = response.replace("```", "")

        response = response.strip()

        # ---------------------------------------------------------
        # Extract first JSON object
        # ---------------------------------------------------------
        match = re.search(
            r"\{.*\}",
            response,
            flags=re.DOTALL,
        )

        if not match:
            raise ValueError(
                f"No JSON object found in response:\n\n{response}"
            )

        json_text = match.group()

        # ---------------------------------------------------------
        # Parse JSON
        # ---------------------------------------------------------
        try:
            return json.loads(json_text)

        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON returned by Ollama:\n\n{json_text}"
            ) from e
        