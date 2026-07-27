"""
patient_record.py

Builds a unified patient record from all extracted forms.

This module contains NO LLM logic.
It only consolidates extracted information into one
normalized structure that downstream reasoning modules use.
"""

from typing import Any, Dict, List


class PatientRecord:

    def __init__(self):

        self.data = {

            "patient": {},

            "maternal": {},

            "sae": {},

            "dcm": [],

            "nss": [],

            "lab": [],

            "metadata": {}
        }

    # ----------------------------
    # Basic setters
    # ----------------------------

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

    def set_metadata(self, metadata: Dict[str, Any]):

        self.data["metadata"] = metadata

    # ----------------------------
    # Access
    # ----------------------------

    def to_dict(self):

        return self.data

    def get(self):

        return self.data