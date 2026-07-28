"""
OCR fallback processor.

Uses PaddleOCR only when a PDF page has no extractable text.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import fitz
from paddleocr import PaddleOCR


class OCRProcessor:
    """
    OCR fallback for scanned PDF pages.
    """

    def __init__(self) -> None:
        # Load OCR model once
        self.ocr = PaddleOCR(
            use_angle_cls=False,
            lang="en",
        )

    def extract(self, page: fitz.Page) -> str:
        """
        Extract text from a scanned PDF page using OCR.
        """

        pix = page.get_pixmap(
            dpi=300,
            alpha=False,
        )

        with tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        ) as tmp:
            image_path = Path(tmp.name)

        pix.save(str(image_path))

        try:
            # PaddleOCR 3.x
            result = self.ocr.ocr(str(image_path))

            lines: list[str] = []

            if result:
                for page_result in result:

                    if not page_result:
                        continue

                    for item in page_result:

                        try:
                            # Standard OCR output
                            text = item[1][0]

                            if text:
                                lines.append(text.strip())

                        except (IndexError, TypeError):
                            # Ignore unexpected structures
                            continue

            return "\n".join(lines)

        finally:
            image_path.unlink(missing_ok=True)