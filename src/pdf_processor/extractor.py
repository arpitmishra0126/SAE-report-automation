
from __future__ import annotations
from pathlib import Path
from .page import PageData
from .pdf_reader import PDFReader

class PDFExtractor:
    """
    Extracts page-wise text from a PDF document.
    """

    def __init__(self, pdf_path: str | Path) -> None:
        self.pdf_path = Path(pdf_path)
    def extract(self) -> list[PageData]:

        extracted_pages: list[PageData] = []
        with PDFReader(self.pdf_path) as reader:
            for page_index in range(reader.page_count):
                text = reader.get_text(page_index)
                metadata = reader.get_metadata(page_index)

                page_data = PageData(page_number=page_index + 1,text=text.strip(),metadata=metadata)
                extracted_pages.append(page_data)
        return extracted_pages