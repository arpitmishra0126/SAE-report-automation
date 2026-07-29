"""
Daily Clinical Monitoring model.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DCMData(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    monitoring_date: str | None = Field(default=None)

    # ------------------------
    # Status
    # ------------------------

    vital_status: str | None = Field(
        default=None,
        description="Current vital status of the newborn, e.g. Alive / Dead.",
    )

    discharged_or_referred: bool | None = Field(default=None)

    bed_sharing: bool | None = Field(default=None)

    # ------------------------
    # Weight
    # ------------------------

    weight_taken: bool | None = Field(default=None)

    weight: float | None = Field(default=None, description="grams.")

    weight_not_taken_reason: str | None = Field(default=None)

    # ------------------------
    # Support / interventions
    # ------------------------

    on_incubator_support: bool | None = Field(default=None)

    on_medications: bool | None = Field(default=None)

    medications: str | None = Field(
        default=None,
        description="Free-text medication list as recorded on the form.",
    )

    kmc_provided: bool | None = Field(default=None)

    kmc_not_provided_reason: str | None = Field(default=None)

    # ------------------------
    # Feeding
    # ------------------------

    feed_types: str | None = Field(
        default=None,
        description="Selected feed types, e.g. EBM, Formula, IV fluids, TPN.",
    )

    feed_route: str | None = Field(
        default=None,
        description="How feed was delivered, e.g. NG tube, direct breastfeeding, IV.",
    )

    enteral_feed_ml: float | None = Field(default=None, description="ml in last 24 hours.")

    tpn_ml: float | None = Field(default=None, description="ml in last 24 hours.")

    total_fluid_intake_ml: float | None = Field(default=None, description="ml in last 24 hours.")

    # ------------------------
    # Legacy / existing fields (kept for backward compatibility)
    # ------------------------

    feeding: str | None = Field(
        default=None,
        description="Raw feeding module text as originally captured.",
    )

    remarks: str | None = Field(default=None)
