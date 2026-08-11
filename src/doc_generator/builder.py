"""
SAE Case Summary document builder.

Renders the pipeline's structured `CaseSummary` and AI-generated
`ClinicalReport` as a "Clinical Case Narrative" — prose paragraphs
organized chronologically under fixed headings, not field/value
tables.

Narrative text is synthesized here, in plain Python, directly from
already-extracted structured data (`CaseSummary`) and the LLM's own
already-generated narrative field (`ClinicalReport.executive_summary`
/ `.final_outcome`, used as optional lead-ins). No LLM call is made
from this module and no extraction/reasoning logic is touched — this
is presentation only. A clause is written only when the underlying
field is actually present; nothing here invents a clinical fact, a
date, a diagnosis, or an outcome, and a document with fewer records
(or none at all) produces a correspondingly shorter narrative rather
than a differently-shaped one.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from models.case_summary import CaseSummary
from models.dcm import DCMData
from models.lab import LabData
from models.maternal import MaternalData
from models.nss import NSSData

from .template import create_document

try:
    from reasoning.report import ClinicalReport
except ImportError:  # pragma: no cover - reasoning package optional at import time
    ClinicalReport = None  # type: ignore[assignment, misc]


# --------------------------------------------------------------
# Value formatting
# --------------------------------------------------------------

# Known source-form sentinel values that must never be presented as a
# genuine clinical measurement. NSSData.respiratory_rate's own
# docstring documents 9999 as meaning "ventilated / not assessable",
# not an actual breaths-per-minute reading.
_SENTINELS: dict[str, set[float]] = {
    "respiratory_rate": {9999},
}


def _clean(value: Any) -> str | None:
    """A present, non-empty display string for `value`, or None."""

    if value is None:
        return None

    if isinstance(value, bool):
        return "yes" if value else "no"

    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None

    if isinstance(value, float):
        # A whole-number reading (e.g. weight 1490.0) reads more
        # naturally in prose as "1490" than "1490.0"; a genuine
        # decimal reading (e.g. temperature 37.2) is left as-is.
        return str(int(value)) if value.is_integer() else str(value)

    return str(value)


def _field(record: Any, field_name: str) -> str | None:
    """
    `_clean(record.<field_name>)`, but returns None for a value that
    is a documented sentinel/placeholder rather than a real reading.
    """

    if record is None:
        return None

    value = getattr(record, field_name, None)

    if value is not None and value in _SENTINELS.get(field_name, set()):
        return None

    return _clean(value)


_DATE_FORMATS = (
    "%d-%m-%Y %H:%M",
    "%d-%m-%Y",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
    "%d-%b-%Y %H:%M",
    "%d-%b-%Y",
)


def _parse_date(value: str | None) -> date | None:

    if not value:
        return None

    text = value.strip()

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    return None


# --------------------------------------------------------------
# OCR / extraction artifact cleanup for free-text remarks
# --------------------------------------------------------------

_SENTENCE_END = (".", "!", "?", "।")


def _dedupe_repeated_phrase(text: str) -> str:
    """
    Collapses a phrase that repeats immediately back-to-back at the
    start of the text — an observed extraction artifact where a DCM
    and NSS remark are near-duplicates and end up concatenated, e.g.
    "Baby severe Baby severe today" -> "Baby severe today".
    """

    words = text.split()
    n = len(words)

    for k in range(n // 2, 0, -1):
        if words[:k] == words[k:2 * k]:
            return " ".join(words[:k] + words[2 * k:])

    return text


# A REDCap question header leaking into a free-text field looks like
# "22- Please enter..." / "20-Is the..." / "25-In your opinion...":
# digit(s), then a dash or comma, then a capitalized word. Two or
# more of these inside one field is a reliable sign that raw,
# scrambled form text was captured instead of the intended answer
# (a known artifact on badly-OCR'd multi-column source pages) — the
# whole field is unsafe to reproduce, not just a trailing fragment.
_FORM_QUESTION_FRAGMENT = re.compile(r"\b\d{1,2}(?:\.\d+)?\s*[-,]\s*[A-Z]")


def _is_garbled_form_dump(text: str) -> bool:
    return len(_FORM_QUESTION_FRAGMENT.findall(text)) >= 2


def _clean_remark(text: str | None) -> str | None:
    """
    Cleanup for a free-text remark/description before it is embedded
    in the narrative: omits the value entirely if it looks like a
    scrambled dump of raw form text; otherwise collapses an
    immediately repeated phrase, and trims a trailing one-or-two
    -character fragment with no sentence-ending punctuation — the
    signature of a mid-word OCR truncation (e.g. "...severe today L").
    This never invents a completion; a cleaned remark is only ever
    shorter than the source, never rewritten or extended.
    """

    cleaned = _clean(text)

    if not cleaned:
        return None

    if _is_garbled_form_dump(cleaned):
        return None

    cleaned = _dedupe_repeated_phrase(cleaned)

    words = cleaned.split()

    if words:
        last = words[-1]
        core = last.rstrip(".,;:")
        if len(core) <= 2 and last[-1:] not in _SENTENCE_END:
            words = words[:-1]

    cleaned = " ".join(words).strip()

    return cleaned if len(cleaned) >= 3 else None


# --------------------------------------------------------------
# Document primitives
# --------------------------------------------------------------


def _join_sentences(sentences: list[str]) -> str:
    """
    Joins clause/sentence fragments into one paragraph, ensuring each
    ends with terminal punctuation first — a fragment sourced
    verbatim from extracted data (e.g. an event description) may not
    end in a period, and joining it directly onto the next sentence
    would otherwise run the two together.
    """

    finished = []

    for sentence in sentences:

        text = sentence.strip()

        if not text:
            continue

        if text[-1] not in _SENTENCE_END:
            text += "."

        finished.append(text)

    return " ".join(finished)


def _paragraph(document: DocxDocument, text: str, *, italic: bool = False):

    paragraph = document.add_paragraph(text)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.line_spacing = 1.08

    if italic and paragraph.runs:
        paragraph.runs[0].italic = True

    return paragraph


def _section_heading(document: DocxDocument, text: str) -> None:

    document.add_heading(text, level=1)


# --------------------------------------------------------------
# Title / identification
# --------------------------------------------------------------


def _title_block(document: DocxDocument, summary: CaseSummary) -> None:

    sae = summary.sae
    maternal = summary.maternal

    hospital = _field(sae, "hospital_name") or _field(maternal, "hospital_name")
    record_id = _field(sae, "record_id") or _clean(summary.case_id)

    title_parts = ["ICMR Emollient Study"]

    if hospital:
        title_parts.append(hospital)

    if record_id:
        title_parts.append(f"Record ID: {record_id}")

    title = document.add_heading(" | ".join(title_parts), level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subtitle = document.add_paragraph("Clinical Case Narrative")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(8)

    if subtitle.runs:
        subtitle.runs[0].bold = True
        subtitle.runs[0].font.size = Pt(13)


def _identification_block(document: DocxDocument, summary: CaseSummary) -> None:

    sae = summary.sae
    maternal = summary.maternal

    baby_ref = _field(sae, "patient_name")

    if not baby_ref and maternal and _field(maternal, "mother_name"):
        baby_ref = f"Baby of {_field(maternal, 'mother_name')}"

    hospital = _field(sae, "hospital_name") or _field(maternal, "hospital_name")

    line1_parts = [part for part in [baby_ref, "ICMR Emollient Study", hospital] if part]

    if line1_parts:
        _paragraph(document, "  |  ".join(line1_parts), italic=True)

    record_id = _field(sae, "record_id") or _clean(summary.case_id)
    uid = _field(maternal, "baby_uid")

    line2_parts = []

    if record_id:
        line2_parts.append(f"Record ID: {record_id}")

    if uid:
        line2_parts.append(f"UID: {uid}")

    if line2_parts:
        _paragraph(document, "  |  ".join(line2_parts), italic=True)


# --------------------------------------------------------------
# Section 1 — Maternal History
# --------------------------------------------------------------


def _maternal_narrative(maternal: MaternalData) -> str | None:
    """
    Synthesizes maternal history into flowing prose from whichever
    fields are actually present. Built deterministically (rather than
    relying solely on the LLM's narrative) so that every available
    field is guaranteed to be represented, for any future document.
    """

    sentences: list[str] = []

    name = _field(maternal, "mother_name")

    parity_term = None
    if maternal.gravida == 1:
        parity_term = "primigravida"
    elif maternal.gravida is not None and maternal.gravida > 1:
        parity_term = "multigravida"

    gp_bits = []
    if maternal.gravida is not None:
        gp_bits.append(f"G{maternal.gravida}")
    if maternal.para is not None:
        gp_bits.append(f"P{maternal.para}")
    gp_text = "".join(gp_bits) or None

    if name:
        opening = name
        if maternal.mother_age is not None:
            opening += f", a {maternal.mother_age}-year-old"
            if parity_term:
                opening += f" {parity_term}"
            opening += " mother"
        elif parity_term:
            opening += f", a {parity_term} mother"
    elif parity_term:
        opening = f"The mother, a {parity_term},"
    else:
        opening = "The mother"

    if gp_text:
        opening += f" ({gp_text})"

    father = _field(maternal, "father_name")
    if father:
        opening += f", father {father},"

    hospital = _field(maternal, "hospital_name")
    if hospital:
        opening += f" was managed at {hospital}"

    sentences.append(opening.strip().rstrip(",") + ".")

    if maternal.corticosteroids_given is True:
        steroid = "Antenatal corticosteroids were administered"
        details = []
        if _field(maternal, "steroid_type"):
            details.append(_field(maternal, "steroid_type"))
        if maternal.steroid_doses is not None:
            details.append(f"{maternal.steroid_doses} doses")
        if details:
            steroid += " (" + ", ".join(details) + ")"
        sentences.append(steroid + ".")
    elif maternal.corticosteroids_given is False:
        sentences.append("Antenatal corticosteroids were not administered.")

    if _field(maternal, "fever_history"):
        sentences.append(
            f"Fever history during pregnancy/labour was documented as "
            f"{_field(maternal, 'fever_history')}."
        )

    risk_bits = []

    if maternal.foul_smelling_discharge is True:
        risk_bits.append("foul-smelling vaginal discharge")

    if maternal.uterine_tenderness is True:
        risk_bits.append("uterine tenderness")

    if maternal.pprom_over_24h is True:
        risk_bits.append("leaking per vaginum for more than 24 hours (PPROM >24h)")

    if maternal.foetal_distress is True:
        risk_bits.append("foetal distress")

    if risk_bits:
        sentences.append("Antenatal/intrapartum findings included " + ", ".join(risk_bits) + ".")

    if _field(maternal, "amniotic_fluid_appearance"):
        sentences.append(
            f"Amniotic fluid at delivery was {_field(maternal, 'amniotic_fluid_appearance')}."
        )

    labour_bits = []

    if _field(maternal, "labour_type"):
        labour_bits.append(f"labour type {_field(maternal, 'labour_type')}")

    if _field(maternal, "labour_course"):
        labour_bits.append(f"course {_field(maternal, 'labour_course')}")

    if labour_bits:
        sentences.append("Labour: " + ", ".join(labour_bits) + ".")

    delivery_bits = []

    if _field(maternal, "delivery_type"):
        delivery_bits.append(f"delivered by {_field(maternal, 'delivery_type')}")
    elif _field(maternal, "delivery_mode"):
        delivery_bits.append(f"delivered by {_field(maternal, 'delivery_mode')}")

    if _field(maternal, "presentation"):
        delivery_bits.append(f"{_field(maternal, 'presentation')} presentation")

    if _field(maternal, "delivery_attendant"):
        delivery_bits.append(f"assisted by {_field(maternal, 'delivery_attendant')}")

    if delivery_bits:
        sentences.append("The baby was " + ", ".join(delivery_bits) + ".")

    if _field(maternal, "gestational_age"):
        sentences.append(f"Gestational age was documented as {_field(maternal, 'gestational_age')}.")

    screening_bits = []

    if _field(maternal, "blood_group"):
        screening_bits.append(f"blood group {_field(maternal, 'blood_group')}")

    if _field(maternal, "vdrl"):
        screening_bits.append(f"VDRL {_field(maternal, 'vdrl')}")

    if _field(maternal, "hbsag"):
        screening_bits.append(f"HBsAg {_field(maternal, 'hbsag')}")

    if _field(maternal, "hiv_status"):
        screening_bits.append(f"HIV status {_field(maternal, 'hiv_status')}")

    if maternal.pih is True:
        screening_bits.append("pregnancy-induced hypertension")

    if maternal.gdm is True:
        screening_bits.append("gestational diabetes mellitus")

    if _field(maternal, "thyroid_status"):
        screening_bits.append(f"thyroid status {_field(maternal, 'thyroid_status')}")

    if maternal.oligohydramnios is True:
        screening_bits.append("oligohydramnios")

    if _field(maternal, "amniotic_fluid_volume"):
        screening_bits.append(f"amniotic fluid volume {_field(maternal, 'amniotic_fluid_volume')}")

    if screening_bits:
        sentences.append("Antenatal screening/status: " + ", ".join(screening_bits) + ".")

    other_bits = []

    if _field(maternal, "illness_history"):
        other_bits.append(f"illness history: {_field(maternal, 'illness_history')}")

    if _field(maternal, "epilepsy_radiation_drug_history"):
        other_bits.append(
            f"epilepsy/radiation/drug history: {_field(maternal, 'epilepsy_radiation_drug_history')}"
        )

    if maternal.aph is True:
        other_bits.append("antepartum haemorrhage")

    if other_bits:
        sentences.append("Other relevant history: " + "; ".join(other_bits) + ".")

    remark = _clean_remark(_field(maternal, "maternal_remarks"))

    if maternal.significant_maternal_info_flag is True:
        sentence = "Significant maternal information was flagged"
        sentence += f": {remark}." if remark else "."
        sentences.append(sentence)
    elif remark:
        sentences.append(remark)

    return _join_sentences(sentences) if sentences else None


def _section_maternal_history(document: DocxDocument, summary: CaseSummary, clinical_report) -> None:

    _section_heading(document, "1. Maternal History")

    narrative = _maternal_narrative(summary.maternal) if summary.maternal else None

    if not narrative and clinical_report:
        narrative = _clean(getattr(clinical_report, "maternal_history", None))

    _paragraph(document, narrative or "No maternal history data was available for this case.")


# --------------------------------------------------------------
# Section 2 — Day-wise Clinical Course
# --------------------------------------------------------------


def _group_by_day(
    dcm_records: list[DCMData],
    nss_records: list[NSSData],
) -> list[tuple[int, str | None, DCMData | None, NSSData | None]]:
    """
    Groups DCM and NSS records that fall on the same calendar day,
    sorted chronologically, and numbered Day 1, Day 2, ... Records
    whose date cannot be parsed are still included, ordered after
    every dated record, using their own raw date string as the
    grouping key so they are never silently dropped. The number of
    days produced is entirely a function of the input records.
    """

    days: dict[str, dict[str, Any]] = {}

    def register(records: list, date_field: str, kind: str) -> None:

        for record in records:

            raw_date = getattr(record, date_field, None)
            parsed = _parse_date(raw_date)
            key = parsed.isoformat() if parsed else f"unparsed::{raw_date or id(record)}"

            bucket = days.setdefault(
                key, {"dcm": None, "nss": None, "display_date": raw_date, "sort_date": parsed}
            )
            bucket[kind] = record

            if raw_date and not bucket.get("display_date"):
                bucket["display_date"] = raw_date

    register(dcm_records, "monitoring_date", "dcm")
    register(nss_records, "assessment_date", "nss")

    def sort_key(item: tuple[str, dict[str, Any]]):
        _, bucket = item
        sort_date = bucket["sort_date"]
        return (0, sort_date) if sort_date else (1, bucket["display_date"] or "")

    ordered = sorted(days.items(), key=sort_key)

    return [
        (index, bucket["display_date"], bucket["dcm"], bucket["nss"])
        for index, (_, bucket) in enumerate(ordered, start=1)
    ]


def _ventilation_level(nss: NSSData | None) -> int | None:

    if nss is None:
        return None

    if nss.on_invasive_ventilator:
        return 2

    if nss.on_noninvasive_ventilator:
        return 1

    if nss.on_invasive_ventilator is False and nss.on_noninvasive_ventilator is False:
        return 0

    return None


_SEPSIS_PATTERNS: list[tuple[int, tuple[str, ...]]] = [
    (2, ("confirmed sepsis",)),
    (1, ("probable sepsis", "suspected sepsis")),
    (0, ("no signs of sepsis", "no sign of sepsis", "no evidence of sepsis")),
]

_SEPSIS_LABELS = {0: "no signs of sepsis", 1: "probable sepsis", 2: "confirmed sepsis"}


def _sepsis_rank(text: str | None) -> int | None:

    if not text:
        return None

    lowered = text.lower()

    for rank, keywords in _SEPSIS_PATTERNS:
        if any(keyword in lowered for keyword in keywords):
            return rank

    return None


# Compact labels for table cells (the narrative sentence forms above
# read naturally in prose but are too verbose repeated in every row).
_VENTILATION_LABELS_SHORT = {
    0: "Not on ventilatory support",
    1: "On non-invasive ventilatory support",
    2: "On invasive mechanical ventilation",
}


def _ventilation_cell_clause(level: int | None, previous: int | None) -> str | None:

    if level is None:
        return None

    label = _VENTILATION_LABELS_SHORT[level]

    if previous is not None and level > previous:
        return f"{label} (escalated)"

    if previous is not None and level < previous:
        return f"{label} (de-escalated)"

    return label


def _sepsis_cell_clause(text: str | None, previous_rank: int | None) -> str | None:

    if not text:
        return None

    rank = _sepsis_rank(text)

    if rank is None:
        return f"Sepsis impression: {text}"

    suffix = ""

    if previous_rank is not None and rank > previous_rank:
        suffix = " (escalated)"
    elif previous_rank is not None and rank < previous_rank:
        suffix = " (improved)"

    return f"Sepsis impression: {_SEPSIS_LABELS[rank]}{suffix}"


def _dcm_cell_text(dcm: DCMData | None) -> str:
    """
    Synthesized (not raw-dumped) Daily Clinical Monitoring cell
    content for one day's table row.
    """

    if dcm is None:
        return "No DCM record for this day."

    clauses: list[str] = []

    if _field(dcm, "vital_status"):
        clauses.append(_field(dcm, "vital_status"))

    if dcm.weight is not None:
        clauses.append(f"Wt {_clean(dcm.weight)} g")
    elif dcm.weight_taken is False:
        reason = _field(dcm, "weight_not_taken_reason")
        clauses.append("Weight not recorded" + (f" ({reason})" if reason else ""))

    if dcm.on_incubator_support is True:
        clauses.append("On incubator support")
    elif dcm.on_incubator_support is False:
        clauses.append("Not on incubator support")

    if _field(dcm, "medications"):
        clauses.append(f"Meds: {_field(dcm, 'medications')}")

    feed_bits = []

    if _field(dcm, "feed_types"):
        feed_bits.append(_field(dcm, "feed_types"))

    if _field(dcm, "feed_route"):
        feed_bits.append(f"via {_field(dcm, 'feed_route')}")

    if dcm.enteral_feed_ml is not None:
        feed_bits.append(f"{_clean(dcm.enteral_feed_ml)} ml enteral")

    if dcm.total_fluid_intake_ml is not None:
        feed_bits.append(f"total fluid {_clean(dcm.total_fluid_intake_ml)} ml")

    if feed_bits:
        clauses.append("Feeds: " + ", ".join(feed_bits))

    if dcm.kmc_provided is True:
        clauses.append("KMC provided")
    elif dcm.kmc_provided is False:
        reason = _field(dcm, "kmc_not_provided_reason")
        clauses.append("No KMC" + (f" ({reason})" if reason else ""))

    remark = _clean_remark(_field(dcm, "remarks"))

    if remark:
        clauses.append(f"Remark: {remark}")

    return _join_sentences(clauses) if clauses else "No further DCM details recorded."


def _nss_cell_text(
    nss: NSSData | None,
    previous_ventilation: int | None,
    previous_sepsis_rank: int | None,
) -> tuple[str, int | None, int | None]:
    """
    Synthesized Neonatal Sepsis Screening cell content for one day's
    table row, plus the running ventilation/sepsis state so the next
    day's row can show genuine progression.
    """

    if nss is None:
        return "No NSS record for this day.", previous_ventilation, previous_sepsis_rank

    clauses: list[str] = []

    vitals_bits = []

    if nss.temperature is not None:
        unit = _field(nss, "temperature_unit") or "°C"
        vitals_bits.append(f"Temp {_clean(nss.temperature)}{unit if unit.startswith('°') else ' ' + unit}")

    if nss.spo2 is not None:
        vitals_bits.append(f"SpO₂ {_clean(nss.spo2)}%")

    if nss.pulse_rate is not None:
        vitals_bits.append(f"HR {_clean(nss.pulse_rate)} bpm")

    if nss.respiratory_rate is not None:
        rr = _field(nss, "respiratory_rate")
        vitals_bits.append(f"RR {rr}/min" if rr else "RR not assessable (placeholder value in source form)")

    if vitals_bits:
        clauses.append(", ".join(vitals_bits))

    if nss.on_radiant_warmer:
        clauses.append("Radiant warmer")

    ventilation_level = _ventilation_level(nss)
    vent_clause = _ventilation_cell_clause(ventilation_level, previous_ventilation)

    if vent_clause:
        clauses.append(vent_clause)

    abnormal_bits = []

    for flag, label in [
        ("tachycardia", "tachycardia"),
        ("bradycardia", "bradycardia"),
        ("fast_breathing", "fast breathing"),
        ("bradypnea", "bradypnea"),
        ("high_temperature_flag", "high temperature"),
        ("low_temperature_flag", "low body temperature"),
        ("bleeding_observed", "bleeding"),
        ("fontanelle_bulging", "bulging fontanelle"),
    ]:
        if getattr(nss, flag, None):
            abnormal_bits.append(label)

    if abnormal_bits:
        clauses.append(", ".join(abnormal_bits))

    exam_bits = []

    for field_name, label in [
        ("general_condition", "general condition"),
        ("cry_type", "cry"),
        ("muscle_tone", "tone"),
        ("skin_colour", "skin"),
        ("gi_signs", "GI"),
        ("skin_umbilical_signs", "skin/umbilical"),
    ]:
        value = _field(nss, field_name)
        if value:
            exam_bits.append(f"{label} {value}")

    if exam_bits:
        clauses.append(", ".join(exam_bits))

    sepsis_text = _field(nss, "sepsis_impression")
    sepsis_clause = _sepsis_cell_clause(sepsis_text, previous_sepsis_rank)

    if sepsis_clause:
        clauses.append(sepsis_clause)

    new_sepsis_rank = _sepsis_rank(sepsis_text) if sepsis_text else previous_sepsis_rank

    lab_bits = []

    for field_name, label, unit in [
        ("tlc", "TLC", "/mm³"),
        ("hemoglobin", "Hb", "g/dL"),
        ("platelet_count", "platelet count", "/mm³"),
        ("anc", "ANC", "x10³/mm³"),
        ("total_bilirubin", "total bilirubin", "mg/dL"),
        ("crp", "CRP", "mg/L"),
        ("blood_glucose", "blood glucose", "mg/dL"),
    ]:
        value = _field(nss, field_name)
        if value:
            lab_bits.append(f"{label} {value} {unit}")

    if lab_bits:
        clauses.append("Labs: " + ", ".join(lab_bits))

    remark = _clean_remark(_field(nss, "remarks"))

    if remark:
        clauses.append(f"Remark: {remark}")

    new_ventilation = ventilation_level if ventilation_level is not None else previous_ventilation

    text = _join_sentences(clauses) if clauses else "No further NSS details recorded."

    return text, new_ventilation, new_sepsis_rank


def _set_cell_text(cell, text: str, *, bold: bool = False) -> None:

    cell.text = text

    for paragraph in cell.paragraphs:

        paragraph.paragraph_format.space_after = Pt(2)

        for run in paragraph.runs:
            run.bold = bold


def _section_daywise_course(document: DocxDocument, summary: CaseSummary) -> None:

    _section_heading(document, "2. Day-wise Clinical Course: DCM & Neonatal Sepsis Screening")

    days = _group_by_day(summary.dcm, summary.nss)

    if not days:
        _paragraph(
            document,
            "No Daily Clinical Monitoring or Neonatal Sepsis Screening records "
            "were available for this case.",
        )
        return

    table = document.add_table(rows=1, cols=3)
    table.style = "Light Grid Accent 1"
    table.autofit = True

    header_cells = table.rows[0].cells
    _set_cell_text(header_cells[0], "Date", bold=True)
    _set_cell_text(header_cells[1], "Daily Clinical Monitoring", bold=True)
    _set_cell_text(header_cells[2], "Neonatal Sepsis Screening", bold=True)

    previous_ventilation: int | None = None
    previous_sepsis_rank: int | None = None

    for day_number, display_date, dcm, nss in days:

        date_label = f"Day {day_number}"

        if display_date:
            date_label += f"\n({display_date})"

        dcm_text = _dcm_cell_text(dcm)
        nss_text, previous_ventilation, previous_sepsis_rank = _nss_cell_text(
            nss, previous_ventilation, previous_sepsis_rank
        )

        row_cells = table.add_row().cells
        _set_cell_text(row_cells[0], date_label)
        _set_cell_text(row_cells[1], dcm_text)
        _set_cell_text(row_cells[2], nss_text)


# --------------------------------------------------------------
# Section 3 — Key Laboratory Findings
# --------------------------------------------------------------

_LAB_PANELS: list[tuple[str, list[tuple[str, str, str]]]] = [
    (
        "CBC",
        [
            ("hemoglobin", "Hemoglobin", "g/dL"),
            ("tlc", "TLC", "/mm³"),
            ("platelet_count", "Platelet count", "/mm³"),
            ("anc", "ANC", "x10³/mm³"),
        ],
    ),
    (
        "LFT",
        [
            ("total_bilirubin", "Total bilirubin", "mg/dL"),
            ("direct_bilirubin", "Direct bilirubin", "mg/dL"),
            ("indirect_bilirubin", "Indirect bilirubin", "mg/dL"),
            ("total_protein", "Total protein", "g/dL"),
            ("albumin", "Albumin", "g/dL"),
            ("globulin", "Globulin", "g/dL"),
            ("alkaline_phosphatase", "Alkaline phosphatase", "IU/L"),
        ],
    ),
    (
        "Electrolytes / KFT",
        [
            ("sodium", "Sodium", "meq/L"),
            ("potassium", "Potassium", "meq/L"),
            ("ionic_calcium", "Ionic calcium", "mg/dL"),
            ("urea", "Urea", "mg/dL"),
            ("creatinine", "Creatinine", "mg/dL"),
        ],
    ),
    (
        "Inflammatory markers",
        [("crp", "CRP", "mg/L")],
    ),
]


def _lab_panel_sentence(panel_name: str, fields: list[tuple[str, str, str]], record: LabData) -> str | None:

    bits = []

    for field_name, label, unit in fields:
        value = _field(record, field_name)
        if value:
            bits.append(f"{label} {value} {unit}")

    return f"{panel_name} — " + ", ".join(bits) if bits else None


def _section_lab_findings(document: DocxDocument, summary: CaseSummary) -> None:

    _section_heading(document, "3. Key Laboratory Findings")

    rendered = False

    # A safe, evidence-based cross-reference (correlating two already
    # -extracted facts) rather than an invented clinical threshold.
    phototherapy_noted = any(
        "photo" in (_field(dcm, "remarks") or "").lower() for dcm in summary.dcm
    )

    for lab in summary.lab:

        panel_sentences = [
            sentence
            for panel_name, fields in _LAB_PANELS
            if (sentence := _lab_panel_sentence(panel_name, fields, lab))
        ]

        if not panel_sentences:
            continue

        header_bits = []

        if _field(lab, "test_date"):
            header_bits.append(_field(lab, "test_date"))

        if _field(lab, "lab_accession_no"):
            header_bits.append(f"Reg/Ref {_field(lab, 'lab_accession_no')}")

        intro = "Laboratory investigations"

        if header_bits:
            intro += f" dated {', '.join(header_bits)}"

        text = intro + " showed: " + "; ".join(panel_sentences) + "."

        if phototherapy_noted and _field(lab, "total_bilirubin"):
            text += " Phototherapy was noted in the clinical record around this time."

        _paragraph(document, text)

        rendered = True

    # Serial/trend view from the day-wise NSS-inline lab values, when present.
    trend_bits = []

    for nss in summary.nss:

        day_bits = []

        for field_name, label, unit in [
            ("tlc", "TLC", "/mm³"),
            ("hemoglobin", "Hb", "g/dL"),
            ("platelet_count", "platelets", "/mm³"),
            ("anc", "ANC", "x10³/mm³"),
            ("total_bilirubin", "total bilirubin", "mg/dL"),
            ("crp", "CRP", "mg/L"),
        ]:
            value = _field(nss, field_name)
            if value:
                day_bits.append(f"{label} {value} {unit}")

        if day_bits and _field(nss, "assessment_date"):
            trend_bits.append(f"{_field(nss, 'assessment_date')}: {', '.join(day_bits)}")

    if trend_bits:
        _paragraph(
            document,
            "Serial monitoring during the admission showed the following trend: "
            + "; ".join(trend_bits) + ".",
        )
        rendered = True

    if not rendered:
        _paragraph(document, "No laboratory investigation results were available for this case.")


# --------------------------------------------------------------
# Section 4 — In-hospital Death & Outcome
# --------------------------------------------------------------


def _last_known_status(nss_records: list[NSSData]) -> str | None:

    dated = [(record, _parse_date(record.assessment_date)) for record in nss_records]
    dated_only = [(record, d) for record, d in dated if d is not None]

    if dated_only:
        dated_only.sort(key=lambda pair: pair[1])
        candidate = dated_only[-1][0]
    elif nss_records:
        candidate = nss_records[-1]
    else:
        return None

    bits = []

    if _field(candidate, "general_condition"):
        bits.append(f"general condition {_field(candidate, 'general_condition')}")

    if _field(candidate, "sepsis_impression"):
        bits.append(f"sepsis impression {_field(candidate, 'sepsis_impression')}")

    if not bits:
        return None

    date_bit = f" as of {candidate.assessment_date}" if candidate.assessment_date else ""

    return f"At the most recent documented assessment{date_bit}, the infant's {', '.join(bits)} was noted."


def _section_outcome(document: DocxDocument, summary: CaseSummary, clinical_report) -> None:

    _section_heading(document, "4. In-hospital Death & Outcome")

    sentences: list[str] = []

    narrative = _clean(getattr(clinical_report, "final_outcome", None)) if clinical_report else None

    if narrative:
        sentences.append(narrative)

    sae = summary.sae

    if sae:

        onset_bits = []

        if _field(sae, "event_date"):
            onset_bits.append(f"with an onset date of {_field(sae, 'event_date')}")

        diagnosis = _clean_remark(_field(sae, "diagnosis"))

        if diagnosis:
            onset_bits.append(f"diagnosed as {diagnosis}")

        if onset_bits:
            sentences.append("A Serious Adverse Event was recorded " + " and ".join(onset_bits) + ".")

        event_description = _clean_remark(_field(sae, "event_description"))

        if event_description:
            sentences.append(event_description)

        if _field(sae, "seriousness"):
            sentences.append(f"The event was classified as {_field(sae, 'seriousness')}.")

        outcome_bits = []

        cause_of_death = _clean_remark(_field(sae, "cause_of_death"))

        if cause_of_death:
            outcome_bits.append(f"the cause of death was documented as {cause_of_death}")

        if _field(sae, "outcome"):
            outcome_bits.append(f"the documented outcome was {_field(sae, 'outcome')}")

        if outcome_bits:
            combined = " and ".join(outcome_bits)
            sentences.append(combined[0].upper() + combined[1:] + ".")

        admin_bits = []

        if _field(sae, "admission_date"):
            admin_bits.append(f"admitted on {_field(sae, 'admission_date')}")

        if _field(sae, "discharge_date"):
            admin_bits.append(f"discharged on {_field(sae, 'discharge_date')}")

        if admin_bits:
            sentences.append("The infant was " + " and ".join(admin_bits) + ".")

        notif_bits = []

        if _field(sae, "reporter_name"):
            notif_bits.append(f"by {_field(sae, 'reporter_name')}")

        if _field(sae, "reporting_date"):
            notif_bits.append(f"on {_field(sae, 'reporting_date')}")

        if notif_bits:
            sentences.append("This SAE was notified " + " ".join(notif_bits) + ".")

    else:
        sentences.append(
            "No dedicated Serious Adverse Event (SAE) form was identified for this "
            "case in the source document."
        )

    # Only fall back to the last routine monitoring status if the
    # case doesn't already have a clearer outcome statement above —
    # otherwise a pre-event NSS assessment reads as a confusing
    # non-sequitur after an outcome (e.g. death) has just been stated.
    if not narrative and not (sae and _field(sae, "outcome")):
        last_status = _last_known_status(summary.nss)
        if last_status:
            sentences.append(last_status)

    _paragraph(document, _join_sentences(sentences))


def _confidentiality_footer(document: DocxDocument) -> None:

    _paragraph(document, "Confidential — ICMR Emollient Study", italic=True)


# --------------------------------------------------------------
# Builder
# --------------------------------------------------------------


class DocumentBuilder:

    def build(
        self,
        summary: CaseSummary,
        output_file: str | Path,
        clinical_report: "ClinicalReport | None" = None,
    ) -> None:

        document = create_document()

        _title_block(document, summary)
        _identification_block(document, summary)

        _section_maternal_history(document, summary, clinical_report)
        _section_daywise_course(document, summary)
        _section_lab_findings(document, summary)
        _section_outcome(document, summary, clinical_report)

        _confidentiality_footer(document)

        document.save(str(output_file))
