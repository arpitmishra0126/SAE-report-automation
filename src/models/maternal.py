"""
Maternal History data model.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MaternalData(BaseModel):
    """
    Structured maternal history information.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    mother_name: str | None = Field(default=None)

    father_name: str | None = Field(default=None)

    mother_age: int | None = Field(default=None)

    hospital_name: str | None = Field(default=None)

    hospital_reg_no: str | None = Field(default=None)

    baby_uid: str | None = Field(default=None)

    gestational_age: str | None = Field(default=None)

    delivery_type: str | None = Field(default=None)

    labour_type: str | None = Field(default=None)

    maternal_remarks: str | None = Field(default=None)