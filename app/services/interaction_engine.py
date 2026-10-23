"""
Rule-based DDI with optional clearance multipliers + contraindications.
"""

from typing import List, Tuple

from app.schemas.patient import Medicine

from app.schemas.report import DrugInteraction, Contraindication, OrganFlag

from app.data.safety_rules import allergy_hits

                                                                                            

                                                              

                               

INTERACTION_RULES = [

    {

        "a": "ibuprofen", "b": "warfarin",

        "type": "Pharmacodynamic", "severity": "major",

        "mechanism": "Increased bleeding risk (antiplatelet + anticoagulant)",

        "recommendation": "Avoid if possible; monitor INR closely",

        "cl_multiplier": 1.0,

    },

    {

        "a": "ibuprofen", "b": "aspirin",

        "type": "Pharmacodynamic", "severity": "moderate",

        "mechanism": "Increased GI bleeding; may antagonize aspirin antiplatelet effect",

        "recommendation": "Prefer alternative analgesic",

        "cl_multiplier": 1.0,

    },

    {

        "a": "ibuprofen", "b": "metformin",

        "type": "Pharmacodynamic / renal", "severity": "moderate",

        "mechanism": "NSAIDs may reduce renal function → metformin accumulation",

        "recommendation": "Monitor renal function",

        "cl_multiplier": 0.85,                                                                          

    },

    {

        "a": "ibuprofen", "b": "amlodipine",

        "type": "Pharmacodynamic", "severity": "minor",

        "mechanism": "NSAIDs can attenuate antihypertensive effect",

        "recommendation": "Monitor blood pressure",

        "cl_multiplier": 1.0,

    },

    {

        "a": "warfarin", "b": "omeprazole",

        "type": "Pharmacokinetic", "severity": "moderate",

        "mechanism": "CYP2C19/CYP3A4 inhibition → increased warfarin exposure",

        "recommendation": "Monitor INR after starting PPI",

        "cl_multiplier": 0.75,

    },

    {

        "a": "simvastatin", "b": "clarithromycin",

        "type": "Pharmacokinetic (CYP3A4)", "severity": "major",

        "mechanism": "Strong CYP3A4 inhibition raises statin levels",

        "recommendation": "Avoid combination",

        "cl_multiplier": 0.4,

    },

    {

        "a": "atorvastatin", "b": "clarithromycin",

        "type": "Pharmacokinetic (CYP3A4)", "severity": "major",

        "mechanism": "CYP3A4 inhibition raises statin exposure",

        "recommendation": "Avoid or use limited dose statin",

        "cl_multiplier": 0.45,

    },

    {

        "a": "clopidogrel", "b": "omeprazole",

        "type": "Pharmacokinetic (CYP2C19)", "severity": "moderate",

        "mechanism": "Reduced activation of clopidogrel",

        "recommendation": "Prefer pantoprazole if PPI needed",

        "cl_multiplier": 1.0,

    },

    {

        "a": "digoxin", "b": "amiodarone",

        "type": "Pharmacokinetic (P-gp)", "severity": "major",

        "mechanism": "P-gp inhibition increases digoxin levels",

        "recommendation": "Reduce digoxin dose; monitor levels",

        "cl_multiplier": 0.6,

    },

    {

        "a": "metformin", "b": "cimetidine",

        "type": "Transporter (OCT2)", "severity": "minor",

        "mechanism": "Reduced renal clearance of metformin",

        "recommendation": "Monitor; consider dose adjust",

        "cl_multiplier": 0.8,

    },

]

def check_drug_interactions(

    new_drug_name: str,

    current_medicines: List[Medicine],

) -> Tuple[List[DrugInteraction], float]:

    """
    Returns (interactions, combined_cl_multiplier for the NEW drug).
    Multipliers multiply when several inhibitors apply (capped later).
    """

    results = []

    cl_mult = 1.0

    new_lower = new_drug_name.strip().lower()

    for med in current_medicines:

        med_lower = med.name.strip().lower()

        for rule in INTERACTION_RULES:

            a, b = rule["a"], rule["b"]

            hit = (a in new_lower and b in med_lower) or (b in new_lower and a in med_lower)

            if not hit:

                continue

            results.append(

                DrugInteraction(

                    interacting_drug=med.name,

                    interaction_type=rule["type"],

                    severity=rule["severity"],

                    mechanism=rule["mechanism"],

                    recommendation=rule["recommendation"],

                )

            )

                                                                                      

            m = float(rule.get("cl_multiplier", 1.0))

            if m != 1.0:

                                                                          

                if a in new_lower or b in new_lower:

                    cl_mult *= m

                          

    cl_mult = max(0.25, min(2.0, cl_mult))

    return results, cl_mult

