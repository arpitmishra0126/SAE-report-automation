"""
SAE Case Summary Automation Pipeline.

Entry point for the application.
"""

from __future__ import annotations

from pathlib import Path

from doc_generator import DocumentBuilder
from extractor import Extractor
from form_segmenter.detector import FormDetector
from models.case_summary import CaseSummary
from pdf_processor.pdf_reader import PDFReader
from validator import Validator


class SAEPipeline:
    """
    Complete SAE Case Summary pipeline.
    """

    def __init__(self) -> None:
        self._detector = FormDetector()
        self._extractor = Extractor()
        self._validator = Validator()
        self._builder = DocumentBuilder()

    def run(
        self,
        pdf_path: str | Path,
        output_path: str | Path | None = None,
    ) -> CaseSummary:
        """
        Execute the complete pipeline.

        Parameters
        ----------
        pdf_path:
            Path to REDCap exported PDF.

        output_path:
            Optional output DOCX path.

        Returns
        -------
        CaseSummary
        """

        pdf_path = Path(pdf_path)

        with PDFReader(pdf_path) as reader:
            pages = reader.read()

        forms = self._detector.segment(pages)

        summary = self._extractor.extract(forms)

        summary.source_pdf = pdf_path.name

        summary.case_id = (
            summary.sae.record_id
            if summary.sae
            else pdf_path.stem
        )

        summary = self._validator.validate(summary)

        if output_path is None:

            output_path = (
                pdf_path.parent
                / f"{summary.case_id}_SAE_Case_Summary.docx"
            )

        self._builder.build(
            summary,
            output_path,
        )

        return summary


def main() -> None:
    """
    Run the complete pipeline.
    """

    pdf = input("Enter PDF path: ").strip()

    pipeline = SAEPipeline()

    summary = pipeline.run(pdf)

    print("\n✓ Pipeline completed successfully.\n")

    print(f"Case ID : {summary.case_id}")
    print(f"Source  : {summary.source_pdf}")

    if summary.validation_messages:

        print("\nValidation Messages:")

        for message in summary.validation_messages:
            print(f" - {message}")

    else:
        print("\nNo validation issues detected.")

    print("\nDOCX generated successfully.")


if __name__ == "__main__":
    main()