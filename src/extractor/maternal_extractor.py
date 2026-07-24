"""
Maternal History extractor.
"""

from __future__ import annotations

from form_segmenter.form import Form
from models.maternal import MaternalData
from utils.parser import TextParser

from .base import BaseExtractor


class MaternalExtractor(BaseExtractor[MaternalData]):
    """
    Extract structured information from the
    Maternal History REDCap form.
    """

    def __init__(self) -> None:
        self._parser = TextParser()

    def extract(self, form: Form) -> MaternalData:
        """
        Extract structured maternal history data.
        """

        text = "\n".join(page.text for page in form.pages)

        text = self._parser.normalize(text)

        data = MaternalData()

        # -------------------------------------------------
        # General Information
        # -------------------------------------------------

        data.mother_name = self._parser.get_value(
            text,
            "Mother's Name",
        )

        data.father_name = self._parser.get_value(
            text,
            "Fathers Name",
        )

        data.hospital_name = self._parser.get_value(
            text,
            "Hospital Name",
        )

        data.hospital_reg_no = self._parser.get_value(
            text,
            "Hospital Reg No",
        )

        data.baby_uid = self._parser.get_value(
            text,
            "Enrolled Baby's UID",
        )

        # -------------------------------------------------
        # Maternal History
        # -------------------------------------------------

        data.mother_age = self._parser.get_number(
            text,
            "Please state age of the mother in completed years",
        )

        data.labour_type = self._parser.get_value(
            text,
            "Type of Labour",
        )

        data.delivery_type = self._parser.get_value(
            text,
            "What was the type of delivery of eligible baby?",
        )

        data.maternal_remarks = self._parser.get_value(
            text,
            "21 - Remarks",
        )

        # -------------------------------------------------
        # Gestational Age
        # -------------------------------------------------

        data.gestational_age = self._parser.get_value(
            text,
            "G.A",
        )

        return data