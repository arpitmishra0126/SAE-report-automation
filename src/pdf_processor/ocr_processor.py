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
            show_log=False,
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
            result = self.ocr.ocr(
                str(image_path),
                cls=False,
            )

            lines: list[str] = []

            if result and result[0]:
                for item in result[0]:
                    if len(item) >= 2:
                        text = item[1][0]
                        if text:
                            lines.append(text.strip())

            return "\n".join(lines)

        finally:
            image_path.unlink(missing_ok=True)