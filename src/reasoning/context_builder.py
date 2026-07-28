"""
context_builder.py

Transforms a PatientRecord into a reasoning-ready context.

This module performs NO summarization.
It simply organizes extracted information so the LLM receives
clean, structured, and consistent input.

The output of this module is called a Reasoning Context.
"""

from copy import deepcopy
from typing import Any, Dict

from .patient_record import PatientRecord


class ContextBuilder:

    def build(self, record: PatientRecord) -> Dict[str, Any]:
        """
        Build a structured reasoning context from a PatientRecord.
        """

        data = deepcopy(record.to_dict())

        context = {
            "patient": {
                "patient": data.get("patient", {}),
                "maternal": data.get("maternal", {})
            },

            "clinical_story": {

                # Raw extracted forms
                "sae": data.get("sae", {}),
                "daily_clinical_monitoring": data.get("dcm", []),
                "neonatal_sepsis": data.get("nss", []),
                "laboratory_findings": data.get("lab", []),

                # AI-friendly sections (initially empty)
                "events": [],
                "diagnoses": [],
                "treatments": [],
                "investigations": [],
                "observations": [],
                "outcome": {},
                "missing_information": [],
                "quality_flags": []
            },

            "metadata": data.get("metadata", {})
        }

        return context