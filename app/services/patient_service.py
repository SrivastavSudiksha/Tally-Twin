"""CRUD helpers for Patient model."""

from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.patient import Patient

from app.schemas.patient import PatientInput

from app.utils.clearance import derive_patient_pk_params

def create_patient(db: Session, data: PatientInput, external_id: Optional[str] = None) -> Patient:

    derived = derive_patient_pk_params(

        age=data.age,

        sex=data.sex.value,

        weight_kg=data.weight_kg,

        height_cm=data.height_cm,

        serum_creatinine=data.serum_creatinine,

        egfr_provided=data.egfr,

        alt=data.alt,

        ast=data.ast,

        bilirubin=data.bilirubin,

        albumin=data.albumin,

        smoking=data.smoking,

        alcohol=data.alcohol,

        conditions=data.conditions,

    )

    patient = Patient(

        external_id=external_id,

        age=data.age,

        sex=data.sex.value,

        weight_kg=data.weight_kg,

        height_cm=data.height_cm,

        serum_creatinine=data.serum_creatinine,

        egfr=derived["egfr"],

        alt=data.alt,

        ast=data.ast,

        bilirubin=data.bilirubin,

        albumin=data.albumin,

        conditions=data.conditions or [],

        allergies=data.allergies or [],

        current_medicines=[m.model_dump() for m in data.current_medicines],

        smoking=data.smoking,

        alcohol=data.alcohol,

        cyp2d6=data.cyp2d6,

        cyp2c19=data.cyp2c19,

        cyp2c9=data.cyp2c9,

        qtc_ms=data.qtc_ms,

        bmi=derived["bmi"],

        clearance_adjustment_factor=derived["clearance_adjustment_factor"],

    )

    db.add(patient)

    db.commit()

    db.refresh(patient)

    return patient

def get_patient(db: Session, patient_id: int) -> Optional[Patient]:

    return db.query(Patient).filter(Patient.id == patient_id).first()

def list_patients(db: Session, skip: int = 0, limit: int = 50) -> List[Patient]:

    return (

        db.query(Patient)

        .order_by(Patient.created_at.desc())

        .offset(skip)

        .limit(limit)

        .all()

    )

def delete_patient(db: Session, patient_id: int) -> bool:

    patient = get_patient(db, patient_id)

    if not patient:

        return False

    db.delete(patient)

    db.commit()

    return True

