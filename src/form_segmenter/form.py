"""
Data model representing a logical REDCap form.

A Form is a collection of one or more consecutive PDF pages that
belong to the same REDCap form (e.g. SAE, Maternal History,
Daily Clinical Monitoring).

The Form model is produced by the Form Segmenter and consumed by
the Extractor.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from pdf_processor.page import PDFPage


class FormType(str, Enum):
    """
    Supported REDCap form types.
    """

    SAE = "Serious Adverse Event"
    MATERNAL = "Maternal History"
    DCM = "Daily Clinical Monitoring"
    NSS = "Neonatal Sepsis Surveillance"
    LAB = "Laboratory Reports"
    ATTACHMENT = "Hospital Attachment"
    UNKNOWN = "Unknown"


class Form(BaseModel):
    """
    Represents one complete REDCap form.

    Example
    -------
    SAE
        Page 1
        Page 2
        Page 3
        Page 4
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    form_type: FormType = Field(
        ...,
        description="Type of REDCap form.",
    )

    pages: list[PDFPage] = Field(
        default_factory=list,
        description="Pages belonging to this form.",
    )

    @property
    def start_page(self) -> int:
        """First page of the form."""
        return self.pages[0].page_number if self.pages else 0

    @property
    def end_page(self) -> int:
        """Last page of the form."""
        return self.pages[-1].page_number if self.pages else 0

    @property
    def page_count(self) -> int:
        """Number of pages in the form."""
        return len(self.pages)