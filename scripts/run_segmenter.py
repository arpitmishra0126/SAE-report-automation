"""
Unit tests for the FormDetector.
"""

from src.form_segmenter.detector import FormDetector
from src.form_segmenter.form import FormType
from src.pdf_processor.page import PDFPage


def make_page(page_number: int, text: str) -> PDFPage:
    """Create a mock PDF page."""

    return PDFPage(
        source_file="sample.pdf",
        page_number=page_number,
        text=text,
        metadata={},
    )


def test_detect_single_form():
    """Detector should identify a single SAE form."""

    pages = [
        make_page(1, "Serious Adverse Event"),
        make_page(2, "Patient details"),
        make_page(3, "Clinical findings"),
    ]

    detector = FormDetector()
    forms = detector.segment(pages)

    assert len(forms) == 1
    assert forms[0].form_type == FormType.SAE
    assert forms[0].start_page == 1
    assert forms[0].end_page == 3
    assert forms[0].page_count == 3


def test_detect_multiple_forms():
    """Detector should split consecutive forms."""

    pages = [
        make_page(1, "Serious Adverse Event"),
        make_page(2, "Continuation"),

        make_page(3, "Maternal History Module"),
        make_page(4, "Maternal information"),

        make_page(5, "Daily Clinical Monitoring"),
        make_page(6, "Vital signs"),
    ]

    detector = FormDetector()
    forms = detector.segment(pages)

    assert len(forms) == 3

    assert forms[0].form_type == FormType.SAE
    assert forms[0].start_page == 1
    assert forms[0].end_page == 2

    assert forms[1].form_type == FormType.MATERNAL
    assert forms[1].start_page == 3
    assert forms[1].end_page == 4

    assert forms[2].form_type == FormType.DCM
    assert forms[2].start_page == 5
    assert forms[2].end_page == 6


def test_unknown_form():
    """Pages without a known heading should be grouped as UNKNOWN."""

    pages = [
        make_page(1, "Some random page"),
        make_page(2, "Another random page"),
    ]

    detector = FormDetector()
    forms = detector.segment(pages)

    assert len(forms) == 1
    assert forms[0].form_type == FormType.UNKNOWN
    assert forms[0].page_count == 2


def test_empty_document():
    """Empty input should return no forms."""

    detector = FormDetector()
    forms = detector.segment([])

    assert forms == []