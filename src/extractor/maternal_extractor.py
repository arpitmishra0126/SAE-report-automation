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

        # "21 - Remarks" is an optional field with no "* must provide
        # value" marker, so when it's genuinely left blank there is no
        # reliable textual boundary between it and the "G.A" field
        # that immediately follows — the lookahead can pick up G.A's
        # value instead. Guard against that specific, known collision
        # rather than reporting someone else's field as a remark.
        if data.maternal_remarks and data.maternal_remarks.startswith("G.A"):
            data.maternal_remarks = None

        # -------------------------------------------------
        # Gestational Age
        # -------------------------------------------------

        data.gestational_age = self._parser.get_value(
            text,
            "G.A",
        )

        # -------------------------------------------------
        # Antenatal corticosteroids
        # -------------------------------------------------

        data.corticosteroids_given = self._parser.get_bool(
            text,
            "Was the mother given antenatal corticosteroids",
        )

        data.steroid_type = self._parser.get_value(
            text,
            "If yes, which steroid was administered?",
        )

        steroid_doses = self._parser.get_number(
            text,
            "How many doses were administered?",
        )

        if steroid_doses is not None:
            data.steroid_doses = steroid_doses

        # -------------------------------------------------
        # Labour history
        # -------------------------------------------------

        # "Did the mother experience fever during pregnancy or labour?"
        # is an unticked checkbox question in this REDCap export — the
        # tick mark is a graphic, not text, so which option (if any)
        # was selected cannot be recovered here. Left unset rather
        # than guessing.

        data.foul_smelling_discharge = self._parser.get_bool(
            text,
            "Was there foul-smelling vaginal discharge during",
        )

        data.uterine_tenderness = self._parser.get_bool(
            text,
            "Was uterine tenderness observed during labour",
        )

        data.pprom_over_24h = self._parser.get_bool(
            text,
            "Was leaking per vaginum present for more than 24",
        )

        data.amniotic_fluid_appearance = self._parser.get_value(
            text,
            "What was the appearance of amniotic",
        )

        data.presentation = self._parser.get_value(
            text,
            "What was the presentation of the baby at birth?",
        )

        data.labour_course = self._parser.get_value(
            text,
            "What was the course of complete labour?",
        )

        data.foetal_distress = self._parser.get_bool(
            text,
            "Was foetal distress observed during labour",
        )

        data.delivery_mode = data.delivery_type

        # "Who assisted the delivery?" is likewise an unticked
        # checkbox question — not recoverable from the text layer.

        data.significant_maternal_info_flag = self._parser.get_bool(
            text,
            "Is there any significant information in the maternal",
        )

        return data