"""
Patient-derived pharmacokinetic adjustment factors.

- eGFR: CKD-EPI 2021 (race-free)
- CrCl: Cockcroft-Gault (mL/min)
- fe-based clearance split
- Liver: capacity score + optional Child-Pugh
"""

from typing import Optional, List

def calculate_bmi(weight_kg: float, height_cm: Optional[float]) -> Optional[float]:

    if not height_cm or height_cm <= 0:

        return None

    h_m = height_cm / 100.0

    return round(weight_kg / (h_m * h_m), 1)

def calculate_egfr_ckd_epi(age: int, sex: str, serum_creatinine: float) -> float:

    if serum_creatinine <= 0:

        return 90.0

    sex_l = sex.lower()

    kappa = 0.7 if sex_l == "female" else 0.9

    alpha = -0.241 if sex_l == "female" else -0.302

    sex_factor = 1.012 if sex_l == "female" else 1.0

    scr_k = serum_creatinine / kappa

    egfr = (

        142

        * (min(scr_k, 1) ** alpha)

        * (max(scr_k, 1) ** -1.200)

        * (0.9938 ** age)

        * sex_factor

    )

    return round(egfr, 1)

def cockcroft_gault(

    age: int, sex: str, weight_kg: float, serum_creatinine: float

) -> Optional[float]:

    if not serum_creatinine or serum_creatinine <= 0 or age <= 0 or weight_kg <= 0:

        return None

    crcl = ((140 - age) * weight_kg) / (72 * serum_creatinine)

    if sex.lower() == "female":

        crcl *= 0.85

    return round(crcl, 1)

def egfr_category(egfr: float) -> str:

    if egfr >= 90:

        return "Normal / High (≥90)"

    if egfr >= 60:

        return "Mildly decreased (60-89)"

    if egfr >= 45:

        return "Mild-moderate (45-59)"

    if egfr >= 30:

        return "Moderate-severe (30-44)"

    if egfr >= 15:

        return "Severe (15-29)"

    return "Kidney failure (<15)"

def liver_capacity_score(

    alt: Optional[float],

    ast: Optional[float],

    bilirubin: Optional[float] = None,

    albumin: Optional[float] = None,

) -> float:

    score = 1.0

    if alt is not None:

        if alt > 200:

            score -= 0.35

        elif alt > 100:

            score -= 0.20

        elif alt > 50:

            score -= 0.10

    if ast is not None:

        if ast > 200:

            score -= 0.30

        elif ast > 100:

            score -= 0.15

        elif ast > 50:

            score -= 0.08

    if bilirubin is not None and bilirubin > 1.5:

        score -= 0.15 if bilirubin < 3 else 0.25

    if albumin is not None and albumin < 3.5:

        score -= 0.10 if albumin >= 3.0 else 0.20

    return max(0.2, round(score, 2))

def child_pugh_class(

    bilirubin: Optional[float],

    albumin: Optional[float],

    inr: Optional[float],

    ascites: str = "none",

    encephalopathy: str = "none",

) -> Optional[dict]:

    points = 0

    if bilirubin is not None:

        if bilirubin < 2:

            points += 1

        elif bilirubin <= 3:

            points += 2

        else:

            points += 3

    if albumin is not None:

        if albumin > 3.5:

            points += 1

        elif albumin >= 2.8:

            points += 2

        else:

            points += 3

    if inr is not None:

        if inr < 1.7:

            points += 1

        elif inr <= 2.3:

            points += 2

        else:

            points += 3

    lab_n = sum(x is not None for x in (bilirubin, albumin, inr))

    if lab_n < 2:

        return None

    asc = (ascites or "none").lower()

    if asc in ("mild", "slight"):

        points += 2

    elif asc in ("moderate", "severe", "marked"):

        points += 3

    else:

        points += 1

    enc = (encephalopathy or "none").lower()

    if enc in ("mild", "grade1", "grade 1", "1"):

        points += 2

    elif enc in ("moderate", "severe", "grade2", "grade3", "2", "3"):

        points += 3

    else:

        points += 1

    if points <= 6:

        return {"class": "A", "points": points, "hepatic_clearance_factor": 1.0}

    if points <= 9:

        return {"class": "B", "points": points, "hepatic_clearance_factor": 0.7}

    return {"class": "C", "points": points, "hepatic_clearance_factor": 0.4}

