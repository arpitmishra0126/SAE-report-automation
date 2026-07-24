"""
SAE form extractor.
"""

from __future__ import annotations
import datetime
from form_segmenter.form import Form
from models.sae import SAEData
from utils.parser import TextParser

from .base import BaseExtractor


class SAEExtractor(BaseExtractor[SAEData]):
    """
    Extract structured information from the
    Serious Adverse Event (SAE) REDCap form.
    """

    def __init__(self) -> None:
        self._parser = TextParser()

    def extract(self, form: Form) -> SAEData:
        """
        Extract structured SAE data.
        """

        text = "\n".join(page.text for page in form.pages)

        text = self._parser.normalize(text)

        data = SAEData()

        # -------------------------------------------------
        # Case Information
        # -------------------------------------------------

        data.record_id = self._parser.get_value(
            text,
            "Record ID",
        )

        data.participant_id = self._parser.get_value(
            text,
            "Enrolled Baby's UID",
        )

        data.site = self._parser.get_value(
            text,
            "Hospital Name",
        )

        # -------------------------------------------------
        # Hospital Information
        # -------------------------------------------------

        data.hospital_name = self._parser.get_value(
            text,
            "Hospital Name",
        )

        data.admission_date = self._parser.get_datetime(
            text,
            "Enrollment Date",
        )

        # -------------------------------------------------
        # SAE Information
        # -------------------------------------------------

        data.event_date = self._parser.get_date(
            text,
            "Please indicate the date when the adverse event started",
        )

        data.outcome = self._parser.get_value(
            text,
            "Please describe the outcome of the event",
        )

        data.cause_of_death = self._parser.get_multiline_value(
            text,
            "If yes, state the underlying cause of death",
            "Please describe the events leading up to the SAE",
        )

        data.event_description = self._parser.get_multiline_value(
            text,
            "Please describe the events leading up to the SAE",
            "Please provide any relevant past medical",
        )

        data.diagnosis = self._parser.get_multiline_value(
            text,
            "Please provide any other relevant clinical information",
            "Please enter any additional comments",
        )

        # -------------------------------------------------
        # Reporter
        # -------------------------------------------------

        data.reporter_name = self._parser.get_value(
            text,
            "Data collector name",
        )

        data.reporting_date = self._parser.get_datetime(
            text,
            "Start Time",
        )

        return data