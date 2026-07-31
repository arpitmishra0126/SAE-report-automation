"""
patient_record_builder.py

Converts a validated CaseSummary into a normalized PatientRecord.

Responsibilities
----------------
- Translate application models into AI-friendly dictionaries.
- Populate PatientRecord.
- Perform NO reasoning.
- Perform NO validation.
- Perform NO summarization.
"""

from models.case_summary import CaseSummary

from .patient_record import PatientRecord


class PatientRecordBuilder:
    """
    Builds a PatientRecord from a CaseSummary.
    """

    def build(self, summary: CaseSummary) -> PatientRecord:

        record = PatientRecord()

        # --------------------------------------------------
        # Core extracted forms
        # --------------------------------------------------

        if summary.sae:
            record.set_sae(summary.sae.model_dump())

        if summary.maternal:
            record.set_maternal(summary.maternal.model_dump())

        for dcm in summary.dcm:
            record.add_dcm(dcm.model_dump())

        for nss in summary.nss:
            record.add_nss(nss.model_dump())

        for lab in summary.lab:
            record.add_lab(lab.model_dump())

        # --------------------------------------------------
        # Derived application data
        # --------------------------------------------------

        record.set_timeline(summary.timeline)

        record.set_validation_messages(
            summary.validation_messages
        )

        # --------------------------------------------------
        # Metadata
        # --------------------------------------------------

        record.set_metadata(
            {
                "case_id": summary.case_id,
                "source_pdf": summary.source_pdf,
            }
        )

        return record