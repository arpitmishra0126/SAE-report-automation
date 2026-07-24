"""
Neonatal Sepsis Surveillance model.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class NSSData(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    assessment_date: str | None = Field(default=None)

    diagnosis: str | None = Field(default=None)

    culture_result: str | None = Field(default=None)

    treatment: str | None = Field(default=None)

    outcome: str | None = Field(default=None)

    remarks: str | None = Field(default=None)