"""
PDF reader implementation.

This module provides a lightweight wrapper around PyMuPDF for opening
PDF documents and exposing page-level information in a controlled way.

Responsibilities
----------------
- Open PDF documents.
- Validate the PDF path.
- Read page text.
- Read page metadata.
- Return structured PDFPage objects.

This module intentionally does NOT:
- Perform OCR.
- Clean extracted text.
- Detect forms.
- Extract clinical information.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import fitz

from .exceptions import (
    PDFEncryptedError,
    PDFNotFoundError,
    PDFReadError,
)
from .page import PDFPage


class PDFReader:
    """
    Low-level PDF reader built on top of PyMuPDF.
    """

    def __init__(self, pdf_path: str | Path) -> None:
        self.pdf_path = Path(pdf_path)

        if not self.pdf_path.exists():
            raise PDFNotFoundError(f"PDF not found: {self.pdf_path}")

        try:
            self._document = fitz.open(self.pdf_path)

            if self._document.needs_pass:
                raise PDFEncryptedError(
                    "Encrypted PDFs are not supported."
                )

        except PDFEncryptedError:
            raise

        except Exception as exc:
            raise PDFReadError(
                f"Unable to open PDF: {self.pdf_path}"
            ) from exc

    @property
    def filename(self) -> str:
        """Return the source PDF filename."""
        return self.pdf_path.name

    @property
    def page_count(self) -> int:
        """Return total number of pages."""
        return len(self._document)

    def _validate_page_number(self, page_number: int) -> None:
        """
        Validate that the requested page exists.

        Args:
            page_number:
                Zero-based page index.
        """
        if page_number < 0 or page_number >= self.page_count:
            raise IndexError(
                f"Page index {page_number} is out of range "
                f"(0-{self.page_count - 1})."
            )

    def get_text(self, page_number: int) -> str:
        """
        Extract plain text from a page.

        Args:
            page_number:
                Zero-based page index.

        Returns:
            Extracted page text.
        """
        self._validate_page_number(page_number)

        page = self._document.load_page(page_number)

        # PyMuPDF type hints are very broad.
        # We know "text" always returns a string.
        text = cast(str, page.get_text("text"))

        return text.strip()

    def get_metadata(self, page_number: int) -> dict[str, Any]:
        """
        Return basic metadata for a page.

        Args:
            page_number:
                Zero-based page index.

        Returns:
            Dictionary containing page metadata.
        """
        self._validate_page_number(page_number)

        page = self._document.load_page(page_number)

        return {
            "width": page.rect.width,
            "height": page.rect.height,
            "rotation": page.rotation,
        }

    def get_page(self, page_number: int) -> fitz.Page:
        """
        Return the raw PyMuPDF page object.

        Intended for advanced processing such as image extraction,
        coordinate-based operations or future OCR support.

        Args:
            page_number:
                Zero-based page index.

        Returns:
            PyMuPDF Page object.
        """
        self._validate_page_number(page_number)

        return self._document.load_page(page_number)

    def read(self) -> list[PDFPage]:
        """
        Read the entire PDF.

        Returns:
            List of structured PDFPage objects.
        """
        pages: list[PDFPage] = []

        for index in range(self.page_count):
            pages.append(
                PDFPage(
                    source_file=self.filename,
                    page_number=index + 1,
                    text=self.get_text(index),
                    metadata=self.get_metadata(index),
                )
            )

        return pages

    def close(self) -> None:
        """Close the PDF document."""
        self._document.close()

    def __enter__(self) -> "PDFReader":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()