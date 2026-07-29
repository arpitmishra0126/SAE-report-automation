"""
Maternal History data model.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MaternalData(BaseModel):
    """
    Structured maternal history information.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    mother_name: str | None = Field(default=None)

    father_name: str | None = Field(default=None)

    mother_age: int | None = Field(default=None)

    hospital_name: str | None = Field(default=None)

    hospital_reg_no: str | None = Field(default=None)

    baby_uid: str | None = Field(default=None)

    gestational_age: str | None = Field(default=None)

    delivery_type: str | None = Field(default=None)

    labour_type: str | None = Field(default=None)

    maternal_remarks: str | None = Field(default=None)

    # ------------------------
    # Obstetric history
    # ------------------------

    gravida: int | None = Field(default=None)

    para: int | None = Field(default=None)

    # ------------------------
    # Antenatal corticosteroids
    # ------------------------

    corticosteroids_given: bool | None = Field(default=None)

    steroid_type: str | None = Field(
        default=None,
        description="e.g. Betamethasone, Dexamethasone.",
    )

    steroid_doses: int | None = Field(default=None)

    # ------------------------
    # Labour history
    # ------------------------

    fever_history: str | None = Field(
        default=None,
        description="e.g. No fever at all / In 1st trimester / During labour only if >=100.4F.",
    )

    foul_smelling_discharge: bool | None = Field(default=None)

    uterine_tenderness: bool | None = Field(default=None)

    pprom_over_24h: bool | None = Field(
        default=None,
        description="Leaking per vaginum > 24 hours before delivery.",
    )

    amniotic_fluid_appearance: str | None = Field(
        default=None,
        description="e.g. Clear / Blood Stained / Meconium Stained / Foul Smelling.",
    )

    presentation: str | None = Field(
        default=None,
        description="e.g. Vertex / Breech / Transverse.",
    )

    labour_course: str | None = Field(
        default=None,
        description="e.g. Uneventful / Prolonged 1st stage / Prolonged 2nd stage / Obstructed.",
    )

    foetal_distress: bool | None = Field(default=None)

    delivery_mode: str | None = Field(
        default=None,
        description="e.g. NVD / LSCS / AVD.",
    )

    delivery_attendant: str | None = Field(
        default=None,
        description="e.g. Doctor / Nurse / ANM / Dai.",
    )

    significant_maternal_info_flag: bool | None = Field(default=None)

    # ------------------------
    # Antenatal screening panel
    # ------------------------

    blood_group: str | None = Field(default=None)

    vdrl: str | None = Field(default=None, description="Not Done / +Ve / -Ve.")

    hbsag: str | None = Field(default=None, description="Not Done / +Ve / -Ve.")

    hiv_status: str | None = Field(default=None, description="Done / Not Done, and result if known.")

    pih: bool | None = Field(default=None, description="Pregnancy-induced hypertension.")

    gdm: bool | None = Field(default=None, description="Gestational diabetes mellitus.")

    thyroid_status: str | None = Field(
        default=None,
        description="e.g. Euthyroid / Hypothyroid / Hyperthyroid / Not Known.",
    )

    oligohydramnios: bool | None = Field(default=None)

    amniotic_fluid_volume: str | None = Field(
        default=None,
        description="e.g. Adequate / Polyhydramnios / Oligohydramnios.",
    )

    illness_history: str | None = Field(
        default=None,
        description="e.g. UTI/Bacteraemia, Malaria, TB, Jaundice, or None.",
    )

    epilepsy_radiation_drug_history: str | None = Field(default=None)

    aph: bool | None = Field(default=None, description="Antepartum haemorrhage.")
