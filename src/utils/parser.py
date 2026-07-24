"""
Utility functions for parsing REDCap PDF text.

Responsibilities
----------------
- Normalize extracted text.
- Extract values by label.
- Extract multiline values.
- Extract dates, datetimes and numbers.
- Check whether labels exist.
"""

from __future__ import annotations

import re
from typing import Optional


class TextParser:
    """
    Generic parser for REDCap PDF text.
    """

    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalize whitespace.
        """
        text = text.replace("\r", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{2,}", "\n", text)

        return text.strip()

    @staticmethod
    def exists(text: str, label: str) -> bool:
        """
        Check whether a label exists.
        """
        return re.search(
            re.escape(label),
            text,
            flags=re.IGNORECASE,
        ) is not None

    @staticmethod
    def get_value(text: str, label: str) -> Optional[str]:
        """
        Extract the first non-empty line following a label.

        Example
        -------
        Hospital Name
        GSVM Medical College

        ->
        GSVM Medical College
        """

        text = TextParser.normalize(text)

        pattern = (
            rf"{re.escape(label)}"
            r"\s*\n?"
            r"([^\n]+)"
        )

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        value = match.group(1).strip()

        return value or None

    @staticmethod
    def get_multiline_value(
        text: str,
        start_label: str,
        end_label: str | None = None,
    ) -> Optional[str]:
        """
        Extract multiline text.

        If end_label is provided,
        extraction stops before it.
        """

        text = TextParser.normalize(text)

        if end_label:

            pattern = (
                rf"{re.escape(start_label)}"
                r"(.*?)"
                rf"{re.escape(end_label)}"
            )

        else:

            pattern = (
                rf"{re.escape(start_label)}"
                r"(.*)"
            )

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if not match:
            return None

        value = match.group(1).strip()

        return value or None

    @staticmethod
    def get_date(
        text: str,
        label: str,
    ) -> Optional[str]:
        """
        Extract a date.

        Supports:
        DD-MM-YYYY
        DD/MM/YYYY
        """

        pattern = (
            rf"{re.escape(label)}"
            r".*?"
            r"(\d{2}[/-]\d{2}[/-]\d{4})"
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
    def get_datetime(
        text: str,
        label: str,
    ) -> Optional[str]:
        """
        Extract a date-time.

        Example

        25-09-2025 08:40
        """

        pattern = (
            rf"{re.escape(label)}"
            r".*?"
            r"(\d{2}[/-]\d{2}[/-]\d{4}\s+\d{2}:\d{2})"
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
    def get_number(
        text: str,
        label: str,
    ) -> Optional[int]:
        """
        Extract an integer.
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

    @staticmethod
    def get_all_matches(
        text: str,
        pattern: str,
    ) -> list[str]:
        """
        Return every regex match.
        """

        return re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

    @staticmethod
    def clean(value: str | None) -> Optional[str]:
        """
        Final cleanup.
        """

        if value is None:
            return None

        value = value.strip()

        if value == "":
            return None

        return value