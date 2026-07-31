"""
report_validator.py

Validation and normalization for AI-generated clinical reports.

This module ensures that the LLM output conforms to the
ClinicalReport schema before being passed to downstream
components such as the DOCX generator.
"""

from __future__ import annotations

import re
from typing import Any, Dict

from .report import ClinicalReport


# Patterns the LLM can still slip through despite prompt instructions —
# the same PDF-viewer/REDCap chrome and bracket-fragment noise that
# TextParser strips upstream. A final scrub before the report is
# handed to the DOCX generator is cheap insurance against a model
# that didn't fully comply.
_CONTAMINATION_PATTERNS = [
    r"\d{1,2}/\d{1,2}/\d{2,4},?\s*\d{1,2}:\d{2}\s*(AM|PM)",
    r"ICMR Emollient[^\n]*\|\s*REDCap",
    r"https?://\S+",
    r"\[[^\]]*$",  # an unclosed "[..." translation fragment
]

_CONTAMINATION_RE = re.compile(
    "|".join(f"(?:{p})" for p in _CONTAMINATION_PATTERNS),
    flags=re.IGNORECASE,
)


class ReportValidator:
    """
    Validate and normalize report JSON returned by the LLM.
    """

    @staticmethod
    def validate(data: Dict[str, Any]) -> ClinicalReport:
        """
        Validate and normalize the LLM response.

        Parameters
        ----------
        data : dict
            Raw JSON returned by the reasoning engine.

        Returns
        -------
        ClinicalReport
            Validated report object.
        """

        if not isinstance(data, dict):
            raise TypeError(
                "LLM response must be a dictionary."
            )

        return ClinicalReport(

            executive_summary=ReportValidator._as_string(
                data.get("executive_summary")
            ),

            maternal_history=ReportValidator._as_string(
                data.get("maternal_history")
            ),

            clinical_timeline=ReportValidator._as_list(
                data.get("clinical_timeline")
            ),

            daily_clinical_monitoring=ReportValidator._as_list(
                data.get("daily_clinical_monitoring")
            ),

            neonatal_sepsis=ReportValidator._as_list(
                data.get("neonatal_sepsis")
            ),

            laboratory_findings=ReportValidator._as_list(
                data.get("laboratory_findings")
            ),

            final_outcome=ReportValidator._as_string(
                data.get("final_outcome")
            ),

            quality_flags=ReportValidator._as_list(
                data.get("quality_flags")
            ),

            metadata=ReportValidator._as_dict(
                data.get("metadata")
            ),
        )

    # ---------------------------------------------------------
    # Helper methods
    # ---------------------------------------------------------

    @staticmethod
    def _as_string(value: Any) -> str:
        """
        Convert value to string.
        """

        if value is None:
            return ""

        return ReportValidator._scrub(str(value))

    @staticmethod
    def _scrub(value: str) -> str:
        """
        Strip PDF-viewer/REDCap chrome and bracket fragments that the
        model may have copied through despite being told not to.
        """

        cleaned = _CONTAMINATION_RE.sub("", value)

        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)

        return cleaned.strip()

    @staticmethod
    def _as_list(value: Any):
        """
        Ensure value is a list, scrubbing any string content inside it.
        """

        if value is None:
            return []

        if not isinstance(value, list):
            value = [value]

        return [ReportValidator._scrub_nested(item) for item in value]

    @staticmethod
    def _scrub_nested(value: Any) -> Any:

        if isinstance(value, str):
            return ReportValidator._scrub(value)

        if isinstance(value, list):
            return [ReportValidator._scrub_nested(v) for v in value]

        if isinstance(value, dict):
            return {
                k: ReportValidator._scrub_nested(v)
                for k, v in value.items()
            }

        return value

    @staticmethod
    def _as_dict(value: Any):
        """
        Ensure value is a dictionary.
        """

        if value is None:
            return {}

        if isinstance(value, dict):
            return value

        return {}