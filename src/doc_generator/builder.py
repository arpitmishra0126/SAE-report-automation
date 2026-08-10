"""
SAE Case Summary document builder.

Renders the pipeline's structured `CaseSummary` and AI-generated
`ClinicalReport` as a "Clinical Case Narrative" — prose paragraphs
organized chronologically under fixed headings, not field/value
tables.

Narrative text is synthesized here, in plain Python, directly from
already-extracted structured data (`CaseSummary`) and the LLM's own
already-generated narrative fields (`ClinicalReport.maternal_history`,
`.final_outcome`, `.executive_summary`). No LLM call is made from
this module and no extraction/reasoning logic is touched — this is
presentation only. A clause is written only when the underlying
field is actually present; nothing here invents a clinical fact, a
date, a diagnosis, or an outcome, and a document with fewer records
(or none at all) produces a correspondingly shorter narrative rather
than a differently-shaped one.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from models.case_summary import CaseSummary
from models.dcm import DCMData
from models.lab import LabData
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
# Document primitives
# --------------------------------------------------------------


def _paragraph(document: DocxDocument, text: str, *, italic: bool = False):

    paragraph = document.add_paragraph(text)
    paragraph.paragraph_format.space_after = Pt(10)

    if italic and paragraph.runs:
        paragraph.runs[0].italic = True

    return paragraph


def _section_heading(document: DocxDocument, text: str, *, page_break: bool = False) -> None:

    if page_break:
        document.add_page_break()

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
    subtitle.paragraph_format.space_after = Pt(16)

    if subtitle.runs:
        subtitle.runs[0].bold = True
        subtitle.runs[0].font.size = Pt(13)


def _identification_line(document: DocxDocument, summary: CaseSummary) -> None:

    sae = summary.sae
    maternal = summary.maternal

    parts: list[str] = []

    baby_ref = _field(sae, "patient_name")

    if not baby_ref and maternal and _field(maternal, "mother_name"):
        baby_ref = f"Baby of {_field(maternal, 'mother_name')}"

    if baby_ref:
        parts.append(baby_ref)

    if sae and _field(sae, "sex"):
        parts.append(_field(sae, "sex"))

    if sae and sae.age_days is not None:
        parts.append(f"aged {sae.age_days} days")

    if maternal and _field(maternal, "gestational_age"):
        parts.append(f"born at {_field(maternal, 'gestational_age')} gestation")

    if maternal and _field(maternal, "baby_uid"):
        parts.append(f"UID {_field(maternal, 'baby_uid')}")

    if sae and _field(sae, "date_of_birth"):
        parts.append(f"DOB {_field(sae, 'date_of_birth')}")

    hospital = _field(sae, "hospital_name") or _field(maternal, "hospital_name")

    if hospital:
        parts.append(f"admitted at {hospital}")

    if parts:
        _paragraph(document, ", ".join(parts) + ".", italic=True)


def _lead_summary(document: DocxDocument, clinical_report) -> None:
    """
    An unheaded lead paragraph giving overall case context, using the
    LLM's own already-generated executive summary when available.
    """

    text = _clean(getattr(clinical_report, "executive_summary", None)) if clinical_report else None

    if text:
        _paragraph(document, text)


# --------------------------------------------------------------
# Section 1 — Maternal History
# --------------------------------------------------------------


def _maternal_fallback_narrative(maternal) -> str | None:
    """
    Deterministic narrative used only if the AI-generated maternal
    history narrative is unavailable. Only present fields are used.
    """

    sentences: list[str] = []

    intro_bits = []

    if _field(maternal, "mother_name"):
        intro_bits.append(f"mother {_field(maternal, 'mother_name')}")

    if maternal.mother_age is not None:
        intro_bits.append(f"aged {maternal.mother_age} years")

    if _field(maternal, "father_name"):
        intro_bits.append(f"father {_field(maternal, 'father_name')}")

    if intro_bits:
        sentence = "This case involves the " + ", ".join(intro_bits)
        if _field(maternal, "hospital_name"):
            sentence += f", delivered at {_field(maternal, 'hospital_name')}"
        sentences.append(sentence + ".")

    delivery_bits = []

    for label, field_name in [
        ("delivery type", "delivery_type"),
        ("labour type", "labour_type"),
        ("presentation", "presentation"),
        ("course of labour", "labour_course"),
    ]:
        value = _field(maternal, field_name)
        if value:
            delivery_bits.append(f"{label} {value}")

    if delivery_bits:
        sentences.append("Delivery details: " + ", ".join(delivery_bits) + ".")

    if maternal.corticosteroids_given:
        steroid_bits = ["Antenatal corticosteroids were administered"]
        if _field(maternal, "steroid_type"):
            steroid_bits.append(f"({_field(maternal, 'steroid_type')}")
            if maternal.steroid_doses is not None:
                steroid_bits[-1] += f", {maternal.steroid_doses} doses)"
            else:
                steroid_bits[-1] += ")"
        sentences.append(" ".join(steroid_bits) + ".")

    risk_bits = []

    if maternal.foul_smelling_discharge:
        risk_bits.append("foul-smelling vaginal discharge")

    if maternal.pprom_over_24h:
        risk_bits.append("prolonged rupture of membranes (>24 hours)")

    if maternal.foetal_distress:
        risk_bits.append("foetal distress")

    if risk_bits:
        sentences.append(
            "Antenatal/intrapartum risk factors included " + ", ".join(risk_bits) + "."
        )

    if _field(maternal, "amniotic_fluid_appearance"):
        sentences.append(
            f"Amniotic fluid appearance was documented as "
            f"{_field(maternal, 'amniotic_fluid_appearance')}."
        )

    if _field(maternal, "maternal_remarks"):
        sentences.append(_field(maternal, "maternal_remarks"))

    return " ".join(sentences) if sentences else None


def _section_maternal_history(document: DocxDocument, summary: CaseSummary, clinical_report) -> None:

    _section_heading(document, "1. Maternal History")

    narrative = _clean(getattr(clinical_report, "maternal_history", None)) if clinical_report else None

    if not narrative and summary.maternal:
        narrative = _maternal_fallback_narrative(summary.maternal)

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
    grouping key so they are never silently dropped.
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


def _day_sentences(dcm: DCMData | None, nss: NSSData | None) -> list[str]:

    sentences: list[str] = []

    # Overall status
    status_bits = []

    if _field(dcm, "vital_status"):
        status_bits.append(f"vital status recorded as {_field(dcm, 'vital_status')}")

    if dcm and dcm.weight is not None:
        status_bits.append(f"weight {_clean(dcm.weight)} g")

    if status_bits:
        sentences.append("The newborn's " + " and ".join(status_bits) + ".")

    # Support / interventions
    support_bits = []

    if dcm and dcm.on_incubator_support:
        support_bits.append("was on incubator support")

    if nss and nss.on_invasive_ventilator:
        support_bits.append("was on invasive mechanical ventilation")
    elif nss and nss.on_noninvasive_ventilator:
        support_bits.append("was on non-invasive ventilatory support")

    if dcm and dcm.kmc_provided:
        support_bits.append("received Kangaroo Mother Care")

    if support_bits:
        sentences.append("The infant " + ", ".join(support_bits) + ".")

    # Medications
    if _field(dcm, "medications"):
        sentences.append(f"Medications administered included {_field(dcm, 'medications')}.")

    # Feeding
    feeding_bits = []

    if _field(dcm, "feed_types"):
        feeding_bits.append(f"feed type {_field(dcm, 'feed_types')}")

    if _field(dcm, "feed_route"):
        feeding_bits.append(f"route {_field(dcm, 'feed_route')}")

    if dcm and dcm.enteral_feed_ml is not None:
        feeding_bits.append(f"enteral feeds {_clean(dcm.enteral_feed_ml)} ml")

    if dcm and dcm.total_fluid_intake_ml is not None:
        feeding_bits.append(f"total fluid intake {_clean(dcm.total_fluid_intake_ml)} ml")

    if feeding_bits:
        sentences.append("Feeding: " + ", ".join(feeding_bits) + ".")

    # Vitals
    vitals_bits = []

    if nss and nss.temperature is not None:
        unit = _field(nss, "temperature_unit") or "°C"
        vitals_bits.append(f"temperature {_clean(nss.temperature)} {unit}")

    if nss and nss.spo2 is not None:
        vitals_bits.append(f"SpO₂ {_clean(nss.spo2)}%")

    if nss and nss.pulse_rate is not None:
        vitals_bits.append(f"pulse rate {_clean(nss.pulse_rate)}/min")

    if nss and nss.respiratory_rate is not None:
        rr = _field(nss, "respiratory_rate")
        if rr:
            vitals_bits.append(f"respiratory rate {rr}/min")
        else:
            vitals_bits.append(
                "respiratory rate not assessable (source form recorded a "
                "non-measurable placeholder value)"
            )

    if vitals_bits:
        sentences.append("Vital signs: " + ", ".join(vitals_bits) + ".")

    # Abnormal flags — mentioned only when actually present
    abnormal_bits = []

    if nss:
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
        sentences.append("Abnormal findings noted: " + ", ".join(abnormal_bits) + ".")

    # Clinical exam
    exam_bits = []

    for field_name, label in [
        ("general_condition", "general condition"),
        ("cry_type", "cry"),
        ("muscle_tone", "muscle tone"),
        ("skin_colour", "skin colour"),
    ]:
        value = _field(nss, field_name)
        if value:
            exam_bits.append(f"{label} {value}")

    if exam_bits:
        sentences.append("On examination, " + ", ".join(exam_bits) + ".")

    # Sepsis impression
    if _field(nss, "sepsis_impression"):
        sentences.append(f"Clinician's sepsis impression: {_field(nss, 'sepsis_impression')}.")

    # Inline laboratory parameters
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
        sentences.append("Laboratory parameters: " + ", ".join(lab_bits) + ".")

    # Remarks — preserved verbatim, from both DCM and NSS if distinct
    remark_bits = []

    dcm_remarks = _field(dcm, "remarks")
    nss_remarks = _field(nss, "remarks")

    if dcm_remarks:
        remark_bits.append(dcm_remarks)

    if nss_remarks and nss_remarks != dcm_remarks:
        remark_bits.append(nss_remarks)

    if remark_bits:
        sentences.append("Remarks: " + " ".join(remark_bits))

    return sentences


def _section_daywise_course(document: DocxDocument, summary: CaseSummary) -> None:

    _section_heading(
        document,
        "2. Day-wise Clinical Course: DCM & Neonatal Sepsis Screening",
        page_break=True,
    )

    days = _group_by_day(summary.dcm, summary.nss)

    if not days:
        _paragraph(
            document,
            "No Daily Clinical Monitoring or Neonatal Sepsis Screening records "
            "were available for this case.",
        )
        return

    for day_number, display_date, dcm, nss in days:

        label = f"Day {day_number}"

        if display_date:
            label += f" ({display_date})"

        document.add_heading(label, level=2)

        sentences = _day_sentences(dcm, nss)

        _paragraph(
            document,
            " ".join(sentences) if sentences else "No further clinical details were recorded for this day.",
        )


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

    _section_heading(document, "3. Key Laboratory Findings", page_break=True)

    rendered = False

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

        _paragraph(document, intro + " showed: " + "; ".join(panel_sentences) + ".")

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

    _section_heading(document, "4. In-hospital Death & Outcome", page_break=True)

    sentences: list[str] = []

    narrative = _clean(getattr(clinical_report, "final_outcome", None)) if clinical_report else None

    if narrative:
        sentences.append(narrative)

    sae = summary.sae

    if sae:

        if _field(sae, "event_date"):
            sentences.append(
                f"The Serious Adverse Event was recorded with an onset date of "
                f"{_field(sae, 'event_date')}."
            )

        if _field(sae, "diagnosis"):
            sentences.append(f"Diagnosis: {_field(sae, 'diagnosis')}.")

        if _field(sae, "event_description"):
            sentences.append(_field(sae, "event_description"))

        if _field(sae, "seriousness"):
            sentences.append(f"The event was classified as: {_field(sae, 'seriousness')}.")

        if _field(sae, "cause_of_death"):
            sentences.append(f"Cause of death: {_field(sae, 'cause_of_death')}.")

        if _field(sae, "outcome"):
            sentences.append(f"Documented outcome: {_field(sae, 'outcome')}.")

        if _field(sae, "admission_date"):
            sentences.append(f"Hospital admission date: {_field(sae, 'admission_date')}.")

        if _field(sae, "discharge_date"):
            sentences.append(f"Discharge date: {_field(sae, 'discharge_date')}.")

        notif_bits = []

        if _field(sae, "reporter_name"):
            notif_bits.append(f"reported by {_field(sae, 'reporter_name')}")

        if _field(sae, "reporting_date"):
            notif_bits.append(f"on {_field(sae, 'reporting_date')}")

        if notif_bits:
            sentences.append("This SAE was " + " ".join(notif_bits) + ".")

    else:
        sentences.append(
            "No dedicated Serious Adverse Event (SAE) form was identified for this "
            "case in the source document."
        )

    if not (sae and _field(sae, "outcome")):
        last_status = _last_known_status(summary.nss)
        if last_status:
            sentences.append(last_status)

    _paragraph(document, " ".join(sentences))


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
        _identification_line(document, summary)
        _lead_summary(document, clinical_report)

        _section_maternal_history(document, summary, clinical_report)
        _section_daywise_course(document, summary)
        _section_lab_findings(document, summary)
        _section_outcome(document, summary, clinical_report)

        document.save(str(output_file))
