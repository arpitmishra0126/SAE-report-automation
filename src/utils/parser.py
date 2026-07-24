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

    _IGNORE_LINES = {
        "",
        "update",
        "complete",
        "switch",
        "reset",
        "-- cancel --",
    }

    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalize REDCap extracted text.
        """

        text = text.replace("\r", "")

        text = re.sub(r"[ \t]+", " ", text)

        text = re.sub(
            r"\*+\s*must provide value",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"use M icon next to field for missing values",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(r"\n{2,}", "\n", text)

        return text.strip()

    @staticmethod
    def exists(text: str, label: str) -> bool:
        text = TextParser.normalize(text)

        pattern = (
            rf"(?:\d+(?:\.\d+)?\s*[-–]\s*)?"
            rf"{re.escape(label)}"
        )

        return (
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            is not None
        )

    @staticmethod
    def _clean_candidate(value: str) -> Optional[str]:

        value = value.strip()

        if not value:
            return None

        lower = value.lower()

        if lower in TextParser._IGNORE_LINES:
            return None

        if "must provide value" in lower:
            return None

        if lower.startswith("http"):
            return None

        if lower.startswith("https"):
            return None

        if lower.startswith("record id"):
            return None

        if lower.startswith("icmr emollient"):
            return None

        return value

    @staticmethod
    def get_value(
        text: str,
        label: str,
    ) -> Optional[str]:

        text = TextParser.normalize(text)

        lines = text.splitlines()

        pattern = re.compile(
            rf"(?:\d+(?:\.\d+)?\s*[-–]\s*)?"
            rf"{re.escape(label)}",
            flags=re.IGNORECASE,
        )

        for i, line in enumerate(lines):

            if not pattern.search(line):
                continue

            after = pattern.sub("", line).strip(" :-")

            cleaned = TextParser._clean_candidate(after)

            if cleaned:
                return cleaned

            for candidate in lines[i + 1:i + 8]:

                cleaned = TextParser._clean_candidate(candidate)

                if cleaned:
                    return cleaned

        return None

    @staticmethod
    def get_multiline_value(
        text: str,
        start_label: str,
        end_label: str | None = None,
    ) -> Optional[str]:

        text = TextParser.normalize(text)

        start = re.search(
            re.escape(start_label),
            text,
            flags=re.IGNORECASE,
        )

        if not start:
            return None

        begin = start.end()

        if end_label:

            end = re.search(
                re.escape(end_label),
                text[begin:],
                flags=re.IGNORECASE,
            )

            if end:
                value = text[begin:begin + end.start()]
            else:
                value = text[begin:]

        else:
            value = text[begin:]

        cleaned_lines = []

        for line in value.splitlines():

            cleaned = TextParser._clean_candidate(line)

            if cleaned:
                cleaned_lines.append(cleaned)

        value = "\n".join(cleaned_lines).strip()

        return value or None

    @staticmethod
    def get_date(
        text: str,
        label: str,
    ) -> Optional[str]:

        text = TextParser.normalize(text)

        pattern = (
            rf"{re.escape(label)}"
            r".{0,300}?"
            r"(\d{2}[/-]\d{2}[/-]\d{4})"
        )

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if match:
            return match.group(1)

        return None

    @staticmethod
    def get_datetime(
        text: str,
        label: str,
    ) -> Optional[str]:

        text = TextParser.normalize(text)

        pattern = (
            rf"{re.escape(label)}"
            r".{0,300}?"
            r"(\d{2}[/-]\d{2}[/-]\d{4}\s+\d{2}:\d{2})"
        )

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if match:
            return match.group(1)

        return None

    @staticmethod
    def get_number(
        text: str,
        label: str,
    ) -> Optional[int]:

        value = TextParser.get_value(
            text,
            label,
        )

        if value is None:
            return None

        match = re.search(r"\d+", value)

        if match:
            return int(match.group())

        return None

    @staticmethod
    def get_all_matches(
        text: str,
        pattern: str,
    ) -> list[str]:

        return re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

    @staticmethod
    def clean(
        value: str | None,
    ) -> Optional[str]:

        if value is None:
            return None

        value = value.strip()

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        if value == "":
            return None

        return value