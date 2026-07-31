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
        # Discharge / Bed Sharing
        # -------------------------------------------------

        data.discharged_or_referred = self._parser.get_bool(
            text,
            "Is the baby discharged/referred out",
        )

        data.bed_sharing = self._parser.get_bool(
            text,
            "Was the baby sharing bed with other babies?",
        )

        # -------------------------------------------------
        # Baby Weight
        # -------------------------------------------------

        data.weight_taken = self._parser.get_bool(
            text,
            "Have you taken the weight of the newborn?",
        )

        weight = self._parser.get_number(
            text,
            "Measure the weight of the newborn",
        )

        if weight is not None:
            data.weight = float(weight)

        # -------------------------------------------------
        # Support / interventions
        # -------------------------------------------------

        data.on_incubator_support = self._parser.get_bool(
            text,
            "Is the newborn kept on incubator support?",
        )

        data.on_medications = self._parser.get_bool(
            text,
            "Is the newborn being prescribed any medications?",
        )

        data.medications = self._parser.get_multiline_value(
            text,
            "newborn is being prescribed.",
            "Section F",
        )

        data.kmc_provided = self._parser.get_bool(
            text,
            "Has Kangaroo Mother Care (KMC) been provided to",
        )

        # "If No KMC, please specify the reason" is an unticked
        # multi-select checkbox question — the tick mark is a graphic,
        # not text, so it is not recoverable from the text layer.

        # -------------------------------------------------
        # Feeding
        # -------------------------------------------------

        # "What was the newborn fed..." and "How was the feed
        # provided..." are also unticked checkbox questions and are
        # not recoverable — dumping their unmarked option list into
        # feed_types/feed_route would fabricate an answer, so they
        # are left unset.

        data.enteral_feed_ml = self._parser.get_float(
            text,
            "Enteral feeds in last 24 hours",
        )

        data.total_fluid_intake_ml = self._parser.get_float(
            text,
            "Total Fluid Intake in ml in last 24 hours",
        )

        # -------------------------------------------------
        # Remarks
        # -------------------------------------------------

        data.remarks = self._parser.get_value(
            text,
            "16 - Remarks",
        )

        return data