"""
Form segmentation engine.

Groups consecutive PDF pages into logical REDCap forms.

--------------------------------------------------------------------
Continuation rule (how pages are grouped into one Form)
--------------------------------------------------------------------
Each page is classified independently as either a strong match for
one specific FormType, or UNKNOWN.

- A strong match always starts a *new* Form, even if the previous
  page was the same type (e.g. two separate NSS submissions for
  different days are kept as two Forms, not merged) — with one
  exception: consecutive LAB-type strong matches are merged into the
  same Form, since a multi-page pathology report typically re-clears
  the LAB score on every page (each page is independently dense with
  test names/values), unlike a REDCap form's title page.
- An UNKNOWN page is treated as a continuation of whatever Form is
  currently open and is appended to it. This is deliberate: REDCap's
  PDF export repeats a full page header only on a form's first page,
  so pages 2..N of the same submission (and pages of a multi-page
  attachment such as a scanned lab report) legitimately carry no
  detectable signature of their own. There is no per-pair "is this
  really a continuation" check beyond that — the strong/weak
  distinction above *is* the continuation rule. Pages before the
  first strong match remain an UNKNOWN form (e.g. a cover page).

Because "UNKNOWN attaches to whatever is currently open" is the whole
continuation mechanism, a signature that fires as a false positive
mid-form (e.g. a REDCap question that merely *mentions* the word
"laboratory") doesn't just mislabel one page — it fractures the
current form and starts misrouting subsequent UNKNOWN pages into the
wrong Form. Signatures must therefore be conservative: specific
enough that they only fire on a genuine new form/attachment, never on
a passing mention inside another form's content. See
`_looks_like_redcap_page` / `_looks_like_lab_report` below.
"""

from __future__ import annotations

import re

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
    }

    # Markers that only ever appear on a REDCap-native page (the
    # "* must provide value" field marker, the REDCap footer/URL, or
    # a numbered REDCap question). Any page carrying one of these is
    # part of a REDCap form submission, never a standalone uploaded
    # lab report — regardless of what words it happens to contain.
    _REDCAP_MARKERS = re.compile(
        r"must provide value|redcap|record id\s*\n?\s*\d",
        flags=re.IGNORECASE,
    )

    # Requires whitespace around the dash ("16 - What was...") so it
    # doesn't false-positive on a bare numeric range like "0-12" in a
    # lab report's reference-interval column.
    _NUMBERED_QUESTION = re.compile(
        r"^\s*\d+(?:\.\d+)?\s+[-–]\s+\S", re.MULTILINE
    )

    # Vocabulary and structural cues of a standalone pathology report.
    # No single one is sufficient on its own (several are common
    # English words); a page must clear a minimum combined score.
    _LAB_TEST_KEYWORDS = (
        "hemoglobin", "haemoglobin", "leucocyte", "leukocyte",
        "platelet", "neutrophil", "bilirubin", "creatinine",
        "electrolyte", "sodium", "potassium", "calcium", "albumin",
        "globulin", "urea", "c-reactive protein", "crp",
        "pathology", "biochemistry", "hematology", "haematology",
    )

    _LAB_STRUCTURAL_KEYWORDS = (
        "observed value", "biological ref", "reference range",
        "reference interval", "normal range", "reg/ref", "lab no",
        "accession", "collected at", "requested test",
        "for pathologist", "end of report", "investigation report",
    )

    _LAB_MIN_SCORE = 3

    @classmethod
    def _looks_like_redcap_page(cls, lower_text: str, raw_text: str) -> bool:
        return (
            cls._REDCAP_MARKERS.search(lower_text) is not None
            or cls._NUMBERED_QUESTION.search(raw_text) is not None
        )

    @classmethod
    def _looks_like_lab_report(cls, lower_text: str, raw_text: str) -> bool:

        if cls._looks_like_redcap_page(lower_text, raw_text):
            # A REDCap question mentioning "laboratory tests" (e.g.
            # "Please upload the PDF of laboratory tests...") is not
            # itself a lab report.
            return False

        score = 0

        for keyword in cls._LAB_TEST_KEYWORDS:
            if keyword in lower_text:
                score += 1

        for keyword in cls._LAB_STRUCTURAL_KEYWORDS:
            if keyword in lower_text:
                score += 2

        return score >= cls._LAB_MIN_SCORE

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

            if (
                detected == FormType.LAB
                and current_type == FormType.LAB
            ):
                # Unlike REDCap forms (where two consecutive strong
                # matches of the same type are genuinely two separate
                # submissions), a multi-page pathology report tends to
                # re-clear the LAB score on *every* page — each page
                # is independently dense with test names. Treat a
                # LAB page immediately following another LAB page as
                # the same report continuing, not a new one.
                current_pages.append(page)

            elif detected != FormType.UNKNOWN:

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

        if self._looks_like_lab_report(lower, text):
            return FormType.LAB

        return FormType.UNKNOWN