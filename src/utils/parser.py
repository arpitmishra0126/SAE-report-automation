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

    # Lines that are PDF-viewer/REDCap chrome, never form content.
    # Stripped whole-line, before any label matching happens, so they
    # can never leak into an extracted field or into the LLM context.
    _CONTAMINATION_LINE_PATTERNS = [
        r"^\d{1,2}/\d{1,2}/\d{2,4},?\s*\d{1,2}:\d{2}\s*(AM|PM)\s*$",  # viewer timestamp
        r".*\|\s*REDCap\s*$",  # "ICMR Emollient - Main | REDCap" header
        r"^https?://\S+$",  # exported page URL
        r"^\d+\s*/\s*\d+$",  # page fraction footer, e.g. "2/3"
        r"^--\s*cancel\s*--$",
    ]

    _CONTAMINATION_RE = re.compile(
        "|".join(f"(?:{p})" for p in _CONTAMINATION_LINE_PATTERNS),
        flags=re.IGNORECASE,
    )

    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalize REDCap extracted text.
        """

        text = text.replace("\r", "")

        text = text.replace("\xa0", " ")

        # PDF ligature glyphs ("ﬁ", "ﬂ") extracted as single codepoints
        # rather than decomposed, e.g. "signiﬁcant", "ﬂuid".
        text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")

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

        lines = [
            line
            for line in text.splitlines()
            if not TextParser._CONTAMINATION_RE.match(line.strip())
        ]

        text = "\n".join(lines)

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

        # Checkbox/instructional chrome, never an answer.
        if re.match(
            r"^\(?(tick all|select all|multi-select)\b",
            lower,
        ):
            return None

        # Punctuation-only leftovers (e.g. a trailing "." after a label
        # once the label text itself has been stripped from the line).
        if not re.search(r"[A-Za-z0-9ऀ-ॿ]", value):
            return None

        return value

    # A new numbered question ("16 - What was..." / "6.2 - How many...")
    # marks the end of the previous question's answer region. Used to
    # stop a lookahead before it wanders into the next field's content.
    # Requires whitespace around the dash ("16 - What was...") so it
    # doesn't false-positive on hyphenated IDs/values like "12-0009-1".
    _QUESTION_BOUNDARY = re.compile(r"^\d+(?:\.\d+)?\s+[-–]\s+\S")

    _DEVANAGARI_TAIL = re.compile(r"[ऀ-ॿ]$")
    _DEVANAGARI_HEAD = re.compile(r"^[ऀ-ॿ]")
    _DEVANAGARI_ANY = re.compile(r"[ऀ-ॿ]")

    @staticmethod
    def _merge_wrapped_devanagari(
        value: str,
        lines: list[str],
        next_index: int,
    ) -> str:
        """
        This PDF export sometimes wraps a Devanagari conjunct cluster
        across a line break mid-word (e.g. "सेप्सि" / "स के कोई..."),
        rather than at a real word boundary. When the chosen answer
        line ends on a bare Devanagari character and the very next
        line picks straight back up in Devanagari with no leading
        space, it is the same word continuing — stitch it back
        together instead of returning the truncated fragment.
        """

        if next_index >= len(lines):
            return value

        if not TextParser._DEVANAGARI_TAIL.search(value):
            return value

        nxt = lines[next_index]

        if not nxt or nxt.startswith(" "):
            return value

        nxt_stripped = nxt.strip()

        if not nxt_stripped:
            return value

        if not TextParser._DEVANAGARI_HEAD.match(nxt_stripped):
            return value

        if (
            TextParser._QUESTION_BOUNDARY.match(nxt_stripped)
            or "[" in nxt_stripped
        ):
            return value

        return value + nxt_stripped

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

        label_is_ascii = label.isascii()

        for i, line in enumerate(lines):

            # A checkbox option line (single leading space) can never
            # itself be a question label — e.g. "CRP" also appears
            # inside the checkbox option "(CRP) (C-Reactive Protein)"
            # of an unrelated "which tests were planned" question. A
            # wrapped continuation of such an option ("व प्रोटीन
            # (CRP) ...") won't have that leading space, but for a
            # pure-English label it's still recognizable: it carries
            # Devanagari script, which a genuine English field-label
            # line in this export never does.
            if line.startswith(" "):
                continue

            match = pattern.search(line)

            if not match:
                continue

            if label_is_ascii and TextParser._DEVANAGARI_ANY.search(
                line[:match.start()]
            ):
                continue

            after = pattern.sub("", line, count=1).strip(" :-")

            j = i + 1
            skipped_translation = False

            # The English label is immediately followed by a Hindi (or
            # bilingual) translation note in square brackets. It may
            # close on the same line, or — because of PDF line wraps —
            # stay open and close several lines later. Either way it is
            # part of the question, never the answer, so consume it
            # whole rather than letting its leftover text become the
            # "value".
            if "[" in after:

                skipped_translation = True

                if "]" not in after:

                    while j < len(lines) and "]" not in lines[j]:
                        j += 1

                    j += 1

                after = ""

            elif after and re.fullmatch(r"\([^()]*\)", after):

                # A bare "(unit)" leftover, e.g. label "TLC Count
                # (mm³)" matched as "TLC Count" leaves "(mm³)" — a
                # unit annotation, not an answer. The real value is
                # the next line.
                after = ""

            elif after and i + 1 < len(lines):

                # If the *next* line continues in lowercase, the label
                # itself is only a prefix of a longer question that
                # wraps onto the next physical line (e.g. "...oxygen
                # saturation (SpO₂) in" / "percent? [...]"). In that
                # case "after" is a fragment of the question, not an
                # answer, so it must not be treated as the value.
                next_stripped = lines[i + 1].strip()

                if next_stripped[:1].islower():
                    after = ""

            if after:

                cleaned = TextParser._clean_candidate(after)

                if cleaned:
                    return TextParser._merge_wrapped_devanagari(
                        cleaned, lines, i + 1,
                    )

            limit = i + 12

            while j < len(lines) and j < limit:

                candidate = lines[j]
                stripped = candidate.strip()

                if not skipped_translation and "[" in stripped:

                    skipped_translation = True

                    if "]" not in stripped:

                        j += 1

                        while j < len(lines) and "]" not in lines[j]:
                            j += 1

                    j += 1
                    continue

                if TextParser._QUESTION_BOUNDARY.match(stripped):
                    # Ran into the next question with no answer found
                    # for this one — the field was left blank.
                    return None

                if (
                    not skipped_translation
                    and stripped
                    and (stripped[:1].islower() or stripped[0] == "(")
                ):
                    # Before the translation bracket/marker is reached,
                    # a lowercase-starting fragment is the label text
                    # itself wrapping onto the next line (e.g. "...in
                    # the maternal" / "sheet"), and a line starting
                    # with "(" is a parenthetical clarification (e.g.
                    # "(≥38°C)?", "(Yes, if Q4 ≥38℃)", "(Autogenerated)")
                    # — REDCap can stack several of these before the
                    # real answer. Neither is ever the answer itself.
                    j += 1
                    continue

                if candidate.startswith(" ") and stripped:
                    # A single leading space marks an unticked checkbox
                    # option in this REDCap export. The checkbox glyph
                    # itself is a graphic, not text, so a *ticked* box
                    # is rendered identically — there is no way to tell
                    # from the text layer which option (if any) was
                    # selected. Returning the first option here would
                    # silently fabricate an answer, so treat the field
                    # as not recoverable instead.
                    return None

                cleaned = TextParser._clean_candidate(candidate)

                if cleaned:
                    return TextParser._merge_wrapped_devanagari(
                        cleaned, lines, j + 1,
                    )

                j += 1

            return None

        return None

    @staticmethod
    def get_multiline_value(
        text: str,
        start_label: str,
        end_label: str | None = None,
    ) -> Optional[str]:

        text = TextParser.normalize(text)

        lines = text.splitlines()

        start_pattern = re.compile(
            re.escape(start_label),
            flags=re.IGNORECASE,
        )

        start_idx = None

        for i, line in enumerate(lines):

            if start_pattern.search(line):
                start_idx = i
                break

        if start_idx is None:
            return None

        end_pattern = (
            re.compile(re.escape(end_label), flags=re.IGNORECASE)
            if end_label
            else None
        )

        cleaned_lines: list[str] = []

        # The translation note in square brackets can begin on the
        # same physical line as the label itself.
        start_remainder = start_pattern.sub(
            "", lines[start_idx], count=1,
        )
        in_bracket = (
            "[" in start_remainder
            and "]" not in start_remainder.split("[", 1)[1]
        )

        for line in lines[start_idx + 1:]:

            if end_pattern and end_pattern.search(line):
                break

            stripped = line.strip()

            if in_bracket:

                if "]" in stripped:
                    in_bracket = False

                continue

            # A new numbered question means this field's answer region
            # has ended, whether or not anything was captured for it —
            # never bleed into the next question's content.
            if TextParser._QUESTION_BOUNDARY.match(stripped):
                break

            if "[" in stripped:

                if "]" not in stripped:
                    in_bracket = True

                continue

            if line.startswith(" ") and stripped:
                # Unticked checkbox option — the glyph that would show
                # which one (if any) was selected is a graphic, not
                # text, so it cannot be distinguished here.
                continue

            cleaned = TextParser._clean_candidate(line)

            if cleaned:
                cleaned_lines.append(cleaned)

        value = "\n".join(cleaned_lines).strip()

        return value or None

    # "25-09-2025" (REDCap export) or "25-Sep-2025" (typical pathology
    # report letterhead), either "/" or "-" separated.
    _DATE_PATTERN = (
        r"\d{2}[/-](?:\d{2}|[A-Za-z]{3})[/-]\d{4}"
    )

    @staticmethod
    def get_date(
        text: str,
        label: str,
    ) -> Optional[str]:

        text = TextParser.normalize(text)

        pattern = (
            rf"{re.escape(label)}"
            r".{0,300}?"
            rf"({TextParser._DATE_PATTERN})"
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
            rf"({TextParser._DATE_PATTERN}\s+\d{{1,2}}:\d{{2}}(?:\s*[AP]M)?)"
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
    def get_float(
        text: str,
        label: str,
    ) -> Optional[float]:

        value = TextParser.get_value(
            text,
            label,
        )

        if value is None:
            return None

        match = re.search(r"\d+(?:\.\d+)?", value)

        if match:
            return float(match.group())

        return None

    @staticmethod
    def get_bool(
        text: str,
        label: str,
    ) -> Optional[bool]:

        value = TextParser.get_value(
            text,
            label,
        )

        if value is None:
            return None

        lower = value.lower()

        has_no = re.search(r"(?:\bno\b|नहीं)", lower) is not None
        has_yes = re.search(r"(?:\byes\b|हाँ)", lower) is not None

        if has_no:
            return False

        if has_yes:
            return True

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