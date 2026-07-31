"""
PDF reader implementation.

Provides a lightweight wrapper around PyMuPDF.

Responsibilities
----------------
- Open PDF documents.
- Validate PDF path.
- Extract page text.
- Preserve page layout information.
- Return structured PageData objects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from .ocr_processor import OCRProcessor
from .layout import needs_row_reconstruction, reconstruct_reading_order


import fitz

from .exceptions import (
    PDFEncryptedError,
    PDFNotFoundError,
    PDFReadError,
)
from .page import PageData


class PDFReader:
    """
    Low-level PDF reader built on top of PyMuPDF.
    """

    def __init__(self, pdf_path: str | Path) -> None:
        self.pdf_path = Path(pdf_path)
        self._ocr = OCRProcessor()

        if not self.pdf_path.exists():
            raise PDFNotFoundError(
                f"PDF not found: {self.pdf_path}"
            )

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
        return self.pdf_path.name

    @property
    def page_count(self) -> int:
        return len(self._document)

    def _validate_page_number(self, page_number: int) -> None:

        if page_number < 0 or page_number >= self.page_count:
            raise IndexError(
                f"Page index {page_number} is out of range "
                f"(0-{self.page_count - 1})"
            )

    def get_page(self, page_number: int) -> fitz.Page:

        self._validate_page_number(page_number)

        return self._document.load_page(page_number)



    def get_text(self, page_number: int) -> str:

        page = self.get_page(page_number)

    # First try native PDF text extraction
        text = cast(str, page.get_text("text")).strip()

        # If enough text exists, return it
        if len(text) > 20:

            # Plain stream-order text matches visual reading order on
            # every REDCap form page this pipeline handles, and all
            # existing extraction logic is tuned against exactly that
            # output — leave it untouched. Only on a genuine
            # multi-column table page (a pathology report) does the
            # stream order actually fail to keep a row's label/value/
            # reference together; reconstruct from word coordinates
            # only in that case.
            words = cast(list[Any], page.get_text("words"))
            items = [(w[0], w[1], w[2], w[3], w[4]) for w in words]

            if needs_row_reconstruction(items):

                reconstructed = reconstruct_reading_order(items)

                if reconstructed.strip():
                    return reconstructed

            return text

    # Otherwise use OCR fallback
        print(f"[OCR] Page {page_number + 1}")

        return self._ocr.extract(page).strip()


    def get_blocks(self, page_number: int) -> list[Any]:

        page = self.get_page(page_number)

        return cast(list[Any], page.get_text("blocks"))

    def get_words(self, page_number: int) -> list[Any]:

        page = self.get_page(page_number)

        return cast(list[Any], page.get_text("words"))

    def get_metadata(
        self,
        page_number: int,
    ) -> dict[str, Any]:

        page = self.get_page(page_number)

        return {
            "width": page.rect.width,
            "height": page.rect.height,
            "rotation": page.rotation,
        }

    def read(self) -> list[PageData]:

        pages: list[PageData] = []

        for index in range(self.page_count):

            pages.append(
                PageData(
                    page_number=index + 1,
                    text=self.get_text(index),
                    blocks=self.get_blocks(index),
                    words=self.get_words(index),
                    metadata=self.get_metadata(index),
                )
            )

        return pages

    def close(self) -> None:
        self._document.close()

    def __enter__(self) -> "PDFReader":
        return self

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ) -> None:
        self.close()