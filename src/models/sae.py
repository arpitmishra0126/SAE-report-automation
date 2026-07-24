"""
SAE data model.

Represents structured information extracted from the
Serious Adverse Event (SAE) REDCap form.
"""

from __future__ import annotations

from datetime import date

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
    )

    sex: str | None = Field(
        default=None,
    )

    age_days: int | None = Field(
        default=None,
    )

    date_of_birth: date | None = Field(
        default=None,
    )

    # ------------------------
    # SAE Details
    # ------------------------

    event_date: date | None = Field(
        default=None,
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

    admission_date: date | None = Field(
        default=None,
    )

    discharge_date: date | None = Field(
        default=None,
    )

    # ------------------------
    # Reporter
    # ------------------------

    reporter_name: str | None = Field(
        default=None,
    )

    reporting_date: date | None = Field(
        default=None,
    )