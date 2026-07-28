"""
report_validator.py

Validation and normalization for AI-generated clinical reports.

This module ensures that the LLM output conforms to the
ClinicalReport schema before being passed to downstream
components such as the DOCX generator.
"""

from __future__ import annotations

from typing import Any, Dict

from .report import ClinicalReport


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

        return str(value)

    @staticmethod
    def _as_list(value: Any):
        """
        Ensure value is a list.
        """

        if value is None:
            return []

        if isinstance(value, list):
            return value

        return [value]

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