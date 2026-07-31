"""
Standalone pathology/laboratory report extractor.

Unlike the REDCap-form extractors, these are free-form scanned or
digital pathology reports uploaded as attachments — layout, wording,
and unit formatting vary by lab. Extraction here is deliberately
conservative: a field is only populated when a recognizable test name
is found with a plausible value nearby. When a report's own OCR/text
layer scrambles label/value adjacency (e.g. a two-column results
table gets flattened into "all labels, then all values"), fields are
left empty rather than guessed from position alone.
"""

from __future__ import annotations

import re

from form_segmenter.form import Form
from models.lab import LabData
from utils.parser import TextParser

from .base import BaseExtractor


class LabExtractor(BaseExtractor[LabData]):
    """
    Extract structured information from standalone pathology reports.
    """

    # Each field maps to one or more synonyms a real-world report
    # might use for the same test. The first synonym that yields a
    # nearby numeric value wins. Deliberately full phrases only, not
    # bare abbreviations ("Hb", "Na+", "ALP") — those false-match
    # inside unrelated derived-index names that happen to contain the
    # same short token (e.g. "Hb" inside "Mean Corpus Hb Conc", which
    # is MCHC, not Hemoglobin).
    _FIELD_SYNONYMS: dict[str, tuple[str, ...]] = {
        "hemoglobin": ("Hemoglobin", "Haemoglobin"),
        "tlc": (
            "Total Leucocyte Count",
            "Total Leukocyte Count",
            "TLC Count",
            "WBC Count",
        ),
        "platelet_count": ("Platelet Count", "Platelets"),
        "anc": (
            "Absolute Neutrophil Count",
            "Absolute Neutrophils Count",
            "Abs Neutrophils",
        ),
        "total_bilirubin": (
            "Bilirubin Total",
            "Total Bilirubin",
            "Bilirubin (Total)",
        ),
        "direct_bilirubin": (
            "Bilirubin Direct",
            "Direct Bilirubin",
            "Conjugated Bilirubin",
        ),
        "indirect_bilirubin": (
            "Bilirubin Indirect",
            "Indirect Bilirubin",
            "Unconjugated Bilirubin",
        ),
        "total_protein": ("Total Protein", "Proteins Total"),
        "albumin": ("Albumin",),
        "globulin": ("Globulin", "Globulins"),
        "alkaline_phosphatase": (
            "Alkaline Phosphatase",
            "Alk Phosphatase",
        ),
        "sodium": ("Sodium",),
        "potassium": ("Potassium",),
        "ionic_calcium": ("Ionic Calcium", "Calcium"),
        "urea": ("Blood Urea", "Urea"),
        "creatinine": ("Serum Creatinine", "Creatinine"),
        "crp": ("C-Reactive Protein", "CRP"),
    }

    _NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?")

    # Pathology reports have none of REDCap's "* must provide value" /
    # numbered-question markers to bound a search, and a scanned
    # report's OCR text can flatten a two-column results table into
    # "all labels, then all values" — so a label match can be
    # textually followed by some *other* test's number entirely. A
    # wide lookahead (appropriate for REDCap forms) would confidently
    # return that wrong number. Keeping the window tight means: if the
    # value isn't right next to its label, report nothing rather than
    # guess.
    _MAX_LOOKAHEAD_LINES = 2

    # Other header-field labels that can legitimately end up on the
    # same reconstructed row as an unrelated field (e.g. "Date",
    # "Collected At" and "Reg/Ref" often share a compact header
    # line) — used to stop a metadata value before it runs into the
    # next field's label.
    _METADATA_STOP_WORDS = (
        "Date", "Reg/Ref", "Collected At", "Age/Sex", "Validate",
        "Requested Test", "Investigation", "Received", "Ref By",
        "Rel By", "Ret By", "Receipt",
    )

    @classmethod
    def _nearby_text(
        cls,
        lines: list[str],
        label: str,
        max_words: int = 6,
    ) -> str | None:
        """
        Like `_nearby_number`, but for short metadata string values —
        tight adjacency only, capped in length so that a row which
        legitimately contains several unrelated header fields (a
        reconstructed row can span the whole page width) doesn't get
        swallowed whole as one field's value.
        """

        pattern = re.compile(re.escape(label), flags=re.IGNORECASE)

        for line in lines:

            match = pattern.search(line)

            if not match:
                continue

            after = line[match.end():].strip(" :\t")

            if not after:
                continue

            for stop_word in cls._METADATA_STOP_WORDS:
                stop_match = re.search(
                    re.escape(stop_word), after, flags=re.IGNORECASE
                )
                if stop_match:
                    after = after[:stop_match.start()].strip()

            if not after:
                return None

            words = after.split()[:max_words]

            return " ".join(words) if words else None

        return None

    @classmethod
    def _nearby_number(
        cls,
        lines: list[str],
        label: str,
    ) -> float | None:

        pattern = re.compile(re.escape(label), flags=re.IGNORECASE)

        for i, line in enumerate(lines):

            # A comma-separated line is a test panel summary (e.g.
            # "Requested Test: CBC, KFT, LFT, Electrolyte, CRP"), not
            # a single result row — matching a test name inside it
            # would anchor the lookahead on the wrong line entirely.
            if "," in line:
                continue

            match = pattern.search(line)

            if not match:
                continue

            after = line[match.end():]

            for candidate in [after] + lines[
                i + 1:i + 1 + cls._MAX_LOOKAHEAD_LINES
            ]:

                stripped = candidate.strip()

                if not stripped or stripped.startswith(" "):
                    continue

                # The candidate line must *be* a value (a number,
                # optionally with a unit suffix), not merely contain
                # a digit somewhere — OCR frequently misreads letters
                # as digits inside unrelated words (e.g. "Bilirubin"
                # -> "Bil1rub1n"), which would otherwise be picked up
                # as a false value.
                number = cls._NUMBER.match(stripped)

                if number:
                    return float(number.group())

                # A non-numeric, non-blank line here means the label
                # is not actually followed by its value on this
                # document (e.g. a scrambled label/value column
                # layout) — stop rather than keep searching further
                # away and risk grabbing an unrelated number.
                return None

            return None

        return None

    # Report/patient metadata, tried in order.
    _DATE_LABELS = (
        "Collection Date",
        "Coll Time",
        "Collected On",
        "Report Date",
        "Sample Date",
        "Date",
    )

    _COLLECTED_AT_LABELS = ("Collected At", "Collection Centre", "Lab Name")

    _TESTS_REQUESTED_LABELS = (
        "Requested Test",
        "Test(s) Requested",
        "Tests Requested",
        "Investigation",
    )

    _ACCESSION_PATTERN = re.compile(
        r"(?:Reg[/.]?\s*Ref|Lab\s*(?:No|ID)|Accession\s*(?:No)?)\s*[:.\-]?\s*"
        r"([A-Za-z0-9/\-]{4,})",
        flags=re.IGNORECASE,
    )

    def __init__(self) -> None:
        self._parser = TextParser()

    def extract(self, form: Form) -> LabData:
        """
        Extract structured lab report data.
        """

        text = "\n".join(page.text for page in form.pages)
        text = self._parser.normalize(text)
        lines = text.splitlines()

        data = LabData()

        # -------------------------------------------------
        # Report metadata
        # -------------------------------------------------

        for label in self._DATE_LABELS:
            date = self._parser.get_date(text, label)
            if date:
                data.test_date = date
                break

        accession = self._ACCESSION_PATTERN.search(text)
        if accession:
            data.lab_accession_no = accession.group(1).strip()

        for label in self._COLLECTED_AT_LABELS:
            value = self._nearby_text(lines, label)
            if value:
                data.collected_at = value
                break

        for label in self._TESTS_REQUESTED_LABELS:
            value = self._nearby_text(lines, label, max_words=12)
            if value:
                data.tests_requested = value
                break

        # -------------------------------------------------
        # Test results
        # -------------------------------------------------

        for field_name, synonyms in self._FIELD_SYNONYMS.items():

            value = None

            for synonym in synonyms:
                value = self._nearby_number(lines, synonym)
                if value is not None:
                    break

            if value is not None:
                setattr(data, field_name, value)

        data.remarks = self._parser.get_value(text, "Remarks")

        return data
