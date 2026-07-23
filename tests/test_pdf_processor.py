"""
Unit tests for the PDF Processing module.
"""

from pathlib import Path

import pytest

from src.pdf_processor import PDFExtractor


SAMPLE_PDF = Path("data/sample_pdfs/sample.pdf")


@pytest.mark.skipif(
    not SAMPLE_PDF.exists(),
    reason="Sample PDF not found."
)
def test_pdf_extraction():
    """
    Verify that page-wise text extraction works correctly.
    """

    extractor = PDFExtractor(SAMPLE_PDF)

    pages = extractor.extract()

    # At least one page should be extracted
    assert len(pages) > 0

    # First page numbering starts at 1
    assert pages[0].page_number == 1

    # Text should always be a string
    assert isinstance(pages[0].text, str)

    # Metadata should exist
    assert isinstance(pages[0].metadata, dict)

    # Basic metadata keys
    assert "width" in pages[0].metadata
    assert "height" in pages[0].metadata
    assert "rotation" in pages[0].metadata