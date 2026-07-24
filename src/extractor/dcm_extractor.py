"""
Daily Clinical Monitoring extractor.
"""

from __future__ import annotations

from form_segmenter.form import Form
from models.dcm import DCMData
from utils.parser import TextParser

from .base import BaseExtractor


class DCMExtractor(BaseExtractor[DCMData]):
    """
    Extract structured information from the
    Daily Clinical Monitoring REDCap form.
    """

    def __init__(self) -> None:
        self._parser = TextParser()

    def extract(self, form: Form) -> DCMData:
        """
        Extract Daily Clinical Monitoring data.
        """

        text = "\n".join(page.text for page in form.pages)

        text = self._parser.normalize(text)

        data = DCMData()

        # -------------------------------------------------
        # Monitoring Information
        # -------------------------------------------------

        data.monitoring_date = self._parser.get_datetime(
            text,
            "Date of Clinical Monitoring",
        )

        # -------------------------------------------------
        # Vital Status
        # -------------------------------------------------

        data.vital_status = self._parser.get_value(
            text,
            "What is the current vital status of the newborn?",
        )

        # -------------------------------------------------
        # Baby Weight
        # -------------------------------------------------

        weight = self._parser.get_number(
            text,
            "Measure the weight of the newborn",
        )

        if weight is not None:
            data.weight = float(weight)

        # -------------------------------------------------
        # Medication
        # -------------------------------------------------

        data.medications = self._parser.get_multiline_value(
            text,
            "Please check the file and state all the medicines the newborn is being prescribed.",
            "Section F",
        )

        # -------------------------------------------------
        # Feeding
        # -------------------------------------------------

        data.feeding = self._parser.get_multiline_value(
            text,
            "What was the newborn fed in the last 24 hours?",
            "Section H",
        )

        # -------------------------------------------------
        # Remarks
        # -------------------------------------------------

        data.remarks = self._parser.get_value(
            text,
            "16 - Remarks",
        )

        return data