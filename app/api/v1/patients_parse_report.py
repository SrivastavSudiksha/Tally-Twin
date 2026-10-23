"""
POST /api/v1/patients/parse-report
Upload a lab report image or PDF → structured fields for form auto-fill.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List

from app.core.security import require_api_key
from app.core.rate_limit import rate_limit
from app.core.audit import audit_event
from app.schemas.lab_report import LabReportParseResponse, LabReportParsedFields
from app.services.lab_report_parser import parse_lab_report_file

router = APIRouter(prefix="/patients", tags=["Patients"])

MAX_BYTES = 12 * 1024 * 1024  # 12 MB


@router.post("/parse-report", response_model=LabReportParseResponse)
async def parse_lab_report(
    request: Request,
    file: UploadFile = File(...),
    _key=Depends(require_api_key),
):
    """
    Accept a blood-test / lab report image or PDF and return extracted
    demographics + kidney/liver labs for form auto-fill.

    Always review values before running a simulation. OCR can misread numbers.
    """
    rate_limit(request, max_per_minute=15)

    ct = (file.content_type or "").lower()
    name = file.filename or ""

    allowed = (
        ct.startswith("image/")
        or "pdf" in ct
        or name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".pdf"))
    )
    if not allowed:
        raise HTTPException(
            status_code=400,
            detail="File must be an image (PNG/JPEG/WebP) or PDF",
        )

    data = await file.read()
    if len(data) > MAX_BYTES:
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
