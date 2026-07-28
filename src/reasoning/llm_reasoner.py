from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any

from llm.ollama_client import ask

from .prompts import SYSTEM_PROMPT, build_report_prompt
from .report import ClinicalReport
from .report_validator import ReportValidator


class LLMReasoner:
    """
    AI reasoning engine for generating structured clinical reports.
    """

    def __init__(
        self,
        temperature: float = 0.2,
    ):
        self.temperature = temperature

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def generate_report(
        self,
        context: Dict[str, Any],
    ) -> ClinicalReport:
        """
        Generate a structured clinical report.
        """

        print("\n" + "=" * 80)
        print("BUILDING REPORT PROMPT")
        print("=" * 80)

        print(f"Context size: {len(json.dumps(context)):,} characters")
        prompt = build_report_prompt(context)

        print(f"Prompt Length : {len(prompt):,} characters")

        response = ask(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            temperature=self.temperature,
        )

        data = self._parse_response(response)

        print("\n✓ JSON parsed successfully.")
        print("✓ Validating clinical report...")

        return ReportValidator.validate(data)

    # ---------------------------------------------------------
    # Internal Helpers
    # ---------------------------------------------------------

    def _parse_response(self, response: str) -> dict:
        """
        Parse JSON returned by the LLM.

        This method is intentionally robust because local LLMs often return:

        - Markdown fences
        - Introductory text
        - Trailing explanations
        - Invalid formatting
        """

        Path("logs").mkdir(exist_ok=True)

        raw_file = Path("logs") / "llm_raw_response.txt"

        with open(raw_file, "w", encoding="utf-8") as f:
            f.write(response)

        print("\n" + "=" * 80)
        print("RAW RESPONSE SAVED")
        print(raw_file)
        print("=" * 80)

        if response is None:
            raise ValueError("LLM returned None.")

        response = response.strip()

        if not response:
            raise ValueError("LLM returned an empty response.")

        print("\nFirst 500 characters:\n")
        print(response[:500])
        print("\n" + "=" * 80)

        # -----------------------------------------------------
        # Remove Markdown Code Fences
        # -----------------------------------------------------

        response = re.sub(
            r"^```json\s*",
            "",
            response,
            flags=re.IGNORECASE,
        )

        response = re.sub(
            r"^```",
            "",
            response,
        )

        response = re.sub(
            r"```$",
            "",
            response,
        )

        response = response.strip()

        # -----------------------------------------------------
        # Locate JSON
        # -----------------------------------------------------

        start = response.find("{")
        end = response.rfind("}")

        if start == -1 or end == -1 or end <= start:

            print("\nNo JSON object detected.")
            print("Please inspect:")
            print(raw_file)

            raise ValueError(
                "LLM response did not contain a JSON object."
            )

        json_text = response[start:end + 1]

        cleaned_file = Path("logs") / "llm_cleaned.json"

        with open(cleaned_file, "w", encoding="utf-8") as f:
            f.write(json_text)

        print("Cleaned JSON saved to:")
        print(cleaned_file)

        # -----------------------------------------------------
        # Parse JSON
        # -----------------------------------------------------

        try:
            parsed = json.loads(json_text)

            print("\n✓ JSON successfully decoded.")

            return parsed

        except json.JSONDecodeError as e:

            print("\n" + "=" * 80)
            print("JSON PARSE FAILED")
            print("=" * 80)

            print(e)

            print("\nInspect these files:")

            print(raw_file)
            print(cleaned_file)

            raise