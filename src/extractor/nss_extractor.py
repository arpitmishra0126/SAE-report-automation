"""
Neonatal Sepsis Surveillance extractor.
"""

from __future__ import annotations

from form_segmenter.form import Form
from models.nss import NSSData
from utils.parser import TextParser

from .base import BaseExtractor


class NSSExtractor(BaseExtractor[NSSData]):
    """
    Extract structured information from the
    Neonatal Sepsis Screening REDCap form.
    """

    def __init__(self) -> None:
        self._parser = TextParser()

    def extract(self, form: Form) -> NSSData:
        """
        Extract Neonatal Sepsis Screening data.
        """

        text = "\n".join(page.text for page in form.pages)

        text = self._parser.normalize(text)

        data = NSSData()

        # -------------------------------------------------
        # Assessment
        # -------------------------------------------------

        data.assessment_date = self._parser.get_datetime(
            text,
            "Date of Neonatal Sepsis Screening",
        )

        # -------------------------------------------------
        # Diagnosis
        # -------------------------------------------------

        data.diagnosis = self._parser.get_multiline_value(
            text,
            "Diagnosis",
            "Culture",
        )

        # -------------------------------------------------
        # Culture Result
        # -------------------------------------------------

        data.culture_result = self._parser.get_multiline_value(
            text,
            "Culture",
            "Treatment",
        )

        # -------------------------------------------------
        # Treatment
        # -------------------------------------------------

        data.treatment = self._parser.get_multiline_value(
            text,
            "Treatment",
            "Outcome",
        )

        # -------------------------------------------------
        # Outcome
        # -------------------------------------------------

        data.outcome = self._parser.get_multiline_value(
            text,
            "Outcome",
            "Remarks",
        )

        # -------------------------------------------------
        # Remarks
        # -------------------------------------------------

        data.remarks = self._parser.get_value(
            text,
            "Remarks",
        )

        return data