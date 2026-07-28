"""
Form segmentation engine.

Groups consecutive PDF pages into logical REDCap forms.
"""

from __future__ import annotations

from pdf_processor.page import PageData

from .form import Form, FormType


class FormDetector:
    """
    Detect REDCap forms from extracted PDF pages.
    """

    FORM_SIGNATURES: dict[FormType, tuple[str, ...]] = {
        FormType.MATERNAL: (
            "Maternal History Module",
            "Maternal History",
        ),

        FormType.DCM: (
            "Daily Clinical Monitoring",
        ),

        FormType.NSS: (
            "Neonatal Sepsis Screening",
            "Neonatal Sepsis Surveillance",
        ),

        FormType.SAE: (
            "Serious Adverse Event\nRecord ID",
            "Serious Adverse Event\r\nRecord ID",
            "Serious Adverse Event Record ID",
        ),

        FormType.LAB: (
            "Laboratory",
            "Laboratory Investigations",
        ),
    }

    def _safe_console(self, text: str) -> str:
        """
        Convert text into something Windows console can always print.
        """
        return (
            text.encode("cp1252", errors="replace")
            .decode("cp1252")
        )

    def segment(
        self,
        pages: list[PageData],
    ) -> list[Form]:

        forms: list[Form] = []

        current_type = FormType.UNKNOWN
        current_pages: list[PageData] = []

        print("\n" + "=" * 70)
        print("FORM DETECTION")
        print("=" * 70)

        for page in pages:

            detected = self._detect_form_type(page)

            preview = page.text[:60]
            preview = self._safe_console(preview)

            print(
                f"Page {page.page_number:03d} | "
                f"{detected.name:<10} | "
                f"{preview}"
            )

            if detected != FormType.UNKNOWN:

                if current_pages:
                    forms.append(
                        Form(
                            form_type=current_type,
                            pages=current_pages,
                        )
                    )

                current_type = detected
                current_pages = [page]

            else:
                current_pages.append(page)

        if current_pages:
            forms.append(
                Form(
                    form_type=current_type,
                    pages=current_pages,
                )
            )

        print("\nDetected Forms")
        print("-" * 70)

        for i, form in enumerate(forms, start=1):
            print(
                f"{i:02d}. "
                f"{form.form_type.name:<10} "
                f"Pages={len(form.pages):<3} "
                f"Start={form.pages[0].page_number}"
            )

        print("=" * 70)

        return forms

    def _detect_form_type(
        self,
        page: PageData,
    ) -> FormType:

        text = page.text
        lower = text.casefold()

        if (
            "adverse skin events and serious adverse events screening"
            in lower
        ):
            return FormType.UNKNOWN

        if (
            "serious adverse event" in lower
            and "record id" in lower
            and "enrolled baby's uid" in lower
        ):
            return FormType.SAE

        for form_type, signatures in self.FORM_SIGNATURES.items():

            if form_type == FormType.SAE:
                continue

            for signature in signatures:
                if signature.casefold() in lower:
                    return form_type

        return FormType.UNKNOWN