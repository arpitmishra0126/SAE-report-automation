"""
SAE form extractor.
"""

from __future__ import annotations

import re

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

        text = "\n".join(page.text for page in form.pages)
        text = self._parser.normalize(text)

        print("\n" + "=" * 80)
        print("SAE EXTRACTOR INPUT")
        print("=" * 80)
        print(text[:8000])
        print("=" * 80)

        data = SAEData()

        # -------------------------------------------------
        # Case Information
        # -------------------------------------------------

        record = self._parser.get_value(text, "Record ID")

        if record:
            m = re.search(r"\d+-\d+", record)
            if m:
                data.record_id = m.group(0)

        uid = self._parser.get_value(text, "Enrolled Baby's UID")

        if uid:
            data.participant_id = uid.split()[0]

        data.site = (
            self._parser.get_value(text, "Hospital Name")
            or self._parser.get_value(text, "Hospita Name")
        )

        # -------------------------------------------------
        # Hospital Information
        # -------------------------------------------------

        data.hospital_name = data.site

        data.admission_date = (
            self._parser.get_datetime(text, "Enrollment Date")
            or self._parser.get_datetime(text, "Date of Enrollment")
        )

        # -------------------------------------------------
        # SAE Information
        # -------------------------------------------------

        data.event_date = (
            self._parser.get_date(text, "Date of onset of SAE")
            or self._parser.get_date(text, "adverse event started")
            or self._parser.get_date(text, "date when the adverse event started")
        )

        data.outcome = (
            self._parser.get_value(text, "Please describe the outcome of the event")
            or self._parser.get_value(text, "outcome of the event")
        )

        data.cause_of_death = (
            self._parser.get_multiline_value(
                text,
                "underlying cause of death",
                "Please provide any relevant past medical",
            )
            or self._parser.get_multiline_value(
                text,
                "cause of death",
                "Please provide any relevant past medical",
            )
        )

        data.diagnosis = (
            self._parser.get_multiline_value(
                text,
                "Please provide any other relevant clinical",
                "Please enter any additional comments",
            )
            or self._parser.get_multiline_value(
                text,
                "relevant clinical information",
                "Please enter any additional comments",
            )
        )

        data.event_description = (
            self._parser.get_multiline_value(
                text,
                "Please enter the medication history",
                "How severe was the SAE",
            )
            or self._parser.get_multiline_value(
                text,
                "medication history",
                "How severe was the SAE",
            )
        )

        data.seriousness = (
            self._parser.get_value(text, "How severe was the SAE")
            or self._parser.get_value(text, "How severe was the SAE [AE")
        )

        # -------------------------------------------------
        # Reporter
        # -------------------------------------------------

        data.reporter_name = (
            self._parser.get_value(text, "Data collector name")
            or self._parser.get_value(text, "Collector Name")
        )

        data.reporting_date = (
            self._parser.get_datetime(text, "Start Time")
            or self._parser.get_datetime(text, "Start Time/Time Stamp")
        )

        return data