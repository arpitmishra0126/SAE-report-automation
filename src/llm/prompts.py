"""
LLM prompts for medical document extraction.
"""

from __future__ import annotations


SYSTEM_PROMPT = """
You are an expert neonatal clinical documentation assistant.

You are helping extract structured information from REDCap-generated
Serious Adverse Event (SAE) forms.

The OCR text may contain:

- spelling mistakes
- broken words
- missing spaces
- duplicated lines
- OCR artifacts
- Hindi + English mixed text

Your task is ONLY to improve the extracted JSON.

Rules:

1. NEVER invent information.
2. NEVER guess.
3. If information is missing, return null.
4. Preserve dates exactly.
5. Remove OCR artifacts.
6. Return ONLY valid JSON.
7. Do not explain anything.
"""


def build_sae_prompt(
    ocr_text: str,
    extracted_json: dict,
) -> str:
    """
    Build prompt for SAE cleanup.
    """

    import json

    return f"""
Below is OCR text extracted from a REDCap Serious Adverse Event form.

==============================
OCR TEXT
==============================

{ocr_text}

==============================
CURRENT EXTRACTED JSON
==============================

{json.dumps(extracted_json, indent=2)}

==============================
TASK
==============================

Improve ONLY these fields if better information exists:

- participant_id
- event_date
- diagnosis
- event_description
- seriousness
- outcome
- cause_of_death
- hospital_name
- admission_date
- reporting_date

Remove OCR artifacts such as:

qR
Rf
.yy
[AE
Hag4?
Updatereset
must provide value

Do NOT modify fields that are already correct.

Return ONLY valid JSON.

No markdown.

No explanation.
"""