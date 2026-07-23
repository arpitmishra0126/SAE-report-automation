"""
Data models for PDF pages.

This module defines the structured representation of a single page extracted
from a REDCap PDF. Every downstream module (form segmentation, extraction,
validation, etc.) will operate on these page objects instead of raw PDF pages.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PageData(BaseModel):
    """
    Represents a single extracted PDF page.

    Attributes:
        page_number: 1-based page number in the PDF.
        text: Extracted text content from the page.
        metadata: Optional metadata associated with the page.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    page_number: int = Field(
        ...,
        ge=1,
        description="1-based page number within the PDF.",
    )

    text: str = Field(
        default="",
        description="Extracted text from the page.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata for the page.",
    )