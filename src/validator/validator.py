"""
Case Summary validator.

Validates extracted data before document generation.
"""

from __future__ import annotations

from models.case_summary import CaseSummary


class Validator:
    """
    Validate extracted CaseSummary data.
    """

    def validate(self, summary: CaseSummary) -> CaseSummary:
        """
        Validate the extracted case summary.
        """

        messages: list[str] = []

        # -------------------------------------------------
        # SAE Validation
        # -------------------------------------------------

        if summary.sae:

            if not summary.sae.record_id:
                messages.append("Missing SAE Record ID.")

            if not summary.sae.participant_id:
                messages.append("Missing Participant ID.")

            if not summary.sae.event_date:
                messages.append("Missing SAE event date.")

            if not summary.sae.diagnosis:
                messages.append("Missing diagnosis.")

        else:
            messages.append("SAE form not found.")

        # -------------------------------------------------
        # Maternal Validation
        # -------------------------------------------------

        if summary.maternal:

            if not summary.maternal.mother_name:
                messages.append("Missing mother name.")

            if not summary.maternal.hospital_name:
                messages.append("Missing hospital name.")

        else:
            messages.append("Maternal History form not found.")

        # -------------------------------------------------
        # DCM Validation
        # -------------------------------------------------

        if summary.dcm:

            for index, dcm in enumerate(summary.dcm, start=1):

                if not dcm.monitoring_date:
                    messages.append(
                        f"Missing monitoring date in DCM record {index}."
                    )

        else:
            messages.append(
                "Daily Clinical Monitoring forms not found."
            )

        # -------------------------------------------------
        # NSS Validation
        # -------------------------------------------------

        if summary.nss:

            for index, nss in enumerate(summary.nss, start=1):

                if not nss.assessment_date:
                    messages.append(
                        f"Missing NSS assessment date in record {index}."
                    )

        else:
            messages.append(
                "Neonatal Sepsis Screening form not found."
            )
       
        # -------------------------------------------------
        # Finalize
        # -------------------------------------------------

        summary.validation_messages = messages

        return summary