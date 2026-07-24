
from __future__ import annotations
from pathlib import Path
from .page import PDFPage
from .pdf_reader import PDFReader

class PDFExtractor:
    """
    Extracts page-wise text from a PDF document.
    """

    def __init__(self, pdf_path: str | Path) -> None:
        self.pdf_path = Path(pdf_path)
    def extract(self) -> list[PDFPage]:

        extracted_pages: list[PDFPage] = []
        with PDFReader(self.pdf_path) as reader:
            for page_index in range(reader.page_count):
                text = reader.get_text(page_index)
                metadata = reader.get_metadata(page_index)

                page_data = PDFPage(source_file=self.pdf_path.name, page_number=page_index + 1, text=text.strip(), metadata=metadata)
                extracted_pages.append(page_data)
        return extracted_pages