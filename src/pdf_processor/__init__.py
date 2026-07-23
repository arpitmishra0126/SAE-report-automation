"""
PDF Processing Module.

This package provides the functionality required to read REDCap PDF exports
and convert them into structured page objects for downstream processing.

Responsibilities
----------------
- Open PDF documents.
- Extract page-wise text.
- Return structured page data.
- Raise standardized exceptions.

This module intentionally does NOT perform:
- OCR
- Form segmentation
- Information extraction
- Validation
- Narrative generation
"""

from .page import PageData
from .pdf_reader import PDFReader
from .extractor import PDFExtractor

__all__ = [
    "PageData",
    "PDFReader",
    "PDFExtractor",
]