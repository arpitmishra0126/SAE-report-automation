"""
Data model representing a logical REDCap form.

A Form is a collection of one or more consecutive PDF pages that
belong to the same REDCap form (e.g. SAE, Maternal History,
Daily Clinical Monitoring).

Produced by the Form Segmenter and consumed by the Extractor.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from pdf_processor.page import PageData


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
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    form_type: FormType = Field(
        ...,
        description="Type of REDCap form.",
    )

    pages: list[PageData] = Field(
        default_factory=list,
        description="Pages belonging to this form.",
    )

    @property
    def start_page(self) -> int:
        """First page number."""
        return self.pages[0].page_number if self.pages else 0

    @property
    def end_page(self) -> int:
        """Last page number."""
        return self.pages[-1].page_number if self.pages else 0

    @property
    def page_count(self) -> int:
        """Number of pages."""
        return len(self.pages)

    @property
    def text(self) -> str:
        """
        Returns all page text concatenated.
        """
        return "\n".join(page.text for page in self.pages)

    @property
    def words(self):
        """
        Returns all words from every page.
        """
        words = []

        for page in self.pages:
            words.extend(page.words)

        return words

    @property
    def blocks(self):
        """
        Returns all text blocks from every page.
        """
        blocks = []

        for page in self.pages:
            blocks.extend(page.blocks)

        return blocks