from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.security import require_api_key
from app.core.rate_limit import rate_limit
from app.core.audit import audit_event
from app.db.session import get_db
from app.schemas.report import SimulationRequest, SimulationReport
from app.services.simulation_service import run_full_simulation
from app.services.simulation_persist import (
    run_and_persist,
    get_simulation,
    list_simulations,
)
from app.services.pdf_report import build_simulation_pdf

router = APIRouter(prefix="/simulations", tags=["Simulations"])


class SimulationSummary(BaseModel):
    id: int
    patient_id: Optional[int] = None
    drug_identifier: str
    dose_mg: float
    route: str
    frequency: str
    risk_level: str
    overall_confidence: str
    patient_cmax: Optional[float] = None
    patient_half_life_h: Optional[float] = None
    clearance_factor: Optional[float] = None
    accumulation_risk: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class SimulationRunResponse(BaseModel):
    simulation_id: Optional[int] = None
    report: SimulationReport


@router.post("/run", response_model=SimulationRunResponse)
def run_simulation(
    request: Request,
    payload: SimulationRequest,
    persist: bool = Query(True, description="Save patient + result to database"),
    db: Session = Depends(get_db),
    _key=Depends(require_api_key),
):
    """
    Main Digital Twin endpoint for clinicians.
    Runs individualized PK risk simulation from patient health data + drug
    composition/regimen. Optionally persists and returns full structured report.
    """
    rate_limit(request)
    try:
        if persist:
            report, sim = run_and_persist(
                db, payload.patient, payload.drug, save_patient=True
            )
            audit_event(
                "simulation_run",
                simulation_id=sim.id,
                patient_id=sim.patient_id,
            )
            return SimulationRunResponse(simulation_id=sim.id, report=report)
        else:
            report = run_full_simulation(payload.patient, payload.drug)
            return SimulationRunResponse(simulation_id=None, report=report)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Simulation failed: {str(e)}"
        ) from e


@router.get("", response_model=List[SimulationSummary])
def list_simulations_endpoint(
    request: Request,
    patient_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _key=Depends(require_api_key),
):
    rate_limit(request)
    sims = list_simulations(db, patient_id=patient_id, skip=skip, limit=limit)
    return [
        SimulationSummary(
            id=s.id,
            patient_id=s.patient_id,
            drug_identifier=s.drug_identifier,
            dose_mg=s.dose_mg,
            route=s.route,
            frequency=s.frequency,
            risk_level=s.risk_level,
            overall_confidence=s.overall_confidence,
            patient_cmax=s.patient_cmax,
            patient_half_life_h=s.patient_half_life_h,
            clearance_factor=s.clearance_factor,
            accumulation_risk=s.accumulation_risk,
            created_at=s.created_at.isoformat() if s.created_at else None,
        )
        for s in sims
    ]


@router.get("/{simulation_id}", response_model=SimulationReport)
def get_simulation_endpoint(
    request: Request,
    simulation_id: int,
    db: Session = Depends(get_db),
    _key=Depends(require_api_key),
):
    """Return the full stored report for a past simulation (API key required)."""
    rate_limit(request)
    sim = get_simulation(db, simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    audit_event("simulation_read", simulation_id=simulation_id, patient_id=sim.patient_id)
    return SimulationReport(**sim.full_report)


@router.get("/{simulation_id}/pdf")
def download_simulation_pdf(
    request: Request,
    simulation_id: int,
    db: Session = Depends(get_db),
    _key=Depends(require_api_key),
):
    """Clinician-facing PDF report."""
    rate_limit(request)
    sim = get_simulation(db, simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    audit_event("simulation_pdf", simulation_id=simulation_id, patient_id=sim.patient_id)
    report = SimulationReport(**sim.full_report)
    pdf_bytes = build_simulation_pdf(report, simulation_id=simulation_id)
    filename = f"digital_twin_report_{simulation_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/run/pdf")
def run_and_download_pdf(
    request: Request,
    payload: SimulationRequest,
    persist: bool = Query(True, description="Save patient + result to database"),
    db: Session = Depends(get_db),
    _key=Depends(require_api_key),
):
    """Run simulation and return PDF directly."""
    rate_limit(request)
    try:
        if persist:
            report, sim = run_and_persist(
                db, payload.patient, payload.drug, save_patient=True
            )
            audit_event(
                "simulation_run_pdf",
                simulation_id=sim.id,
                patient_id=sim.patient_id,
            )
            sim_id = sim.id
        else:
            report = run_full_simulation(payload.patient, payload.drug)
            sim_id = 0
        pdf_bytes = build_simulation_pdf(report, simulation_id=sim_id or None)
        filename = f"digital_twin_report_{sim_id or 'live'}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Simulation failed: {str(e)}"
        ) from e
