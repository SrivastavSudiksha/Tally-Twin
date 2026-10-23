"""Persist simulation results to the database."""

from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.simulation import Simulation

from app.models.patient import Patient

from app.schemas.report import SimulationReport

from app.schemas.patient import PatientInput

from app.schemas.drug import DrugInput

from app.services.simulation_service import run_full_simulation

from app.services.patient_service import create_patient

def save_simulation(

    db: Session,

    report: SimulationReport,

    drug: DrugInput,

    patient_id: Optional[int] = None,

) -> Simulation:

    """Store a completed simulation report."""

    sim = Simulation(

        patient_id=patient_id,

        drug_identifier=drug.identifier,

        dose_mg=drug.dose_mg,

        route=drug.route,

        frequency=drug.frequency,

        duration_days=drug.duration_days,

        risk_level=report.risk_level,

        overall_confidence=report.overall_confidence,

        summary_text=report.summary_text,

        patient_cmax=report.pharmacokinetic_results.metrics_patient.cmax,

        patient_half_life_h=report.pharmacokinetic_results.metrics_patient.half_life_h,

        patient_auc=report.pharmacokinetic_results.metrics_patient.auc,

        clearance_factor=report.patient_profile.clearance_adjustment_factor,

        accumulation_risk=report.pharmacokinetic_results.accumulation_risk,

        full_report=report.model_dump(mode="json"),

    )

    db.add(sim)

    db.commit()

    db.refresh(sim)

    return sim

def run_and_persist(

    db: Session,

    patient_data: PatientInput,

    drug: DrugInput,

    save_patient: bool = True,

) -> tuple[SimulationReport, Simulation]:

    """
    Run the full simulation and optionally persist patient + result.
    Returns (report, simulation_row).
    """

    patient_id = None

    if save_patient:

        patient = create_patient(db, patient_data)

        patient_id = patient.id

    report = run_full_simulation(patient_data, drug)

    sim = save_simulation(db, report, drug, patient_id=patient_id)

    return report, sim

def get_simulation(db: Session, simulation_id: int) -> Optional[Simulation]:

    return db.query(Simulation).filter(Simulation.id == simulation_id).first()

def list_simulations(

    db: Session,

    patient_id: Optional[int] = None,

    skip: int = 0,

    limit: int = 50,

) -> List[Simulation]:

    q = db.query(Simulation)

    if patient_id is not None:

        q = q.filter(Simulation.patient_id == patient_id)

    return q.order_by(Simulation.created_at.desc()).offset(skip).limit(limit).all()

