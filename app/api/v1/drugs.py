from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional

from app.utils.rdkit_utils import extract_molecular_properties, get_basic_drug_knowledge
from app.schemas.drug import MolecularProperties, DrugProfile
from app.core.security import require_api_key
from app.core.rate_limit import rate_limit

router = APIRouter(prefix="/drugs", tags=["Drugs"])


class DrugLookupRequest(BaseModel):
    identifier: str = Field(..., min_length=1, max_length=512)


class CompositionFromImageResponse(BaseModel):
    composition: Optional[str] = None
    source: str = "none"
    message: Optional[str] = None
    confidence: Optional[float] = None


@router.post("/lookup", response_model=DrugProfile)
async def lookup_drug(
    request: Request,
    payload: DrugLookupRequest,
    _key=Depends(require_api_key),
):
    """Return molecular properties + basic knowledge for a drug name or SMILES."""
    rate_limit(request)
    mol = extract_molecular_properties(payload.identifier)
    knowledge = get_basic_drug_knowledge(payload.identifier)
    return DrugProfile(
        name=payload.identifier,
        identifier_used=payload.identifier,
        molecular_properties=MolecularProperties(**mol),
        known_targets=knowledge.get("targets", []),
        metabolism_pathways=knowledge.get("metabolism", []),
        cyp_enzymes=knowledge.get("cyp_enzymes", []),
        therapeutic_window_note=knowledge.get("therapeutic_window"),
    )


@router.post("/composition-from-image", response_model=CompositionFromImageResponse)
async def composition_from_image(
    request: Request,
    file: UploadFile = File(...),
    _key=Depends(require_api_key),
):
    """
    Accept a pack/label image and return detected composition text.
    Production: plug in OCR (Tesseract / cloud Vision). MVP returns a safe stub.
    """
    rate_limit(request, max_per_minute=20)

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 8 MB)")

    text = None
    try:
        from io import BytesIO
        from PIL import Image

        Image.MAX_IMAGE_PIXELS = 40_000_000
        img = Image.open(BytesIO(data))
        img = img.convert("RGB")
        w, h = img.size
        if w * h > 25_000_000:
            raise HTTPException(status_code=400, detail="Image resolution too large")

        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        try:
            import pytesseract

            text = pytesseract.image_to_string(Image.open(BytesIO(buf.getvalue()))) or None
        except Exception:
            text = None

        if text:
            text = " ".join(text.split())
            if len(text) < 8:
                text = None
    except HTTPException:
        raise
    except Exception:
        text = None

    if text:
        return CompositionFromImageResponse(
            composition=text[:2000],
            source="ocr",
            message="Text extracted from image",
            confidence=0.55,
        )

    return CompositionFromImageResponse(
        composition=None,
        source="none",
        message="OCR not available or no text found. Enter composition manually.",
        confidence=None,
    )
