from __future__ import annotations

from pathlib import Path

from .page import PageData
from .pdf_reader import PDFReader


class PDFExtractor:
    """
    Extract page-wise information from a PDF document.
    """

    def __init__(self, pdf_path: str | Path) -> None:
        self.pdf_path = Path(pdf_path)

    def extract(self) -> list[PageData]:
        """
        Read the PDF and return a list of PageData objects.
        """

        extracted_pages: list[PageData] = []

        with PDFReader(self.pdf_path) as reader:

            for page_index in range(reader.page_count):

                page_data = PageData(
                    page_number=page_index + 1,
                    text=reader.get_text(page_index),
                    blocks=reader.get_blocks(page_index),
                    words=reader.get_words(page_index),
                    metadata=reader.get_metadata(page_index),
                )

                extracted_pages.append(page_data)

        return extracted_pages