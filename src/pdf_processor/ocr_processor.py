"""
OCR fallback processor.

Uses PaddleOCR only when a PDF page has no extractable text.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import fitz
from paddleocr import PaddleOCR

from .layout import needs_row_reconstruction, reconstruct_reading_order


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
            items: list[tuple[float, float, float, float, str]] = []

            if result:
                for page_result in result:

                    if not page_result:
                        continue

                    for item in page_result:

                        try:
                            # Standard OCR output
                            box = item[0]
                            text = item[1][0]

                            if not text:
                                continue

                            text = text.strip()
                            lines.append(text)

                            xs = [point[0] for point in box]
                            ys = [point[1] for point in box]

                            items.append(
                                (min(xs), min(ys), max(xs), max(ys), text)
                            )

                        except (IndexError, TypeError):
                            # Ignore unexpected structures
                            continue

            # A scanned multi-column table (e.g. a pathology report
            # photographed/scanned directly, with no embedded PDF
            # text layer) needs the same row reconstruction as a
            # native-text table page. A normal single-column scanned
            # page keeps the existing plain top-to-bottom join
            # unchanged.
            if items and needs_row_reconstruction(items):

                reconstructed = reconstruct_reading_order(items)

                if reconstructed.strip():
                    return reconstructed

            return "\n".join(lines)

        finally:
            image_path.unlink(missing_ok=True)