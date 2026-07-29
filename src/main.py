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
from reasoning.context_builder import ContextBuilder
from reasoning.llm_reasoner import LLMReasoner
from reasoning.patient_record_builder import PatientRecordBuilder
from validator import Validator


class SAEPipeline:
    """
    Complete SAE Case Summary pipeline.
    """

    def __init__(self) -> None:

        # Existing pipeline
        self._detector = FormDetector()
        self._extractor = Extractor()
        self._validator = Validator()
        self._builder = DocumentBuilder()

        # AI reasoning pipeline
        self._record_builder = PatientRecordBuilder()
        self._context_builder = ContextBuilder()
        self._reasoner = LLMReasoner()

    def run(
        self,
        pdf_path: str | Path,
        output_path: str | Path | None = None,
    ) -> CaseSummary:

        pdf_path = Path(pdf_path)

        print("\n" + "=" * 80)
        print("STARTING SAE PIPELINE")
        print("=" * 80)

        # --------------------------------------------------
        # Read PDF
        # --------------------------------------------------

        print("\n[STEP 1/8] Reading PDF...")

        with PDFReader(pdf_path) as reader:
            pages = reader.read()

        print(f"✓ PDF read successfully ({len(pages)} pages)")

        # --------------------------------------------------
        # Detect Forms
        # --------------------------------------------------

        print("\n[STEP 2/8] Detecting forms...")

        forms = self._detector.segment(pages)

        print(f"✓ Form detection completed ({len(forms)} forms)")

        # --------------------------------------------------
        # Structured Extraction
        # --------------------------------------------------

        print("\n[STEP 3/8] Structured extraction...")

        summary = self._extractor.extract(forms)

        print("✓ Structured extraction completed")

        summary.source_pdf = pdf_path.name

        summary.case_id = (
            summary.sae.record_id
            if summary.sae
            else pdf_path.stem
        )

        # --------------------------------------------------
        # Validation
        # --------------------------------------------------

        print("\n[STEP 4/8] Validation...")

        try:
            summary = self._validator.validate(summary)
            print("✓ Validation completed")
        except Exception:
            print("❌ Validation failed")
            raise

        # --------------------------------------------------
        # Patient Record
        # --------------------------------------------------

        print("\n[STEP 5/8] Building PatientRecord...")

        try:
            record = self._record_builder.build(summary)
            print("✓ PatientRecordBuilder completed")
        except Exception:
            print("❌ PatientRecordBuilder failed")
            raise

        # --------------------------------------------------
        # Context
        # --------------------------------------------------

        print("\n[STEP 6/8] Building Context...")

        try:
            context = self._context_builder.build(record)
            print("✓ ContextBuilder completed")
        except Exception:
            print("❌ ContextBuilder failed")
            raise

        # --------------------------------------------------
        # LLM
        # --------------------------------------------------

        print("\n[STEP 7/8] Calling LLM...")

        try:
            clinical_report = self._reasoner.generate_report(context)
            print("✓ LLMReasoner completed")
        except Exception:
            print("❌ LLMReasoner failed")
            raise

        print("\n" + "=" * 70)
        print("AI CLINICAL REPORT")
        print("=" * 70)
        print(clinical_report.to_dict())

        # --------------------------------------------------
        # DOCX
        # --------------------------------------------------

        print("\n[STEP 8/8] Generating DOCX...")

        if output_path is None:
            output_path = (
                pdf_path.parent
                / f"{summary.case_id}_SAE_Case_Summary.docx"
            )

        self._builder.build(
            summary,
            output_path,
        )

        print("✓ DOCX generated")

        return summary


def main() -> None:

    pdf = Path(
        pdf = Path("data") / "sample_pdfs" / "307-9-merged-merged-compressed.pdf"
    )

    pipeline = SAEPipeline()

    try:

        summary = pipeline.run(pdf)

        print("\n" + "=" * 80)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 80)

        print(f"Case ID : {summary.case_id}")
        print(f"Source  : {summary.source_pdf}")

        if summary.validation_messages:

            print("\nValidation Messages:")

            for message in summary.validation_messages:
                print(f" - {message}")

        else:

            print("\nNo validation issues detected.")

        print("\nDOCX generated successfully.")

        print("\n" + "=" * 80)
        print("STRUCTURED DATA")
        print("=" * 80)

        print(summary.model_dump_json(indent=2))

    except Exception as e:

        print("\n" + "=" * 80)
        print("PIPELINE FAILED")
        print("=" * 80)

        print(type(e).__name__)
        print(e)

        raise


if __name__ == "__main__":
    main()