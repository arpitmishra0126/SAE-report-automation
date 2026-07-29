"""
Laboratory report data model.

Represents structured information extracted from standalone
pathology/laboratory report forms (LAB form pages).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LabData(BaseModel):
    """
    Structured representation of one laboratory report.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    test_date: str | None = Field(default=None)

    lab_accession_no: str | None = Field(
        default=None,
        description="Reg/Ref number printed on the pathology report.",
    )

    collected_at: str | None = Field(default=None)

    tests_requested: str | None = Field(
        default=None,
        description="e.g. CBC, KFT, LFT, Electrolyte, CRP.",
    )

    # ------------------------
    # CBC
    # ------------------------

    hemoglobin: float | None = Field(default=None, description="g/dL.")

    tlc: float | None = Field(default=None, description="Total Leucocyte Count, cells/mm3.")

    platelet_count: float | None = Field(default=None, description="lakhs/mm3.")

    anc: float | None = Field(default=None, description="Absolute Neutrophil Count, x10^3/mm3.")

    # ------------------------
    # LFT
    # ------------------------

    total_bilirubin: float | None = Field(default=None, description="mg/dL.")

    direct_bilirubin: float | None = Field(default=None, description="mg/dL.")

    indirect_bilirubin: float | None = Field(default=None, description="mg/dL.")

    total_protein: float | None = Field(default=None, description="gm/dL.")

    albumin: float | None = Field(default=None, description="gm/dL.")

    globulin: float | None = Field(default=None, description="gm/dL.")

    alkaline_phosphatase: float | None = Field(default=None, description="IU/L.")

    # ------------------------
    # Electrolytes / KFT
    # ------------------------

    sodium: float | None = Field(default=None, description="meq/l.")

    potassium: float | None = Field(default=None, description="meq/l.")

    ionic_calcium: float | None = Field(default=None, description="mg/dL.")

    urea: float | None = Field(default=None, description="mg/dL.")

    creatinine: float | None = Field(default=None, description="mg/dL.")

    # ------------------------
    # CRP
    # ------------------------

    crp: float | None = Field(default=None, description="mg/L.")

    remarks: str | None = Field(default=None)
