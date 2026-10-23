"""
Very lightweight adverse-effect prediction for MVP.
Uses static priors + simple modifiers from patient factors.
"""

from typing import List

from app.schemas.report import AdverseEffect

                                                         

ADVERSE_PRIORS = {

    "ibuprofen": [

        ("Gastrointestinal upset / dyspepsia", 0.25, "GI"),

        ("Increased bleeding risk", 0.12, "Hematologic"),

        ("Renal function decline", 0.08, "Kidney"),

        ("Hypertension / fluid retention", 0.07, "Cardiovascular"),

        ("Hypersensitivity / rash", 0.04, "Skin"),

    ],

    "paracetamol": [

        ("Hepatotoxicity (overdose)", 0.05, "Liver"),

        ("Nausea", 0.08, "GI"),

        ("Skin rash", 0.03, "Skin"),

        ("Hypersensitivity", 0.02, "Immune"),

        ("Rare blood dyscrasias", 0.01, "Hematologic"),

    ],

    "acetaminophen": [

        ("Hepatotoxicity (overdose)", 0.05, "Liver"),

        ("Nausea", 0.08, "GI"),

        ("Skin rash", 0.03, "Skin"),

        ("Hypersensitivity", 0.02, "Immune"),

        ("Rare blood dyscrasias", 0.01, "Hematologic"),

    ],

    "metformin": [

        ("GI intolerance (diarrhea, nausea)", 0.30, "GI"),

        ("Vitamin B12 deficiency (long-term)", 0.10, "Metabolic"),

        ("Lactic acidosis (rare)", 0.01, "Metabolic"),

        ("Metallic taste", 0.05, "GI"),

        ("Reduced appetite", 0.08, "GI"),

    ],

    "default": [

        ("Nausea / GI upset", 0.15, "GI"),

        ("Headache", 0.10, "CNS"),

        ("Dizziness", 0.08, "CNS"),

        ("Rash", 0.05, "Skin"),

        ("Fatigue", 0.07, "General"),

    ],

}

def predict_adverse_effects(

    drug_name: str,

    patient_egfr: float,

    liver_score: float,

    age: int,

    conditions: List[str],

) -> List[AdverseEffect]:

    key = drug_name.strip().lower()

    priors = ADVERSE_PRIORS.get(key, ADVERSE_PRIORS["default"])

    results = []

    for effect, base_p, organ in priors:

        p = base_p

                   

        if "renal" in effect.lower() or organ == "Kidney":

            if patient_egfr < 45:

                p *= 2.2

            elif patient_egfr < 60:

                p *= 1.5

        if "hepat" in effect.lower() or organ == "Liver":

            if liver_score < 0.6:

                p *= 2.0

            elif liver_score < 0.8:

                p *= 1.4

        if age >= 75:

            p *= 1.25

        if any(c in ["kidney disease", "ckd", "renal"] for c in [x.lower() for x in conditions]):

            if organ == "Kidney":

                p *= 1.6

        p = min(0.95, round(p, 3))

        results.append(AdverseEffect(effect=effect, probability=p, organ=organ))

                                 

    results.sort(key=lambda x: x.probability, reverse=True)

    return results[:5]

