from pydantic import BaseModel, Field

from typing import List, Optional, Literal, Dict, Any

from .patient import PatientProfileSnapshot, Medicine

from .drug import DrugProfile

class RiskLevel(str):

    SAFE = "Safe"

    CAUTION = "Caution"

    HIGH_RISK = "High Risk"

class ConfidenceLevel(str):

    LOW = "Low"

    MEDIUM = "Medium"

    HIGH = "High"

class PKMetrics(BaseModel):

    cmax: float = Field(..., description="Peak concentration (arbitrary units or mg/L)")

    tmax_h: float

    half_life_h: float

    auc: float

    accumulation_factor: float

    clearance_adjusted: float

    vd_adjusted: float

class ConcentrationPoint(BaseModel):

    time_h: float

    concentration: float

class PKResults(BaseModel):

    average_person_curve: List[ConcentrationPoint]

    patient_curve: List[ConcentrationPoint]

    metrics_average: PKMetrics

    metrics_patient: PKMetrics

    therapeutic_window_low: Optional[float] = None

    therapeutic_window_high: Optional[float] = None

    toxic_threshold: Optional[float] = None

    accumulation_risk: Literal["low", "moderate", "high"]

class DoseAssessment(BaseModel):

    standard_dose_assessment: Literal["too_high", "appropriate", "too_low"]

    suggested_adjustment_range: str                           

    rationale: str

class DrugInteraction(BaseModel):

    interacting_drug: str

    interaction_type: str

    severity: Literal["minor", "moderate", "major"]

    mechanism: str

    recommendation: str

class AdverseEffect(BaseModel):

    effect: str

    probability: float = Field(..., ge=0, le=1)

    organ: Optional[str] = None

class OrganFlag(BaseModel):

    organ: str

    risk_level: Literal["low", "moderate", "high"]

    reason: str

class Contraindication(BaseModel):

    type: Literal["allergy", "condition", "pregnancy", "other"]

    matched_item: str

    severity: Literal["warning", "contraindicated"]

    message: str

class Explainability(BaseModel):

    top_patient_parameters: List[Dict[str, Any]]                                            

    structural_toxicity_notes: List[str] = Field(default_factory=list)

    key_drivers_summary: str

class ConfidenceAndQuality(BaseModel):

    overall_confidence: Literal["Low", "Medium", "High"]

    per_prediction_scores: Dict[str, float]                                  

    data_quality_warnings: List[str] = Field(default_factory=list)

    novel_compound_flag: bool = False

class SimulationReport(BaseModel):

                

    risk_level: Literal["Safe", "Caution", "High Risk"]

    overall_confidence: Literal["Low", "Medium", "High"]

    summary_text: str

                        

    patient_profile: PatientProfileSnapshot

                     

    drug_profile: DrugProfile

                   

    pharmacokinetic_results: PKResults

                        

    dose_assessment: DoseAssessment

                               

    drug_drug_interactions: List[DrugInteraction]

                            

    adverse_effects: List[AdverseEffect]

    organ_flags: List[OrganFlag]

                          

    contraindications: List[Contraindication]

                       

    explainability: Explainability

                                   

    confidence_and_quality: ConfidenceAndQuality

class SimulationRequest(BaseModel):

    patient: "PatientInput"

    drug: "DrugInput"

                          

from .patient import PatientInput

from .drug import DrugInput

SimulationRequest.model_rebuild()

