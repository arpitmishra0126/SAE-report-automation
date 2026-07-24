"""
SAE Case Summary document builder.
"""

from pathlib import Path

from docx.shared import Pt

from models.case_summary import CaseSummary

from .template import create_document


class DocumentBuilder:

    def build(
        self,
        summary: CaseSummary,
        output_file: str | Path,
    ) -> None:

        document = create_document()

        heading = document.add_heading(
            "Serious Adverse Event Case Summary",
            level=0,
        )

        heading.runs[0].font.size = Pt(16)

        document.add_heading(
            "Patient Information",
            level=1,
        )

        if summary.sae:

            document.add_paragraph(
                f"Record ID : {summary.sae.record_id}"
            )

            document.add_paragraph(
                f"Participant ID : {summary.sae.participant_id}"
            )

            document.add_paragraph(
                f"Hospital : {summary.sae.hospital_name}"
            )

        document.add_heading(
            "Maternal History",
            level=1,
        )

        if summary.maternal:

            document.add_paragraph(
                f"Mother : {summary.maternal.mother_name}"
            )

            document.add_paragraph(
                f"Delivery : {summary.maternal.delivery_type}"
            )

        document.add_heading(
            "Clinical Timeline",
            level=1,
        )

        for dcm in summary.dcm:

            document.add_paragraph(
                f"{dcm.monitoring_date} : {dcm.remarks}"
            )

        document.add_heading(
            "Outcome",
            level=1,
        )

        if summary.sae:

            document.add_paragraph(
                summary.sae.outcome or ""
            )

        document.save(str(output_file))