def check_contraindications(

    new_drug_name: str,

    allergies: List[str],

    conditions: List[str],

    age: int,

    sex: str,

    egfr: float = 90.0,

) -> List[Contraindication]:

    findings = []

    drug_lower = new_drug_name.strip().lower()

    cond_lower = [c.lower() for c in conditions]

    for hit in allergy_hits(new_drug_name, allergies):

        findings.append(

            Contraindication(

                type="allergy",

                matched_item=hit["matched_item"],

                severity=hit["severity"],

                message=hit["message"],

            )

        )

    nsaid = any(x in drug_lower for x in ["ibuprofen", "naproxen", "diclofenac", "nsaid", "ketorolac", "celecoxib"])

    if nsaid:

        if any(k in cond_lower for k in ["kidney", "renal", "ckd"]) or egfr < 30:

            findings.append(

                Contraindication(

                    type="condition",

                    matched_item="kidney disease / low eGFR",

                    severity="contraindicated" if egfr < 30 else "warning",

                    message="NSAID with impaired renal function — avoid or shortest course",

                )

            )

        if any(k in cond_lower for k in ["heart failure", "chf", "heart disease"]):

            findings.append(

                Contraindication(

                    type="condition",

                    matched_item="heart disease / HF",

                    severity="warning",

                    message="NSAIDs may exacerbate heart failure (fluid retention)",

                )

            )

        if "pregnancy" in cond_lower or "pregnant" in cond_lower:

            findings.append(

                Contraindication(

                    type="pregnancy",

                    matched_item="pregnancy",

                    severity="contraindicated",

                    message="NSAIDs generally avoided in pregnancy (esp. 3rd trimester)",

                )

            )

    if "metformin" in drug_lower and (egfr < 30 or any(k in cond_lower for k in ["kidney", "renal", "ckd"])):

        findings.append(

            Contraindication(

                type="condition",

                matched_item="kidney disease",

                severity="contraindicated" if egfr < 30 else "warning",

                message="Metformin: contraindicated or dose-adjust if eGFR < 30–45",

            )

        )

    return findings

def organ_specific_flags(

    new_drug_name: str,

    patient_egfr: float,

    liver_score: float,

    qtc_ms: float | None,

    conditions: List[str],

) -> List[OrganFlag]:

    flags = []

    drug_lower = new_drug_name.strip().lower()

    if patient_egfr < 60 and any(

        x in drug_lower for x in ["ibuprofen", "nsaid", "metformin", "digoxin", "vancomycin", "gentamicin"]

    ):

        flags.append(

            OrganFlag(

                organ="kidney",

                risk_level="high" if patient_egfr < 30 else "moderate",

                reason=f"eGFR {patient_egfr} + drug with renal clearance / nephrotoxic potential",

            )

        )

    if liver_score < 0.7 and any(

        x in drug_lower for x in ["paracetamol", "acetaminophen", "atorvastatin", "amiodarone"]

    ):

        flags.append(

            OrganFlag(

                organ="liver",

                risk_level="high" if liver_score < 0.5 else "moderate",

                reason=f"Reduced hepatic capacity (score {liver_score})",

            )

        )

    if qtc_ms and qtc_ms > 450:

        if any(x in drug_lower for x in ["amiodarone", "sotalol", "ondansetron", "haloperidol"]):

            flags.append(

                OrganFlag(

                    organ="heart",

                    risk_level="high" if qtc_ms > 500 else "moderate",

                    reason=f"Baseline QTc {qtc_ms} ms + QT-prolonging drug",

                )

            )

    return flags

