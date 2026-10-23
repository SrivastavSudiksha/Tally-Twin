"""Single source of truth for DDI + allergy cross-reactivity + drug classes."""

from typing import List, Dict, Any

DRUG_CLASSES: Dict[str, List[str]] = {

    "nsaid": ["ibuprofen", "naproxen", "diclofenac", "ketorolac", "indomethacin", "celecoxib", "meloxicam", "aspirin", "mefenamic"],

    "penicillin": ["penicillin", "amoxicillin", "ampicillin", "piperacillin", "flucloxacillin", "augmentin", "amoxyclav"],

    "cephalosporin": ["ceftriaxone", "cefixime", "cephalexin", "cefazolin", "cefuroxime"],

    "sulfa": ["sulfamethoxazole", "cotrimoxazole", "sulfasalazine", "sulfadiazine"],

    "statin": ["simvastatin", "atorvastatin", "rosuvastatin", "pravastatin", "lovastatin"],

    "ace_inhibitor": ["enalapril", "lisinopril", "ramipril", "perindopril", "captopril"],

    "arb": ["losartan", "telmisartan", "olmesartan", "valsartan", "candesartan"],

}

ALLERGY_CROSSWALK: List[Dict[str, Any]] = [

    {"allergy_tokens": ["penicillin", "penicillins", "amoxicillin"], "classes": ["penicillin"], "severity": "contraindicated"},

    {"allergy_tokens": ["nsaid", "ibuprofen", "aspirin", "nsaids"], "classes": ["nsaid"], "severity": "contraindicated"},

    {"allergy_tokens": ["sulfa", "sulfonamide", "cotrimoxazole"], "classes": ["sulfa"], "severity": "contraindicated"},

    {"allergy_tokens": ["cephalosporin", "ceftriaxone"], "classes": ["cephalosporin"], "severity": "contraindicated"},

]

def drug_classes_for(name: str) -> List[str]:

    n = name.lower()

    out = []

    for cls, members in DRUG_CLASSES.items():

        if any(m in n for m in members) or cls in n:

            out.append(cls)

    return out

def allergy_hits(drug_name: str, allergies: List[str]) -> List[Dict[str, str]]:

    hits = []

    drug_l = drug_name.lower()

    d_classes = set(drug_classes_for(drug_name))

    for a in allergies:

        al = a.lower().strip()

        if not al:

            continue

        if al in drug_l or drug_l in al:

            hits.append({"matched_item": a, "severity": "contraindicated", "message": f"Allergy match: {a}"})

            continue

        for rule in ALLERGY_CROSSWALK:

            if any(t in al for t in rule["allergy_tokens"]):

                if d_classes.intersection(rule["classes"]):

                    hits.append({

                        "matched_item": a,

                        "severity": rule["severity"],

                        "message": f"Class cross-reactivity: allergy '{a}' vs {drug_name}",

                    })

    return hits

CHECKED_DDI_LABELS = [

    "NSAID–warfarin", "NSAID–aspirin", "NSAID–metformin", "NSAID–amlodipine",

    "warfarin–omeprazole", "statin–clarithromycin", "clopidogrel–omeprazole",

    "digoxin–amiodarone", "metformin–cimetidine",

]

