"""Schemas for lab-report OCR / parse response."""

from typing import Optional, List
from pydantic import BaseModel, Field


class LabReportParsedFields(BaseModel):
    """Extracted patient / lab values. All optional — only filled fields are returned."""

    age: Optional[int] = Field(None, ge=0, le=120)
    sex: Optional[str] = Field(None, description="male | female | other")
    weight_kg: Optional[float] = Field(None, gt=0, le=300)
    height_cm: Optional[float] = Field(None, gt=0, le=250)

    serum_creatinine: Optional[float] = Field(None, gt=0, le=20, description="mg/dL")
    egfr: Optional[float] = Field(None, gt=0, description="mL/min/1.73m²")
    alt: Optional[float] = Field(None, ge=0, le=5000, description="U/L")
    ast: Optional[float] = Field(None, ge=0, le=5000, description="U/L")
    bilirubin: Optional[float] = Field(None, ge=0, description="mg/dL")
    albumin: Optional[float] = Field(None, ge=0, le=6, description="g/dL")

    hemoglobin: Optional[float] = None
    glucose: Optional[float] = None
    sodium: Optional[float] = None
    potassium: Optional[float] = None


class LabReportParseResponse(BaseModel):
    source: str = Field(..., description="ocr | none | partial")
    message: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)
    fields: LabReportParsedFields = Field(default_factory=LabReportParsedFields)
    raw_text_preview: Optional[str] = Field(
        None, description="First ~500 chars of OCR text for debugging"
    )
    warnings: List[str] = Field(default_factory=list)
