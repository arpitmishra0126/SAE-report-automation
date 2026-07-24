"""
Form segmentation engine.

This module identifies logical REDCap forms from a sequence of PDF pages.

Responsibilities
----------------
- Detect form boundaries.
- Group consecutive pages belonging to the same form.
- Produce structured Form objects.

This module intentionally does NOT:
- Extract clinical information.
- Perform OCR.
- Clean page text.
"""

from __future__ import annotations

from pdf_processor.page import PDFPage

from .form import Form, FormType


class FormDetector:
    """
    Detects REDCap forms from extracted PDF pages.
    """

    # Form title signatures observed across REDCap exports
    FORM_SIGNATURES: dict[FormType, tuple[str, ...]] = {
        FormType.SAE: (
            "Serious Adverse Event",
        ),
        FormType.MATERNAL: (
            "Maternal History Module",
        ),
        FormType.DCM: (
            "Daily Clinical Monitoring",
        ),
        FormType.NSS: (
            "Neonatal Sepsis Surveillance",
        ),
        FormType.LAB: (
            "Laboratory",
        ),
    }

    def segment(self, pages: list[PDFPage]) -> list[Form]:
        """
        Segment PDF pages into logical REDCap forms.

        Args:
            pages:
                List of extracted PDF pages.

        Returns:
            List of detected Form objects.
        """

        forms: list[Form] = []

        current_form_type: FormType | None = None
        current_pages: list[PDFPage] = []

        for page in pages:

            detected_type = self._detect_form_type(page)

            # Start of a new form
            if detected_type != FormType.UNKNOWN:

                if current_pages:
                    forms.append(
                        Form(
                            form_type=current_form_type
                            or FormType.UNKNOWN,
                            pages=current_pages,
                        )
                    )

                current_form_type = detected_type
                current_pages = [page]

            else:
                current_pages.append(page)

        # Add the final form
        if current_pages:
            forms.append(
                Form(
                    form_type=current_form_type
                    or FormType.UNKNOWN,
                    pages=current_pages,
                )
            )

        return forms

    def _detect_form_type(self, page: PDFPage) -> FormType:
        """
        Detect the REDCap form type for a page.

        Args:
            page:
                PDF page.

        Returns:
            Detected FormType.
        """

        text = page.text.lower()

        for form_type, signatures in self.FORM_SIGNATURES.items():

            for signature in signatures:

                if signature.lower() in text:
                    return form_type

        return FormType.UNKNOWN