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
        # Vitals
        # -------------------------------------------------

        data.temperature = self._parser.get_float(
            text,
            "Measure the newborn's temperature.",
        )

        data.on_radiant_warmer = self._parser.get_bool(
            text,
            "Is the newborn kept on a radiant warmer?",
        )

        data.high_temperature_flag = self._parser.get_bool(
            text,
            "Does the newborn have a high temperature",
        )

        data.low_temperature_flag = self._parser.get_bool(
            text,
            "Does the infant have a low body temperature",
        )

        data.spo2 = self._parser.get_float(
            text,
            "What is the newborn's oxygen saturation",
        )

        data.pulse_rate = self._parser.get_float(
            text,
            "What is the pulse rate of the newborn?",
        )

        data.tachycardia = self._parser.get_bool(
            text,
            "Is the newborn having tachycardia?",
        )

        data.bradycardia = self._parser.get_bool(
            text,
            "Is the newborn having bradycardia?",
        )

        data.respiratory_rate = self._parser.get_float(
            text,
            "Count the breaths in one minute.",
        )

        data.fast_breathing = self._parser.get_bool(
            text,
            "Does the baby has fast breathing?",
        )

        data.bradypnea = self._parser.get_bool(
            text,
            "Is the newborn experiencing bradypnea?",
        )

        data.on_noninvasive_ventilator = self._parser.get_bool(
            text,
            "Is the newborn kept on a non-invasive ventilator?",
        )

        data.on_invasive_ventilator = self._parser.get_bool(
            text,
            "Is the newborn kept on a invasive mechanical",
        )

        # -------------------------------------------------
        # Clinical exam findings
        # -------------------------------------------------

        data.cry_type = self._parser.get_value(
            text,
            "What is the type of cry observed in the newborn?",
        )

        data.muscle_tone = self._parser.get_value(
            text,
            "What is the muscle tone of the newborn?",
        )

        # "Has the newborn shown any of the following neurological
        # signs?" and the skin-perfusion, GI-signs and skin/umbilical
        # questions below are unticked multi-select checkboxes in this
        # export — the tick mark is a graphic, not text, so which
        # option(s) were selected cannot be recovered here.

        data.skin_colour = self._parser.get_value(
            text,
            "What is the newborn's skin colour?",
        )

        data.bleeding_observed = self._parser.get_bool(
            text,
            "Is there any bleeding observed in the newborn?",
        )

        data.fontanelle_bulging = self._parser.get_bool(
            text,
            "Is the anterior fontanelle of the newborn bulging?",
        )

        data.general_condition = self._parser.get_value(
            text,
            "What is the general condition of the newborn?",
        )

        data.sepsis_impression = self._parser.get_value(
            text,
            "What is the clinician's impression regarding sepsis?",
        )

        # -------------------------------------------------
        # Blood test ordering
        # -------------------------------------------------

        data.blood_test_ordered = self._parser.get_bool(
            text,
            "Has the doctor prescribed any blood test for the",
        )

        data.blood_test_report_available = self._parser.get_bool(
            text,
            "Are the reports of the prescribed blood test",
        )

        # "What tests were planned/conducted?" is an unticked
        # multi-select checkbox and is not recoverable; which panels
        # were actually run is instead evidenced by which inline lab
        # values below are present.

        data.procalcitonin_done = self._parser.get_bool(
            text,
            "Did the facility planned/conducted a pro-calcitonin",
        )

        # -------------------------------------------------
        # Inline lab values
        # -------------------------------------------------

        data.blood_glucose = self._parser.get_float(
            text,
            "Blood sugar level (mg/dL)",
        )

        data.tlc = self._parser.get_float(
            text,
            "TLC Count",
        )

        data.hemoglobin = self._parser.get_float(
            text,
            "Hemoglobin",
        )

        data.platelet_count = self._parser.get_float(
            text,
            "Platelet Count",
        )

        data.anc = self._parser.get_float(
            text,
            "Absolute Neutrophils Count",
        )

        data.total_bilirubin = self._parser.get_float(
            text,
            "Total Bilirubin",
        )

        data.crp = self._parser.get_float(
            text,
            "CRP",
        )

        # -------------------------------------------------
        # Remarks
        # -------------------------------------------------

        data.remarks = self._parser.get_value(
            text,
            "36 - Remarks",
        )

        return data