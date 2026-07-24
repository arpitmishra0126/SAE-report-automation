"""
Extraction orchestrator.

Coordinates all form-specific extractors and produces a complete
CaseSummary object.

Responsibilities
----------------
- Route each detected form to the correct extractor.
- Combine extracted information.
- Return a populated CaseSummary.
"""

from __future__ import annotations

from form_segmenter.form import Form, FormType
from models.case_summary import CaseSummary

from .dcm_extractor import DCMExtractor
from .maternal_extractor import MaternalExtractor
from .nss_extractor import NSSExtractor
from .sae_extractor import SAEExtractor


class Extractor:
    """
    Main extraction coordinator.
    """

    def __init__(self) -> None:
        self._sae = SAEExtractor()
        self._maternal = MaternalExtractor()
        self._dcm = DCMExtractor()
        self._nss = NSSExtractor()

    def extract(self, forms: list[Form]) -> CaseSummary:
        """
        Extract all detected forms into a CaseSummary.
        """

        summary = CaseSummary()

        for form in forms:

            if form.form_type == FormType.SAE:
                summary.sae = self._sae.extract(form)

            elif form.form_type == FormType.MATERNAL:
                summary.maternal = self._maternal.extract(form)

            elif form.form_type == FormType.DCM:
                summary.dcm.append(
                    self._dcm.extract(form)
                )

            elif form.form_type == FormType.NSS:
                summary.nss.append(
                self._nss.extract(form)
            )

        return summary