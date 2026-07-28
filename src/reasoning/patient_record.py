"""
patient_record.py

Builds a unified patient record from all extracted forms.

This module contains NO LLM logic.
It only consolidates extracted information into one
normalized structure that downstream reasoning modules use.
"""

from typing import Any, Dict, List


class PatientRecord:
    """
    Unified AI-ready representation of a patient's complete case.

    This class serves as the bridge between the extraction pipeline
    (CaseSummary) and the reasoning pipeline (ContextBuilder -> LLM).
    """

    def __init__(self):

        self.data = {

            # ----------------------------
            # Core extracted forms
            # ----------------------------

            "patient": {},

            "maternal": {},

            "sae": {},

            "dcm": [],

            "nss": [],

            "lab": [],

            # ----------------------------
            # Derived application data
            # ----------------------------

            "timeline": [],

            "validation_messages": [],

            # ----------------------------
            # Metadata
            # ----------------------------

            "metadata": {}
        }

    # ==========================================================
    # Core extracted data
    # ==========================================================

    def set_patient(self, patient: Dict[str, Any]):

        self.data["patient"] = patient

    def set_maternal(self, maternal: Dict[str, Any]):

        self.data["maternal"] = maternal

    def set_sae(self, sae: Dict[str, Any]):

        self.data["sae"] = sae

    def add_dcm(self, dcm: Dict[str, Any]):

        self.data["dcm"].append(dcm)

    def add_nss(self, nss: Dict[str, Any]):

        self.data["nss"].append(nss)

    def add_lab(self, lab: Dict[str, Any]):

        self.data["lab"].append(lab)

    # ==========================================================
    # Derived data
    # ==========================================================

    def set_timeline(self, timeline: List[Any]):

        self.data["timeline"] = timeline

    def set_validation_messages(self, messages: List[str]):

        self.data["validation_messages"] = messages

    # ==========================================================
    # Metadata
    # ==========================================================

    def set_metadata(self, metadata: Dict[str, Any]):

        self.data["metadata"] = metadata

    # ==========================================================
    # Access
    # ==========================================================

    def to_dict(self) -> Dict[str, Any]:

        return self.data

    def get(self) -> Dict[str, Any]:

        return self.data