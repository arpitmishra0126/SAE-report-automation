"""
Extraction orchestrator.

Coordinates all form-specific extractors and produces a complete
CaseSummary object.
"""

from __future__ import annotations

import logging

from form_segmenter.form import Form, FormType
from models.case_summary import CaseSummary

from .dcm_extractor import DCMExtractor
from .lab_extractor import LabExtractor
from .maternal_extractor import MaternalExtractor
from .nss_extractor import NSSExtractor
from .sae_extractor import SAEExtractor

logger = logging.getLogger(__name__)

# Below this many characters, a form with no extractor is almost
# certainly a blank/cover/divider page and not worth reporting as
# "skipped" — anything larger is substantial enough content that
# silently dropping it should be visible.
_NOTEWORTHY_SKIP_LENGTH = 40


class Extractor:
    """
    Main extraction coordinator.
    """

    def __init__(self) -> None:
        self._sae = SAEExtractor()
        self._maternal = MaternalExtractor()
        self._dcm = DCMExtractor()
        self._nss = NSSExtractor()
        self._lab = LabExtractor()

    def extract(self, forms: list[Form]) -> CaseSummary:
        """
        Extract all detected forms into a CaseSummary.
        """

        summary = CaseSummary()

        for form in forms:

            if not form.pages:
                continue

            match form.form_type:

                case FormType.SAE:
                    summary.sae = self._sae.extract(form)

                case FormType.MATERNAL:
                    summary.maternal = self._maternal.extract(form)

                case FormType.DCM:
                    summary.dcm.append(
                        self._dcm.extract(form)
                    )

                case FormType.NSS:
                    summary.nss.append(
                        self._nss.extract(form)
                    )

                case FormType.LAB:
                    summary.lab.append(
                        self._lab.extract(form)
                    )

                case _:
                    self._record_skip(summary, form)

        return summary

    @staticmethod
    def _record_skip(summary: CaseSummary, form: Form) -> None:
        """
        No extractor is registered for this form type (currently
        ATTACHMENT/UNKNOWN). Never drop this silently: warn, and
        record it on the summary so it surfaces in the final report.
        """

        if len(form.text.strip()) < _NOTEWORTHY_SKIP_LENGTH:
            return

        message = (
            f"Skipped {form.form_type.name} "
            f"(pages {form.start_page}-{form.end_page}): "
            f"no extractor registered for this form type."
        )

        logger.warning(message)

        summary.skipped_forms.append(message)