"""
Master Case Summary model.

This module defines the top-level data structure used throughout the
SAE Case Summary Automation pipeline.

Responsibilities
----------------
- Aggregate data extracted from all REDCap forms.
- Store timeline information.
- Store validation messages.
- Serve as the input to the DOCX generator.

This module intentionally does NOT:
- Perform extraction.
- Perform validation.
- Generate reports.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .sae import SAEData
from .maternal import MaternalData
from .dcm import DCMData
from .nss import NSSData


class CaseSummary(BaseModel):
    """
    Complete structured representation of one SAE case.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    # ---------- Extracted Data ----------

    sae: SAEData | None = Field(
        default=None,
        description="Extracted Serious Adverse Event data.",
    )

    maternal: MaternalData | None = Field(
        default=None,
        description="Extracted maternal history data.",
    )

    dcm: list[DCMData] = Field(
        default_factory=list,
        description="Daily Clinical Monitoring records.",
    )

    nss: NSSData | None = Field(
        default=None,
        description="Neonatal Sepsis Surveillance data.",
    )

    # ---------- Derived Information ----------

    timeline: list[str] = Field(
        default_factory=list,
        description="Chronological timeline of significant clinical events.",
    )

    # ---------- Validation ----------

    validation_messages: list[str] = Field(
        default_factory=list,
        description="Validation warnings or missing-field messages.",
    )

    # ---------- Metadata ----------

    source_pdf: str | None = Field(
        default=None,
        description="Source PDF filename.",
    )

    case_id: str | None = Field(
        default=None,
        description="Case identifier.",
    )