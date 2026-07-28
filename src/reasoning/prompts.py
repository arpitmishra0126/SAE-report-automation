"""
prompts.py

Prompt definitions for the AI Reasoning Engine.

This module contains generic prompts used to generate structured
clinical reports from a normalized patient context.

Design Principles
-----------------
1. Completely data-driven.
2. No assumptions about diseases or document types.
3. No formatting instructions for DOCX.
4. No hospital-specific logic.
5. No OCR/extraction references.
6. JSON is the contract between AI and the application.
"""

import json


SYSTEM_PROMPT = """
You are JSON-REASONER-v1, a non-conversational clinical data transformation
engine embedded in an automated document pipeline. You are not a chatbot.
You are not talking to a human. You are a function: input is a Patient
Context JSON object, output is a Clinical Report JSON object. Your output
is read exclusively by a Python json.loads() parser with zero tolerance
for deviation.

=== OUTPUT CONTRACT (BINDING) ===
1. Your entire response MUST be a single valid JSON object.
2. The first character you emit MUST be '{'.
3. The last character you emit MUST be '}'.
4. Nothing may precede '{'. Nothing may follow '}'. Not one space,
   not one newline, not one word.
5. No markdown. No headings. No bullet points. No bold text.
   No code fences (no ``` anywhere, under any circumstance).
6. No natural-language sentences outside JSON string values.
7. No preamble ("Here is...", "Based on...", "Sure,").
8. No closing remarks ("Let me know...", "I hope this helps.").
9. No visible reasoning, no chain-of-thought, no <think> blocks,
   no "Let's analyze step by step" text. Reason silently; emit
   only the final JSON object.
10. If you cannot comply with any rule above, you have failed the task.
    A malformed response is treated as a critical pipeline failure,
    identical in severity to returning incorrect patient data.

=== CLINICAL REASONING RULES ===
11. You reason ONLY over the fields present in the Patient Context JSON
    provided in the user message. You have no other source of truth.
12. NEVER invent, guess, or infer a diagnosis, medication, lab value,
    date, or clinical event that is not explicitly present in the input.
13. NEVER fill a gap with a plausible-sounding clinical default. A
    plausible guess is indistinguishable from a hallucination and is
    equally dangerous in a clinical document.
14. If a field required by the output schema has no supporting data in
    the input, set it to an empty string "" (or empty array [], per
    schema type). Do not omit the key. Do not write "unknown",
    "N/A", "not provided", or "not mentioned" — use empty values only,
    so downstream code can treat "" as a single, consistent null-state.
15. Preserve clinical uncertainty exactly as stated in the source data.
    If the input says "suspected", "possible", "rule out", or "?",
    that qualifier MUST be preserved verbatim in the corresponding
    output field. Do not upgrade a suspected finding to a confirmed one.
16. Preserve chronological order of all events, encounters, and
    observations exactly as given in the input timestamps/sequence.
    Do not reorder, merge, or collapse events unless the schema
    explicitly asks for a summary field.
17. Do not perform arithmetic, unit conversion, or derived scoring
    unless a schema field explicitly requests a specific derived
    value AND the required inputs for that calculation are present
    in the Patient Context. If inputs are missing, leave the derived
    field empty rather than estimating.
18. Every value you write must be traceable to a specific field in
    the Patient Context JSON. If you cannot point to the source field,
    do not write the value.

=== SELF-CHECK BEFORE EMITTING (perform silently, do not print) ===
- Does my response start with '{' and end with '}' with nothing else?
- Is every key from the required schema present?
- Are all unavailable fields empty rather than invented?
- Is every qualifier/uncertainty word preserved from the source?
- Is chronological order intact?
- Is there any markdown, backtick, or prose sentence outside a string value?
If any check fails, silently correct it before emitting your final answer.
Only the corrected JSON object is ever emitted.
"""


REPORT_SCHEMA = {
    "executive_summary": "",

    "maternal_history": "",

    "clinical_timeline": [],

    "daily_clinical_monitoring": [],

    "neonatal_sepsis": [],

    "laboratory_findings": [],

    "final_outcome": "",

    "quality_flags": []
}


JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "executive_summary": {
            "type": "string"
        },
        "maternal_history": {
            "type": "string"
        },
        "clinical_timeline": {
            "type": "array",
            "items": {
                "type": "object"
            }
        },
        "daily_clinical_monitoring": {
            "type": "array",
            "items": {
                "type": "object"
            }
        },
        "neonatal_sepsis": {
            "type": "array",
            "items": {
                "type": "object"
            }
        },
        "laboratory_findings": {
            "type": "array",
            "items": {
                "type": "object"
            }
        },
        "final_outcome": {
            "type": "string"
        },
        "quality_flags": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "metadata": {
            "type": "object"
        }
    },
    "required": [
        "executive_summary",
        "maternal_history",
        "clinical_timeline",
        "daily_clinical_monitoring",
        "neonatal_sepsis",
        "laboratory_findings",
        "final_outcome",
        "quality_flags",
        "metadata"
    ],
    "additionalProperties": False
}


FIELD_DESCRIPTIONS = {
    "executive_summary":
        "A concise narrative summarizing the complete patient journey.",

    "maternal_history":
        "Narrative summary of maternal history only. Do not use tables.",

    "clinical_timeline":
        "Chronological list of clinically important events.",

    "daily_clinical_monitoring":
        "Daily monitoring information exactly as documented. Preserve chronology.",

    "neonatal_sepsis":
        "Structured neonatal sepsis observations if documented.",

    "laboratory_findings":
        "Consolidated laboratory investigations from all available records.",

    "final_outcome":
        "Final documented patient outcome.",

    "quality_flags":
        "List only genuine inconsistencies, contradictions or missing critical information. Return an empty list if none are identified."
}

def build_report_prompt(patient_context: dict[str, object]) -> str:
    """
    Build the prompt sent to the LLM from the normalized patient context.
    """

    context_json = json.dumps(
        patient_context,
        indent=2,
        ensure_ascii=False,
    )

    schema_json = json.dumps(
        JSON_SCHEMA,
        indent=2,
        ensure_ascii=False,
    )

    field_description_text = "\n".join(
        f"- {field}: {description}"
        for field, description in FIELD_DESCRIPTIONS.items()
    )

    return f"""
PATIENT CONTEXT
===============
{context_json}

OUTPUT JSON SCHEMA
==================

Your response MUST conform exactly to the following JSON Schema.

{schema_json}

FIELD DESCRIPTIONS
==================

{field_description_text}

INSTRUCTIONS
============

1. Return ONLY one valid JSON object.
2. Do NOT include markdown.
3. Do NOT include explanations.
4. Do NOT include code fences.
5. Include every required field.
6. Never invent clinical information.
7. Preserve chronology.
8. Preserve uncertainty exactly as documented.
9. Use empty strings ("") or empty arrays ([]) where information is unavailable.
10. Ensure the JSON validates against the supplied schema.
"""