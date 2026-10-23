"""
Parse patient lab reports (image or PDF text) into structured fields.

MVP strategy:
1. OCR image/PDF page with Tesseract when available
2. Regex patterns tuned for common Indian / international lab report layouts
3. Unit normalisation (µmol/L creatinine → mg/dL, etc.)
4. Never invent values — return only what was matched with reasonable confidence
"""

from __future__ import annotations

import re
import logging
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

def _num(s: str) -> Optional[float]:
    try:
        return float(s.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def _first_match(patterns: List[str], text: str, flags: int = re.I) -> Optional[re.Match]:
    for p in patterns:
        m = re.search(p, text, flags)
        if m:
            return m
    return None


# Age
AGE_PATTERNS = [
    r"(?:age| उम्र|वय)\s*[:\-]?\s*(\d{1,3})\s*(?:y(?:ears?)?|yrs?|यर्ष)?",
    r"(\d{1,3})\s*(?:years?\s*old|yrs?\s*old|y/?o)",
]

# Sex
SEX_PATTERNS = [
    r"(?:sex|gender|लिंग|लिङ्ग)\s*[:\-]?\s*(male|female|m|f|पुरुष|महिला|स्त्री)",
    r"\b(male|female)\b",
]

# Weight
WEIGHT_PATTERNS = [
    r"(?:weight|wt|वजन)\s*[:\-]?\s*(\d{2,3}(?:\.\d+)?)\s*(?:kg|kgs?)?",
]

# Height
HEIGHT_PATTERNS = [
    r"(?:height|ht|ऊँचाई|ऊंचाई)\s*[:\-]?\s*(\d{2,3}(?:\.\d+)?)\s*(?:cm|cms?)?",
    r"(?:height|ht)\s*[:\-]?\s*(\d)'\s*(\d{1,2})\"?",  # feet'inches
]

# Creatinine (mg/dL preferred; convert µmol/L if needed)
CREAT_PATTERNS = [
    r"(?:serum\s*)?creatinine(?:\s*\(?(?:s\.?\s*cr|scr)\)?)?\s*[:\-]?\s*(\d+\.?\d*)\s*(mg/?dL|mg/dl|µmol/?L|umol/?L|μmol/?L)?",
    r"(?:क्रिएटिनिन|creatinine)\s*[:\-]?\s*(\d+\.?\d*)",
]

# eGFR
EGFR_PATTERNS = [
    r"(?:e\s*GFR|egfr|estimated\s*gfr)\s*[:\-]?\s*(\d+\.?\d*)\s*(?:mL/?min(?:/1\.73\s*m²?)?)?",
    r"GFR\s*[:\-]?\s*(\d+\.?\d*)",
]

# ALT / SGPT
ALT_PATTERNS = [
    r"(?:ALT|SGPT|alanine\s*aminotransferase|अलानाइन)\s*[:\-]?\s*(\d+\.?\d*)\s*(?:U/?L|IU/?L)?",
]

# AST / SGOT
AST_PATTERNS = [
    r"(?:AST|SGOT|aspartate\s*aminotransferase)\s*[:\-]?\s*(\d+\.?\d*)\s*(?:U/?L|IU/?L)?",
]

# Bilirubin (total preferred)
BILI_PATTERNS = [
    r"(?:total\s*)?bilirubin(?:\s*\(?t\.?\s*bil\)?)?\s*[:\-]?\s*(\d+\.?\d*)\s*(?:mg/?dL|mg/dl)?",
    r"(?:बिलीरुबिन)\s*[:\-]?\s*(\d+\.?\d*)",
]

# Albumin
ALB_PATTERNS = [
    r"(?:serum\s*)?albumin\s*[:\-]?\s*(\d+\.?\d*)\s*(?:g/?dL|g/dl|g/?L)?",
]

# Optional extras
HB_PATTERNS = [r"(?:haemoglobin|hemoglobin|hb|Hb)\s*[:\-]?\s*(\d+\.?\d*)"]
GLU_PATTERNS = [r"(?:glucose|fbs|rbs|blood\s*sugar)\s*[:\-]?\s*(\d+\.?\d*)"]
NA_PATTERNS = [r"(?:sodium|na\+?)\s*[:\-]?\s*(\d+\.?\d*)"]
K_PATTERNS = [r"(?:potassium|k\+?)\s*[:\-]?\s*(\d+\.?\d*)"]


def _extract_age(text: str) -> Optional[int]:
    m = _first_match(AGE_PATTERNS, text)
    if not m:
        return None
    v = int(m.group(1))
    return v if 0 < v <= 120 else None


def _extract_sex(text: str) -> Optional[str]:
    m = _first_match(SEX_PATTERNS, text)
    if not m:
        return None
    raw = m.group(1).lower()
    if raw in ("m", "male", "पुरुष"):
        return "male"
    if raw in ("f", "female", "महिला", "स्त्री"):
        return "female"
    return "other"


def _extract_weight(text: str) -> Optional[float]:
    m = _first_match(WEIGHT_PATTERNS, text)
    if not m:
        return None
    v = _num(m.group(1))
    return v if v and 2 < v <= 300 else None


def _extract_height(text: str) -> Optional[float]:
    # cm form
    m = _first_match(HEIGHT_PATTERNS[:1], text)
    if m:
        v = _num(m.group(1))
        if v and 40 < v <= 250:
            return v
    # feet'inches
    m = re.search(HEIGHT_PATTERNS[1], text, re.I)
    if m:
        feet, inches = int(m.group(1)), int(m.group(2))
        cm = feet * 30.48 + inches * 2.54
        return round(cm, 1) if 40 < cm <= 250 else None
    return None


def _extract_creatinine(text: str) -> Optional[float]:
    m = _first_match(CREAT_PATTERNS, text)
    if not m:
        return None
    v = _num(m.group(1))
    if v is None:
        return None
    unit = (m.group(2) or "mg/dL").lower() if m.lastindex and m.lastindex >= 2 else "mg/dl"
    # µmol/L → mg/dL (divide by 88.4)
    if "umol" in unit or "µmol" in unit or "μmol" in unit:
        v = v / 88.4
    # plausible serum creatinine range in mg/dL
    if 0.1 <= v <= 20:
        return round(v, 2)
    return None


def _extract_egfr(text: str) -> Optional[float]:
    m = _first_match(EGFR_PATTERNS, text)
    if not m:
        return None
    v = _num(m.group(1))
    return round(v, 1) if v and 1 <= v <= 200 else None


def _extract_alt(text: str) -> Optional[float]:
    m = _first_match(ALT_PATTERNS, text)
    if not m:
        return None
    v = _num(m.group(1))
    return round(v, 1) if v is not None and 0 <= v <= 5000 else None


def _extract_ast(text: str) -> Optional[float]:
    m = _first_match(AST_PATTERNS, text)
    if not m:
        return None
    v = _num(m.group(1))
    return round(v, 1) if v is not None and 0 <= v <= 5000 else None


def _extract_bilirubin(text: str) -> Optional[float]:
    m = _first_match(BILI_PATTERNS, text)
    if not m:
        return None
    v = _num(m.group(1))
    return round(v, 2) if v is not None and 0 <= v <= 50 else None


def _extract_albumin(text: str) -> Optional[float]:
    m = _first_match(ALB_PATTERNS, text)
    if not m:
        return None
    v = _num(m.group(1))
    # g/L sometimes reported (35–50); convert to g/dL
    if v and v > 10:
        v = v / 10.0
    return round(v, 2) if v is not None and 0.5 <= v <= 6 else None


def parse_lab_text(text: str) -> Tuple[Dict[str, Any], List[str]]:
    """
    Run all extractors on OCR / plain text.
    Returns (fields_dict, warnings).
    """
    warnings: List[str] = []
    if not text or len(text.strip()) < 10:
        return {}, ["No usable text found in report"]

    # Normalise whitespace for easier matching
    t = re.sub(r"[ \t]+", " ", text)
    t = re.sub(r"\r\n?", "\n", t)

    fields: Dict[str, Any] = {}

    age = _extract_age(t)
    if age is not None:
        fields["age"] = age

    sex = _extract_sex(t)
    if sex:
        fields["sex"] = sex

    w = _extract_weight(t)
    if w is not None:
        fields["weight_kg"] = w

    h = _extract_height(t)
    if h is not None:
        fields["height_cm"] = h

    creat = _extract_creatinine(t)
    if creat is not None:
        fields["serum_creatinine"] = creat

    egfr = _extract_egfr(t)
    if egfr is not None:
        fields["egfr"] = egfr

    alt = _extract_alt(t)
    if alt is not None:
        fields["alt"] = alt

    ast = _extract_ast(t)
    if ast is not None:
        fields["ast"] = ast

    bili = _extract_bilirubin(t)
    if bili is not None:
        fields["bilirubin"] = bili

    alb = _extract_albumin(t)
    if alb is not None:
        fields["albumin"] = alb

    # Optional extras (not mapped to form yet, but returned)
    for key, patterns in (
        ("hemoglobin", HB_PATTERNS),
        ("glucose", GLU_PATTERNS),
        ("sodium", NA_PATTERNS),
        ("potassium", K_PATTERNS),
    ):
        m = _first_match(patterns, t)
        if m:
            v = _num(m.group(1))
            if v is not None:
                fields[key] = v

    filled = sum(1 for k in ("age", "sex", "weight_kg", "serum_creatinine", "egfr", "alt", "ast", "bilirubin", "albumin") if k in fields)
    if filled == 0:
        warnings.append("OCR text found but no recognised lab fields matched. Enter values manually.")
    elif filled < 3:
        warnings.append(f"Only {filled} field(s) matched — please review and complete the form.")

    return fields, warnings


# ---------------------------------------------------------------------------
# OCR layer
# ---------------------------------------------------------------------------

def ocr_image_bytes(data: bytes, content_type: str = "image/jpeg") -> Optional[str]:
    """
    OCR an image. Returns text or None.
    Requires pytesseract + Pillow; fails soft if missing.
    """
    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = 40_000_000
        img = Image.open(BytesIO(data))
        img = img.convert("RGB")
        w, h = img.size
        if w * h > 25_000_000:
            logger.warning("Image resolution too large for OCR")
            return None
        # Downscale very large images for speed
        max_side = 2500
        if max(w, h) > max_side:
            scale = max_side / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    except Exception as e:
        logger.warning("PIL open failed: %s", e)
        return None

    try:
        import pytesseract
        # Try English first; Indian reports often have English labels
        text = pytesseract.image_to_string(img, lang="eng") or ""
        text = " ".join(text.split())
        if len(text) < 8:
            return None
        return text
    except Exception as e:
        logger.warning("Tesseract OCR failed: %s", e)
        return None


def ocr_pdf_bytes(data: bytes) -> Optional[str]:
    """
    Extract text from PDF. Prefer embedded text; fall back to first-page raster OCR.
    """
    # 1) Try pypdf / PyPDF2 text extraction
    try:
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader  # type: ignore
        reader = PdfReader(BytesIO(data))
        chunks = []
        for page in reader.pages[:5]:  # first 5 pages max
            t = page.extract_text() or ""
            if t.strip():
                chunks.append(t)
        if chunks:
            combined = "\n".join(chunks)
            if len(combined.strip()) >= 20:
                return combined
    except Exception as e:
        logger.info("PDF text extract failed (will try OCR): %s", e)

    # 2) Rasterise first page if pdf2image available
    try:
        from pdf2image import convert_from_bytes
        pages = convert_from_bytes(data, first_page=1, last_page=1, dpi=200)
        if pages:
            buf = BytesIO()
            pages[0].convert("RGB").save(buf, format="JPEG", quality=85)
            return ocr_image_bytes(buf.getvalue())
    except Exception as e:
        logger.info("PDF raster OCR unavailable: %s", e)

    return None


def parse_lab_report_file(
    data: bytes,
    content_type: str,
    filename: str = "",
) -> Dict[str, Any]:
    """
    Main entry: bytes + content-type → structured parse result.
    """
    ct = (content_type or "").lower()
    fn = (filename or "").lower()

    text: Optional[str] = None
    source = "none"

    is_pdf = "pdf" in ct or fn.endswith(".pdf")
    is_image = ct.startswith("image/") or any(fn.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"))

    if is_pdf:
        text = ocr_pdf_bytes(data)
        source = "ocr" if text else "none"
    elif is_image:
        text = ocr_image_bytes(data, ct)
        source = "ocr" if text else "none"
    else:
        # Try as image anyway
        text = ocr_image_bytes(data)
        source = "ocr" if text else "none"

    if not text:
        return {
            "source": "none",
            "message": "Could not read text from file. Enter values manually. (Install tesseract-ocr + pytesseract for image OCR.)",
            "confidence": None,
            "fields": {},
            "raw_text_preview": None,
            "warnings": ["OCR unavailable or no text detected"],
        }

    fields, warnings = parse_lab_text(text)
    n_core = sum(
        1
        for k in ("age", "sex", "weight_kg", "serum_creatinine", "egfr", "alt", "ast", "bilirubin", "albumin")
        if k in fields
    )
    # Heuristic confidence
    conf = min(0.9, 0.25 + 0.1 * n_core) if n_core else 0.15
    if n_core >= 4:
        source = "ocr"
        msg = "Lab values extracted — please review every field before simulating."
    elif n_core > 0:
        source = "partial"
        msg = "Some values extracted — complete remaining required fields."
    else:
        source = "none"
        msg = "Text found but no lab fields matched. Enter values manually."

    return {
        "source": source,
        "message": msg,
        "confidence": round(conf, 2),
        "fields": fields,
        "raw_text_preview": (text[:500] + "…") if len(text) > 500 else text,
        "warnings": warnings,
    }