def renal_function_factor(egfr: float, crcl: Optional[float] = None) -> float:

    ref = crcl if crcl is not None and crcl > 0 else egfr

    if ref >= 90:

        return 1.0

    if ref >= 60:

        return 0.85

    if ref >= 30:

        return 0.55

    if ref >= 15:

        return 0.35

    return 0.20

def fe_based_clearance_multiplier(fe: float, renal_factor: float, hepatic_factor: float) -> float:

    fe = max(0.0, min(1.0, fe))

    return fe * renal_factor + (1.0 - fe) * hepatic_factor

def overall_clearance_factor(

    egfr: float,

    liver_score: float,

    age: int,

    sex: str,

    fe: float = 0.3,

    crcl: Optional[float] = None,

    child_pugh_hepatic_factor: Optional[float] = None,

    smoking: bool = False,

    alcohol: str = "none",

    conditions: Optional[List[str]] = None,

    ddi_cl_multiplier: float = 1.0,

) -> float:

    conditions = conditions or []

    renal_f = renal_function_factor(egfr, crcl)

    hepatic_f = child_pugh_hepatic_factor if child_pugh_hepatic_factor is not None else liver_score

    factor = fe_based_clearance_multiplier(fe, renal_f, hepatic_f)

    if age >= 75:

        factor *= 0.85

    elif age >= 65:

        factor *= 0.92

    if smoking:

        factor *= 1.08

    if alcohol == "heavy":

        factor *= 0.90

    elif alcohol == "moderate":

        factor *= 0.95

    cond_lower = [c.lower() for c in conditions]

    if any(x in cond_lower for x in ["heart failure", "chf", "heart disease"]):

        factor *= 0.90

    if ("cirrhosis" in cond_lower or "liver disease" in cond_lower) and child_pugh_hepatic_factor is None:

        factor *= 0.75

    factor *= ddi_cl_multiplier

    return round(max(0.15, min(2.0, factor)), 3)

def derive_patient_pk_params(

    age: int,

    sex: str,

    weight_kg: float,

    height_cm: Optional[float],

    serum_creatinine: Optional[float],

    egfr_provided: Optional[float],

    alt: Optional[float],

    ast: Optional[float],

    bilirubin: Optional[float] = None,

    albumin: Optional[float] = None,

    inr: Optional[float] = None,

    smoking: bool = False,

    alcohol: str = "none",

    conditions: Optional[list] = None,

    fe: float = 0.3,

    ddi_cl_multiplier: float = 1.0,

) -> dict:

    if egfr_provided is not None:

        egfr = egfr_provided

    elif serum_creatinine is not None:

        egfr = calculate_egfr_ckd_epi(age, sex, serum_creatinine)

    else:

        egfr = 90.0

    crcl = cockcroft_gault(age, sex, weight_kg, serum_creatinine) if serum_creatinine else None

    liver_score = liver_capacity_score(alt, ast, bilirubin, albumin)

    cp = child_pugh_class(bilirubin, albumin, inr)

    cp_factor = cp["hepatic_clearance_factor"] if cp else None

    cl_factor = overall_clearance_factor(

        egfr=egfr,

        liver_score=liver_score,

        age=age,

        sex=sex,

        fe=fe,

        crcl=crcl,

        child_pugh_hepatic_factor=cp_factor,

        smoking=smoking,

        alcohol=alcohol,

        conditions=conditions,

        ddi_cl_multiplier=ddi_cl_multiplier,

    )

    return {

        "bmi": calculate_bmi(weight_kg, height_cm),

        "egfr": egfr,

        "egfr_category": egfr_category(egfr),

        "crcl_ml_min": crcl,

        "liver_capacity_score": liver_score,

        "child_pugh": cp,

        "clearance_adjustment_factor": cl_factor,

        "fe_used": fe,

        "ddi_cl_multiplier": ddi_cl_multiplier,

    }

