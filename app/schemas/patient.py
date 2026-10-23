from pydantic import BaseModel, Field, computed_field, field_validator

from typing import Optional, List, Literal

from enum import Enum

class Sex(str, Enum):

    male = "male"

    female = "female"

    other = "other"

class Medicine(BaseModel):

    name: str = Field(..., min_length=1, max_length=100)

    dose_mg: float = Field(..., gt=0)

    frequency: str = Field(..., description="e.g. OD, BD, TDS, QID or 'once daily'")

    route: Optional[str] = "oral"

class PatientInput(BaseModel):

    age: int = Field(..., ge=0, le=120)

    sex: Sex

    weight_kg: float = Field(..., gt=2, le=300, description="kg")

    height_cm: Optional[float] = Field(None, gt=0, le=250)

            

    serum_creatinine: Optional[float] = Field(None, gt=0, le=20, description="mg/dL (not µmol/L)")

    egfr: Optional[float] = Field(None, gt=0, description="mL/min/1.73m² – if provided, preferred over calculated")

           

    alt: Optional[float] = Field(None, ge=0, le=5000, description="U/L")

    ast: Optional[float] = Field(None, ge=0, le=5000, description="U/L")

    bilirubin: Optional[float] = Field(None, ge=0, description="mg/dL")

    albumin: Optional[float] = Field(None, ge=0, le=6, description="g/dL")

    inr: Optional[float] = Field(None, ge=0.5, le=10, description="INR for Child-Pugh")

    conditions: List[str] = Field(default_factory=list, max_length=30)

    current_medicines: List[Medicine] = Field(default_factory=list, max_length=40)

    allergies: List[str] = Field(default_factory=list, max_length=40)

    smoking: bool = False

    alcohol: Literal["none", "occasional", "moderate", "heavy"] = "none"

                       

    cyp2d6: Optional[str] = None                                       

    cyp2c19: Optional[str] = None

    cyp2c9: Optional[str] = None

    qtc_ms: Optional[float] = Field(None, gt=0, description="QTc in ms")

    @computed_field

    @property

    def bmi(self) -> Optional[float]:

        if self.height_cm and self.height_cm > 0:

            h_m = self.height_cm / 100

            return round(self.weight_kg / (h_m * h_m), 1)

        return None

class PatientProfileSnapshot(BaseModel):

    age: int

    sex: str

    weight_kg: float

    height_cm: Optional[float]

    bmi: Optional[float]

    serum_creatinine: Optional[float]

    egfr: Optional[float]

    egfr_category: str

    alt: Optional[float]

    ast: Optional[float]

    liver_capacity_score: float       

    conditions: List[str]

    current_medicines: List[Medicine]

    allergies: List[str]

    smoking: bool

    alcohol: str

    clearance_adjustment_factor: float                                                

