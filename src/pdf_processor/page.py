"""
Data models for PDF pages.

Represents a single page extracted from a REDCap PDF.

The model stores both plain text and structured layout information
returned by PyMuPDF so downstream extractors can choose the most
appropriate representation.

Current users:
- Form Detector
- Extractors
- Validator

Future users:
- Coordinate-based field extraction
- Checkbox detection
- OCR fallback
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PageData(BaseModel):
    """
    Structured representation of a PDF page.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    page_number: int = Field(
        ...,
        ge=1,
        description="1-based page number.",
    )

    text: str = Field(
        default="",
        description="Plain text extracted from the page.",
    )

    blocks: list[Any] = Field(
        default_factory=list,
        description="PyMuPDF text blocks preserving layout.",
    )

    words: list[Any] = Field(
        default_factory=list,
        description="PyMuPDF word-level extraction with coordinates.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Page metadata.",
    )