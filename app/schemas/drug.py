from pydantic import BaseModel, Field

from typing import Optional, List, Literal, Dict, Any

class DrugInput(BaseModel):

    identifier: str = Field(..., min_length=1, description="Drug name or SMILES string")

    dose_mg: float = Field(..., gt=0)

    route: Literal["oral", "iv"] = "oral"

    frequency: str = Field(..., description="e.g. OD, BD, TDS, QID, or 'every 8 hours'")

    duration_days: int = Field(..., ge=1, le=365)

    composition: Optional[str] = Field(None, max_length=4000, description="Free-text composition")

    composition_rows: Optional[List[Dict[str, Any]]] = Field(None, max_length=40)

    interval_hours: Optional[float] = Field(None, gt=0, le=168, description="Custom dosing interval τ in hours")

class MolecularProperties(BaseModel):

    molecular_weight: Optional[float] = None

    logp: Optional[float] = None

    tpsa: Optional[float] = None

    hbd: Optional[int] = None

    hba: Optional[int] = None

    smiles: Optional[str] = None

    is_valid_molecule: bool = False

class DrugProfile(BaseModel):

    name: str

    identifier_used: str

    molecular_properties: MolecularProperties

    known_targets: List[str] = Field(default_factory=list)

    metabolism_pathways: List[str] = Field(default_factory=list)

    cyp_enzymes: List[str] = Field(default_factory=list)

    therapeutic_window_note: Optional[str] = None

