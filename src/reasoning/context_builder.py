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

    def __init__(self):
        self.context: Dict[str, Any] = {
            "patient": {},
            "clinical_story": {},
            "metadata": {}
        }

    def build(self, record: PatientRecord) -> Dict[str, Any]:

        data = deepcopy(record.to_dict())

        self.context["patient"] = data

        self.context["clinical_story"] = {
            "events": [],
            "diagnoses": [],
            "treatments": [],
            "investigations": [],
            "observations": [],
            "outcome": {},
            "missing_information": [],
            "quality_flags": []
        }

        self.context["metadata"] = data.get("metadata", {})

        return self.context