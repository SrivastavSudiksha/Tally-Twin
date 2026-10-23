"""
Example: merge parse-report into existing app/api/v1/patients.py

Copy the imports + parse_lab_report endpoint into your patients.py
OR use the separate patients_parse_report.py module + router_patch.py
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, File, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.schemas.patient import PatientInput
from app.services.patient_service import (
    create_patient,
    get_patient,
    list_patients,
    delete_patient,
)
from app.core.security import require_api_key
from app.core.rate_limit import rate_limit
from app.core.audit import audit_event
from app.schemas.lab_report import LabReportParseResponse, LabReportParsedFields
from app.services.lab_report_parser import parse_lab_report_file

router = APIRouter(prefix="/patients", tags=["Patients"])

MAX_REPORT_BYTES = 12 * 1024 * 1024


class PatientResponse(BaseModel):
    id: int
    external_id: Optional[str] = None
    age: int
    sex: str
    weight_kg: float
    height_cm: Optional[float] = None
    bmi: Optional[float] = None
    egfr: Optional[float] = None
    clearance_adjustment_factor: Optional[float] = None
    conditions: Optional[list] = None
    allergies: Optional[list] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


def _to_response(patient) -> PatientResponse:
    return PatientResponse(
        id=patient.id,
        external_id=patient.external_id,
        age=patient.age,
        sex=patient.sex,
        weight_kg=patient.weight_kg,
        height_cm=patient.height_cm,
        bmi=patient.bmi,
        egfr=patient.egfr,
        clearance_adjustment_factor=patient.clearance_adjustment_factor,
        conditions=patient.conditions,
        allergies=patient.allergies,
        created_at=patient.created_at.isoformat() if patient.created_at else None,
    )


@router.post("/parse-report", response_model=LabReportParseResponse)
async def parse_lab_report(
    request: Request,
    file: UploadFile = File(...),
    _key=Depends(require_api_key),
):
    """Upload lab report image/PDF → extract demographics + labs for form auto-fill."""
    rate_limit(request, max_per_minute=15)

    ct = (file.content_type or "").lower()
    name = file.filename or ""
    allowed = (
        ct.startswith("image/")
        or "pdf" in ct
        or name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".pdf"))
    )
    if not allowed:
        raise HTTPException(status_code=400, detail="File must be an image or PDF")

    data = await file.read()
    if len(data) > MAX_REPORT_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 12 MB)")
    if len(data) < 100:
        raise HTTPException(status_code=400, detail="File appears empty")

    result = parse_lab_report_file(data, content_type=ct, filename=name)
    audit_event(
        "lab_report_parse",
        extra=f"source={result.get('source')} fields={list((result.get('fields') or {}).keys())}",
    )
    fields_raw = result.get("fields") or {}
    fields = LabReportParsedFields(**{k: v for k, v in fields_raw.items() if v is not None})
    return LabReportParseResponse(
        source=result.get("source") or "none",
        message=result.get("message"),
        confidence=result.get("confidence"),
        fields=fields,
        raw_text_preview=result.get("raw_text_preview"),
        warnings=result.get("warnings") or [],
    )


@router.post("", response_model=PatientResponse, status_code=201)
def create_patient_endpoint(
    request: Request,
    data: PatientInput,
    external_id: Optional[str] = Query(None, description="Optional external identifier"),
    db: Session = Depends(get_db),
    _key=Depends(require_api_key),
):
    rate_limit(request)
    patient = create_patient(db, data, external_id=external_id)
    audit_event("patient_create", patient_id=patient.id)
    return _to_response(patient)


@router.get("", response_model=List[PatientResponse])
def list_patients_endpoint(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _key=Depends(require_api_key),
):
    rate_limit(request)
    patients = list_patients(db, skip=skip, limit=limit)
    return [_to_response(p) for p in patients]


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient_endpoint(
    request: Request,
    patient_id: int,
    db: Session = Depends(get_db),
    _key=Depends(require_api_key),
):
    rate_limit(request)
    patient = get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return _to_response(patient)


@router.delete("/{patient_id}", status_code=204)
def delete_patient_endpoint(
    request: Request,
    patient_id: int,
    db: Session = Depends(get_db),
    _key=Depends(require_api_key),
):
    rate_limit(request)
    ok = delete_patient(db, patient_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Patient not found")
    audit_event("patient_delete", patient_id=patient_id)
    return None
