"""
SAE data model.

Represents structured information extracted from the
Serious Adverse Event (SAE) REDCap form.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SAEData(BaseModel):
    """
    Structured representation of one SAE form.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    # ------------------------
    # Case Information
    # ------------------------

    record_id: str | None = Field(
        default=None,
        description="REDCap record ID.",
    )

    participant_id: str | None = Field(
        default=None,
        description="Study participant ID.",
    )

    site: str | None = Field(
        default=None,
        description="Study site.",
    )

    # ------------------------
    # Patient Information
    # ------------------------

    patient_name: str | None = Field(
        default=None,
        description="Patient's name.",
    )

    sex: str | None = Field(
        default=None,
        description="Patient's sex.",
    )

    age_days: int | None = Field(
        default=None,
        description="Patient's age in days.",
    )

    date_of_birth: str | None = Field(
        default=None,
        description="Patient's date of birth.",
    )

    # ------------------------
    # SAE Details
    # ------------------------

    event_date: str | None = Field(
        default=None,
        description="Date when adverse event started.",
    )

    event_description: str | None = Field(
        default=None,
    )

    diagnosis: str | None = Field(
        default=None,
    )

    seriousness: str | None = Field(
        default=None,
    )

    outcome: str | None = Field(
        default=None,
    )

    cause_of_death: str | None = Field(
        default=None,
    )

    # ------------------------
    # Hospital Information
    # ------------------------

    hospital_name: str | None = Field(
        default=None,
    )

    admission_date: str | None = Field(
        default=None,
        description="Hospital admission date and time.",
    )

    discharge_date: str | None = Field(
        default=None,
        description="Hospital discharge date.",
    )

    # ------------------------
    # Reporter
    # ------------------------

    reporter_name: str | None = Field(
        default=None,
    )

    reporting_date: str | None = Field(
        default=None,
        description="Form reporting date and time.",
    )