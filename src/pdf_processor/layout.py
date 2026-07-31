"""
Layout-aware text reconstruction.

Plain "stream order" text extraction (PyMuPDF's "text" mode, or a raw
join of OCR detection results) concatenates text in whatever order
the source PDF/OCR engine happened to emit it. Existing extraction
logic (TextParser, the form-specific extractors) is tuned line-by-line
against exactly that stream order for REDCap form pages, where it
already happens to produce usable, correctly-interleaved text (a
question's label is immediately followed by its answer in the
stream) — even on pages that are, geometrically, laid out as a
label/value grid. That must not be touched.

For a genuine multi-column table (a pathology report's
Test / Value / Reference layout), the source PDF's content stream is
frequently authored column by column, so the stream dumps an entire
column's worth of labels, then an entire column's worth of values,
then an entire column's worth of reference ranges — despite each
label/value/range triple sitting on the same visual row. A label and
its value can end up dozens of tokens apart in the stream.

The distinguishing, directly-measurable signal is therefore not "does
this page have multiple x-clusters" (REDCap pages do too, and still
work) but "how far apart, in the *existing* stream order, do the
tokens that belong to the same visual row end up". On working REDCap
pages that gap stays small. On a column-major table dump it is large,
consistently, across many rows. `needs_row_reconstruction` measures
exactly that, so it only ever activates for pages where the current
extraction is actually broken.

When it does activate, `reconstruct_reading_order` rebuilds text in
row-major order: tokens are grouped into row bands by y-coordinate,
then ordered left-to-right within each band.
"""

from __future__ import annotations

# (x0, y0, x1, y1, text)
Item = tuple[float, float, float, float, str]


def _row_tolerance(items: list[Item]) -> float:

    heights = [it[3] - it[1] for it in items if it[3] > it[1]]

    tolerance = sorted(heights)[len(heights) // 2] / 2 if heights else 4.0

    return max(tolerance, 2.0)


def _group_rows(
    items: list[Item],
    row_tolerance: float | None = None,
) -> list[list[Item]]:
    """
    Group tokens into row bands by y-coordinate. Each row is returned
    x-sorted. Grouping is purely geometric — independent of whatever
    order `items` was passed in.
    """

    if not items:
        return []

    if row_tolerance is None:
        row_tolerance = _row_tolerance(items)

    ordered = sorted(items, key=lambda it: (it[1], it[0]))

    rows: list[list[Item]] = []

    for item in ordered:

        placed = False

        for row in rows:
            if abs(row[0][1] - item[1]) <= row_tolerance:
                row.append(item)
                placed = True
                break

        if not placed:
            rows.append([item])

    rows.sort(key=lambda row: min(it[1] for it in row))

    return [sorted(row, key=lambda it: it[0]) for row in rows]


def needs_row_reconstruction(
    items_in_stream_order: list[Item],
    min_stream_spread: int = 50,
    min_wide_rows: int = 5,
) -> bool:
    """
    True when the *existing* stream order already fails to keep a
    visual row's tokens close together — i.e. reconstruction would
    actually change/improve the result — for at least
    `min_wide_rows` distinct rows.

    `items_in_stream_order` must be in the same order the current
    plain-text extraction emits them in (e.g. straight from
    `page.get_text("words")`), since that order is exactly what's
    being evaluated.
    """

    if len(items_in_stream_order) < min_wide_rows * 2:
        return False

    stream_index = {
        id(item): index
        for index, item in enumerate(items_in_stream_order)
    }

    rows = _group_rows(items_in_stream_order)

    wide_rows = 0

    for row in rows:

        if len(row) < 2:
            continue

        positions = [stream_index[id(item)] for item in row]

        if max(positions) - min(positions) >= min_stream_spread:
            wide_rows += 1

    return wide_rows >= min_wide_rows


def reconstruct_reading_order(
    items: list[Item],
    row_tolerance: float | None = None,
) -> str:
    """
    Group tokens into row bands by y-coordinate and order each band
    left-to-right, returning row-major text (one output line per
    detected row).
    """

    if not items:
        return ""

    rows = _group_rows(items, row_tolerance)

    return "\n".join(
        " ".join(it[4] for it in row)
        for row in rows
    )
