# TODO: Add tests for LLM integration and prompt handling.
from llm.json_cleaner import SAEJsonCleaner

ocr = """
Hospital Name
GSVM Medical College

19-Please describe the outcome of the event

Condition Improved

26-How severe was the SAE

Life-threatening
"""

raw = {
    "hospital_name":"GSVM Medical College",
    "outcome":".yy",
    "seriousness":"[AE"
}

clean = SAEJsonCleaner.improve(
    ocr,
    raw,
)

print(clean)