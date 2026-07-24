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

    vital_status: str | None = Field(default=None)

    weight: float | None = Field(default=None)

    medications: str | None = Field(default=None)

    feeding: str | None = Field(default=None)

    remarks: str | None = Field(default=None)