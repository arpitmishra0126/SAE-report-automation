"""
Development utility to test PDF extraction.

This script:
1. Loads a sample REDCap PDF.
2. Extracts all pages.
3. Prints extraction statistics.
4. Flags suspicious pages.
5. Saves the extracted text for inspection.
"""

from pathlib import Path
from time import perf_counter

from pymupdf.pymupdf import annotations

from src.pdf_processor import PDFExtractor

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

PDF_PATH = Path("data/sample_pdfs/307-9-merged-merged-compressed.pdf")

OUTPUT_DIR = Path("outputs")
OUTPUT_FILE = OUTPUT_DIR / "307-9-extracted.txt"

from src.pdf_processor import PDFReader


def inspect_empty_pages(pdf_path: Path, empty_pages: list[int]) -> None:
    """
    Inspect pages where no text was extracted.
    """

    print("\n" + "=" * 60)
    print("EMPTY PAGE INSPECTION")
    print("=" * 60)

    with PDFReader(pdf_path) as reader:

        for page_number in empty_pages:

            page = reader.get_page(page_number - 1)
            metadata = reader.get_metadata(page_number - 1)

            image_count = len(page.get_images(full=True))
            drawing_count = len(page.get_drawings())
            annotations = page.annots()
            annotation_count = 0 if annotations is None else sum(1 for _ in annotations)

            print(
                f"Page {page_number:02d} | "
                f"Images: {image_count:2d} | "
                f"Drawings: {drawing_count:2d} | "
                f"Annotations: {annotation_count:2d} | "
                f"Size: {metadata['width']:.0f}×{metadata['height']:.0f}"
            )
# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------


def main() -> None:
    """Run PDF extraction and save results."""

    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

    print(f"\nReading PDF: {PDF_PATH.name}")

    start = perf_counter()

    extractor = PDFExtractor(PDF_PATH)
    pages = extractor.extract()

    elapsed = perf_counter() - start

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_characters = 0
    empty_pages = []

    print("\nPage-wise Extraction Report")
    print("-" * 60)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:

        for page in pages:

            text = page.text.strip()
            character_count = len(text)

            total_characters += character_count

            if character_count == 0:
                empty_pages.append(page.page_number)
                status = "EMPTY"

            elif character_count < 100:
                status = "LOW TEXT"

            else:
                status = "OK"

            print(
                f"Page {page.page_number:02d} | "
                f"{character_count:5d} chars | "
                f"{status}"
            )

            f.write("=" * 80 + "\n")
            f.write(f"PAGE {page.page_number}\n")
            f.write("=" * 80 + "\n\n")
            f.write(page.text)
            f.write("\n\n")

    print("\n" + "=" * 60)
    print("PDF EXTRACTION SUMMARY")
    print("=" * 60)

    print(f"PDF Name         : {PDF_PATH.name}")
    print(f"Pages Extracted  : {len(pages)}")
    print(f"Total Characters : {total_characters:,}")
    print(f"Extraction Time  : {elapsed:.2f} seconds")

    if empty_pages:
        print(f"Empty Pages      : {empty_pages}")
    else:
        print("Empty Pages      : None")

    print(f"\nOutput saved to:\n{OUTPUT_FILE.resolve()}")
    inspect_empty_pages(PDF_PATH, empty_pages)
    print("\nExtraction completed successfully.")

if __name__ == "__main__":
    main()