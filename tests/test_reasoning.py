"""
test_reasoning.py

End-to-end test for the AI reasoning pipeline.
"""

from pprint import pprint

from src.reasoning.patient_record import PatientRecord
from src.reasoning.context_builder import ContextBuilder
from src.reasoning.llm_reasoner import LLMReasoner


def main():

    # ---------------------------------------------------------
    # Build Patient Record
    # ---------------------------------------------------------

    record = PatientRecord()

    record.set_patient(
        {
            "baby_name": "Baby A",
            "sex": "Male",
            "birth_weight": "2.4 kg",
            "gestational_age": "36 weeks",
        }
    )

    record.set_maternal(
        {
            "mother_age": 24,
            "gravida": "G2",
            "parity": "P1",
            "delivery_mode": "Normal Vaginal Delivery",
        }
    )

    record.set_sae(
        {
            "admission_date": "2025-01-10",
            "event": "Respiratory distress",
            "outcome": "Death",
        }
    )

    record.add_dcm(
        {
            "day": 1,
            "respiratory_rate": 72,
            "spo2": 88,
            "oxygen_support": "CPAP",
        }
    )

    record.add_dcm(
        {
            "day": 2,
            "respiratory_rate": 68,
            "spo2": 90,
            "oxygen_support": "CPAP",
        }
    )

    record.add_nss(
        {
            "day": 2,
            "blood_culture": "Pending",
        }
    )

    record.add_lab(
        {
            "test": "CRP",
            "result": "Positive",
        }
    )

    record.set_metadata(
        {
            "record_id": "TEST001",
        }
    )

    # ---------------------------------------------------------
    # Build Context
    # ---------------------------------------------------------

    builder = ContextBuilder()

    context = builder.build(record)

    print("\n" + "=" * 80)
    print("REASONING CONTEXT")
    print("=" * 80)

    pprint(context)

    # ---------------------------------------------------------
    # Run LLM
    # ---------------------------------------------------------

    reasoner = LLMReasoner()

    report = reasoner.generate_report(context)

    print("\n" + "=" * 80)
    print("GENERATED CLINICAL REPORT")
    print("=" * 80)

    pprint(report.to_dict())


if __name__ == "__main__":
    main()