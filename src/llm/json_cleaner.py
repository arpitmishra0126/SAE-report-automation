"""
LLM-based JSON cleaner for SAE extraction.
"""

from __future__ import annotations

import json
import logging

from llm.ollama_client import ask
from llm.prompts import (
    SYSTEM_PROMPT,
    build_sae_prompt,
)
from llm.response_parser import LLMResponseParser

logger = logging.getLogger(__name__)


class SAEJsonCleaner:
    """
    Uses Ollama to improve SAE extraction.
    """

    @staticmethod
    def improve(
        ocr_text: str,
        extracted_json: dict,
    ) -> dict:
        """
        Improve extracted SAE JSON using Ollama.

        Parameters
        ----------
        ocr_text : str
            OCR text from SAE pages.

        extracted_json : dict
            Regex extracted JSON.

        Returns
        -------
        dict
            Improved JSON.
        """

        try:

            prompt = build_sae_prompt(
                ocr_text,
                extracted_json,
            )

            response = ask(
                prompt=prompt,
                system=SYSTEM_PROMPT,
                temperature=0.0,
            )

            improved_json = LLMResponseParser.parse(
                response
            )

            logger.info(
                "LLM successfully improved SAE JSON."
            )

            return improved_json

        except Exception as e:

            logger.exception(
                "LLM cleanup failed. Using regex extraction instead."
            )

            logger.exception(e)

            # Never fail pipeline
            return extracted_json