"""
PDF reader implementation.

This module provides a lightweight wrapper around PyMuPDF for opening
PDF documents and exposing page-level information in a controlled way.

Responsibilities
----------------
- Open PDF documents.
- Validate the PDF path.
- Provide page count.
- Extract raw page text.
- Provide page metadata.

This module intentionally does NOT:
- Perform OCR.
- Clean extracted text.
- Detect forms.
- Extract clinical information.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz
from pdfplumber import page

from .exceptions import (
    PDFEncryptedError,
    PDFNotFoundError,
    PDFReadError,
)


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
    def page_count(self) -> int:
        """Return total number of pages."""
        return len(self._document)

    def get_text(self, page_number: int) -> str:
        """
        Extract plain text from a page.

        Args:
            page_number:
                Zero-based page index.

        Returns:
            Extracted text.
        """
        page = self._document.load_page(page_number)
        return str(page.get_text("text") or "")

    def get_metadata(self, page_number: int) -> dict[str, Any]:
        """
        Return basic metadata for a page.

        Args:
            page_number:
                Zero-based page index.

        Returns:
            Dictionary containing page metadata.
        """
        page = self._document.load_page(page_number)

        return {
            "width": page.rect.width,
            "height": page.rect.height,
            "rotation": page.rotation,
        }

    def get_page(self, page_number: int) -> fitz.Page:
        """
        Return the raw PyMuPDF page object.

        This method is intended for developer utilities and advanced
        processing that require direct access to the page object.

        Args:
            page_number:
                Zero-based page index.

        Returns:
            PyMuPDF Page object.
        """
        return self._document.load_page(page_number)

    def close(self) -> None:
        """Close the PDF document."""
        self._document.close()

    def __enter__(self) -> "PDFReader":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()