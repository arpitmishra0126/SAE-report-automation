"""
Text parsing utilities.

Provides reusable helper functions for extracting values
from REDCap PDF text.

Responsibilities
----------------
- Locate field labels.
- Extract values following labels.
- Provide safe parsing helpers.

This module intentionally does NOT:
- Detect forms.
- Perform OCR.
- Validate extracted values.
"""

from __future__ import annotations

import re
from typing import Optional


class TextParser:
    """
    Utility class for parsing REDCap page text.
    """

    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalize whitespace.

        Args:
            text:
                Raw extracted page text.

        Returns:
            Normalized text.
        """
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def get_value(text: str, label: str) -> Optional[str]:
        """
        Extract the value appearing immediately after a label.

        Example
        -------
        Hospital Name GSVM Medical College

        get_value(text, "Hospital Name")

        -> GSVM Medical College
        """

        pattern = rf"{re.escape(label)}\s*(.+)"

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        value = match.group(1).strip()

        if not value:
            return None

        return value

    @staticmethod
    def exists(text: str, label: str) -> bool:
        """
        Return True if a label exists.
        """

        return re.search(
            re.escape(label),
            text,
            flags=re.IGNORECASE,
        ) is not None

    @staticmethod
    def get_date(text: str, label: str) -> Optional[str]:
        """
        Extract a DD-MM-YYYY or DD/MM/YYYY date
        following a label.
        """

        pattern = (
            rf"{re.escape(label)}"
            r".*?"
            r"(\d{2}[-/]\d{2}[-/]\d{4})"
        )

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if not match:
            return None

        return match.group(1)

    @staticmethod
    def get_datetime(text: str, label: str) -> Optional[str]:
        """
        Extract a date-time value.

        Example
        -------
        25-09-2025 08:40
        """

        pattern = (
            rf"{re.escape(label)}"
            r".*?"
            r"(\d{2}[-/]\d{2}[-/]\d{4}\s+\d{2}:\d{2})"
        )

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if not match:
            return None

        return match.group(1)

    @staticmethod
    def get_number(text: str, label: str) -> Optional[int]:
        """
        Extract an integer value following a label.
        """

        pattern = (
            rf"{re.escape(label)}"
            r".*?"
            r"(\d+)"
        )

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if not match:
            return None

        return int(match.group(1))