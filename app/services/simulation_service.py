"""
Orchestrates full simulation: drug params, fe-clearance, DDI×CL, exposure risk.
"""

from app.schemas.patient import PatientInput, PatientProfileSnapshot

from app.schemas.drug import DrugInput, DrugProfile, MolecularProperties

from app.schemas.report import (

    SimulationReport,

    DoseAssessment,

    Explainability,

    ConfidenceAndQuality,

)

from app.utils.clearance import derive_patient_pk_params

from app.utils.rdkit_utils import extract_molecular_properties, get_basic_drug_knowledge

from app.data.drug_params import get_drug_params

from app.services.pk_engine import run_pk_simulation, exposure_risk_level

from app.services.interaction_engine import (

    check_drug_interactions,

    check_contraindications,

    organ_specific_flags,

)

from app.services.adverse_effect import predict_adverse_effects

from app.utils.composition_dose import resolve_active_dose

from app.utils.weighting import dosing_weight_kg

from app.services.monte_carlo import monte_carlo_bands

from app.core.constants import APP_MODEL_VERSION, KNOWLEDGE_BASE_VERSION, DISCLAIMER, RULES_VERSION

from app.data.safety_rules import CHECKED_DDI_LABELS

def _build_patient_snapshot(patient: PatientInput, derived: dict) -> PatientProfileSnapshot:

    return PatientProfileSnapshot(

        age=patient.age,

        sex=patient.sex.value,

        weight_kg=patient.weight_kg,

        height_cm=patient.height_cm,

        bmi=derived["bmi"],

        serum_creatinine=patient.serum_creatinine,

        egfr=derived["egfr"],

        egfr_category=derived["egfr_category"],

        alt=patient.alt,

        ast=patient.ast,

        liver_capacity_score=derived["liver_capacity_score"],

        conditions=patient.conditions,

        current_medicines=patient.current_medicines,

        allergies=patient.allergies,

        smoking=patient.smoking,

        alcohol=patient.alcohol,

        clearance_adjustment_factor=derived["clearance_adjustment_factor"],

    )

def _assess_dose(patient_cl_factor: float, accum_risk: str, metrics_patient, exposure_risk: str) -> DoseAssessment:

    if exposure_risk == "High Risk" or patient_cl_factor < 0.55 or accum_risk == "high":

        assessment = "too_high"

        suggestion = "Consider 25–50% dose reduction or longer interval (indicative only)"

        rationale = (

            f"Clearance factor {patient_cl_factor:.2f}; accumulation={accum_risk}; "

            f"exposure risk={exposure_risk}; t½={metrics_patient.half_life_h} h"

        )

    elif patient_cl_factor > 1.15 or exposure_risk == "Caution" and metrics_patient.cmax:

                                                                                  

        if patient_cl_factor > 1.15:

            assessment = "too_low"

            suggestion = "Standard dose may be sub-therapeutic if clinically indicated"

            rationale = f"Higher than typical clearance (factor {patient_cl_factor:.2f})"

        else:

            assessment = "appropriate"

            suggestion = "No strong PK adjustment from clearance alone — review window"

            rationale = f"Clearance factor {patient_cl_factor:.2f}; exposure risk={exposure_risk}"

    else:

        assessment = "appropriate"

        suggestion = "No strong adjustment indicated from PK perspective"

        rationale = f"Clearance factor {patient_cl_factor:.2f} within expected range"

    return DoseAssessment(

        standard_dose_assessment=assessment,

        suggested_adjustment_range=suggestion,

        rationale=rationale,

    )

def _build_explainability(derived: dict, patient: PatientInput, drug_params: dict) -> Explainability:

    impacts = []

    if derived["egfr"] < 60:

        impacts.append({"param": "eGFR / kidney function", "impact": round(1 - derived["egfr"] / 90, 2)})

    if derived.get("crcl_ml_min") and derived["crcl_ml_min"] < 60:

        impacts.append({"param": "Cockcroft-Gault CrCl", "impact": 0.2})

    if derived["liver_capacity_score"] < 0.85:

        impacts.append({"param": "Liver capacity / Child-Pugh", "impact": round(1 - derived["liver_capacity_score"], 2)})

    if derived.get("ddi_cl_multiplier", 1.0) != 1.0:

        impacts.append({"param": "DDI clearance multiplier", "impact": round(abs(1 - derived["ddi_cl_multiplier"]), 2)})

    if patient.age >= 65:

        impacts.append({"param": "Age", "impact": 0.15 if patient.age < 75 else 0.25})

    if patient.weight_kg < 50 or patient.weight_kg > 100:

        impacts.append({"param": "Body weight", "impact": 0.12})

    if not drug_params.get("known"):

        impacts.append({"param": "Unknown drug parameters (defaults)", "impact": 0.3})

    impacts.sort(key=lambda x: x["impact"], reverse=True)

    top = impacts[:5] if impacts else [{"param": "None dominant", "impact": 0.0}]

    summary = (

        f"Primary drivers: {', '.join(p['param'] for p in top)}. "

        f"CL multiplier={derived['clearance_adjustment_factor']:.2f} "

        f"(fe={derived.get('fe_used', '?')}, DDI×CL={derived.get('ddi_cl_multiplier', 1):.2f})."

    )

    return Explainability(

        top_patient_parameters=top,

        structural_toxicity_notes=[],

        key_drivers_summary=summary,

    )

def _merge_risk(*levels: str) -> str:

    order = {"Safe": 0, "Caution": 1, "High Risk": 2}

    best = max(levels, key=lambda x: order.get(x, 0))

    return best

def run_full_simulation(patient: PatientInput, drug: DrugInput) -> SimulationReport:

    drug_params = get_drug_params(drug.identifier)

    fe = float(drug_params.get("fe") or 0.3)

    dose_info = resolve_active_dose(

        drug.identifier,

        drug.dose_mg,

        composition_rows=getattr(drug, "composition_rows", None),

        composition_text=getattr(drug, "composition", None),

    )

    effective_dose = dose_info["effective_dose_mg"]

    wt = dosing_weight_kg(

        patient.sex.value,

        patient.weight_kg,

        patient.height_cm,

        float(drug_params.get("vd_l_per_kg") or 0.8),

    )

                                    

    interactions, ddi_cl_mult = check_drug_interactions(drug.identifier, patient.current_medicines)

    inr = getattr(patient, "inr", None)

    derived = derive_patient_pk_params(

        age=patient.age,

        sex=patient.sex.value,

        weight_kg=patient.weight_kg,

        height_cm=patient.height_cm,

        serum_creatinine=patient.serum_creatinine,

        egfr_provided=patient.egfr,

        alt=patient.alt,

        ast=patient.ast,

        bilirubin=patient.bilirubin,

        albumin=patient.albumin,

        inr=inr,

        smoking=patient.smoking,

        alcohol=patient.alcohol,

        conditions=patient.conditions,

        fe=fe,

        ddi_cl_multiplier=ddi_cl_mult,

    )

    patient_snap = _build_patient_snapshot(patient, derived)

    mol_props = extract_molecular_properties(drug.identifier)

    knowledge = get_basic_drug_knowledge(drug.identifier)

                                            

    cyps = drug_params.get("cyp") or knowledge.get("cyp_enzymes", [])

    composition_note = getattr(drug, "composition", None)

    drug_profile = DrugProfile(

        name=drug_params.get("display_name") or drug.identifier,

        identifier_used=drug.identifier,

        molecular_properties=MolecularProperties(**mol_props),

        known_targets=knowledge.get("targets", []),

        metabolism_pathways=knowledge.get("metabolism", [])

        + ([f"fe={fe}", f"fu={drug_params.get('fu')}"] if drug_params.get("known") else ["parameters: default"]),

        cyp_enzymes=list(cyps),

        therapeutic_window_note=(

            None

            if drug_params.get("therapeutic_low") is None

            else f"{drug_params.get('therapeutic_low')}–{drug_params.get('therapeutic_high')} mg/L"

        ),

    )

    pk_results = run_pk_simulation(

        dose_mg=effective_dose,

        route=drug.route,

        frequency=drug.frequency,

        duration_days=drug.duration_days,

        patient_cl_factor=derived["clearance_adjustment_factor"],

        patient_weight_kg=wt["dosing_weight_kg"],

        drug_params=drug_params,

    )

                                                     

    if pk_results.therapeutic_window_low is None:

        pk_results.therapeutic_window_low = drug_params.get("therapeutic_low")

        pk_results.therapeutic_window_high = drug_params.get("therapeutic_high")

        pk_results.toxic_threshold = drug_params.get("toxic_threshold")

    exp_risk = exposure_risk_level(

        pk_results.metrics_patient.cmax,

        pk_results.therapeutic_window_low,

        pk_results.therapeutic_window_high,

        pk_results.toxic_threshold,

        pk_results.accumulation_risk,

    )

    dose_assessment = _assess_dose(

        derived["clearance_adjustment_factor"],

        pk_results.accumulation_risk,

        pk_results.metrics_patient,

        exp_risk,

    )

    adverse = predict_adverse_effects(

        drug.identifier,

        derived["egfr"],

        derived["liver_capacity_score"],

        patient.age,

        patient.conditions,

    )

    organ_flags = organ_specific_flags(

        drug.identifier,

        derived["egfr"],

        derived["liver_capacity_score"],

        patient.qtc_ms,

        patient.conditions,

    )

    contras = check_contraindications(

        drug.identifier,

        patient.allergies,

        patient.conditions,

        patient.age,

        patient.sex.value,

        egfr=derived["egfr"],

    )

    explain = _build_explainability(derived, patient, drug_params)

    novel = not drug_params.get("known")

    conf_score = float(drug_params.get("confidence") or 0.3)

    if patient.serum_creatinine is None and patient.egfr is None:

        conf_score -= 0.10

    if patient.alt is None and patient.ast is None:

        conf_score -= 0.05

    if ddi_cl_mult != 1.0:

        conf_score = min(conf_score + 0.05, 0.95)

    conf_score = max(0.15, min(0.95, conf_score))

    if conf_score >= 0.7:

        overall_conf = "High"

    elif conf_score >= 0.45:

        overall_conf = "Medium"

    else:

        overall_conf = "Low"

    warnings = []

    if novel:

        warnings.append(

            "Drug not in parameter table — using generic defaults (low confidence). "

            f"Source: {drug_params.get('source')}"

        )

    else:

        warnings.append(

            f"Parameters: {drug_params.get('source')} (confidence {drug_params.get('confidence')})"

        )

    if patient.serum_creatinine is None and patient.egfr is None:

        warnings.append("Kidney function not provided — assumed normal eGFR")

    for w in dose_info.get("warnings") or []:

        warnings.append(w)

    warnings.append(f"Dosing weight: {wt['dosing_weight_kg']} kg ({wt['weight_basis']})")

    warnings.append(f"Model {APP_MODEL_VERSION} | KB {KNOWLEDGE_BASE_VERSION} | Rules {RULES_VERSION}")

    warnings.append(DISCLAIMER)

    if composition_note:

        warnings.append(f"Composition recorded: {composition_note[:200]}")

                       

    try:

        mc = monte_carlo_bands(

            dose_mg=effective_dose,

            F=float(drug_params.get("F") or 0.75),

            cl_mean=max(pk_results.metrics_patient.clearance_adjusted, 0.01),

            vd_mean=max(pk_results.metrics_patient.vd_adjusted, 0.01),

            tau=12.0,

            route=drug.route,

        )

        warnings.append(

            f"Uncertainty (MC): Cmax p5–p95 = {mc['cmax_p5']}–{mc['cmax_p95']}; "

            f"AUC p5–p95 = {mc['auc_p5']}–{mc['auc_p95']}"

        )

    except Exception:

        mc = None

    not_assessed = [

        f"DDI pairs not in rules base remain Not assessed. Checked families: {', '.join(CHECKED_DDI_LABELS[:6])}…"

    ]

    warnings.extend(not_assessed)

                                         

    safety_risk = "Safe"

    if any(c.severity == "contraindicated" for c in contras):

        safety_risk = "High Risk"

    elif any(i.severity == "major" for i in interactions) or any(f.risk_level == "high" for f in organ_flags):

        safety_risk = "High Risk"

    elif any(i.severity == "moderate" for i in interactions) or any(f.risk_level == "moderate" for f in organ_flags):

        safety_risk = "Caution"

    if dose_assessment.standard_dose_assessment == "too_high" and safety_risk == "Safe":

        safety_risk = "Caution"

    risk = _merge_risk(exp_risk, safety_risk)

    confidence = ConfidenceAndQuality(

        overall_confidence=overall_conf,

        per_prediction_scores={

            "pk": round(conf_score, 2),

            "ddi": 0.8 if interactions else 0.65,

            "adverse": 0.65,

            "contraindication": 0.85,

            "drug_params": float(drug_params.get("confidence") or 0.25),

        },

        data_quality_warnings=warnings,

        novel_compound_flag=novel,

    )

    summary_text = (

        f"Risk: {risk} (exposure={exp_risk}, safety={safety_risk}). "

        f"CL factor {derived['clearance_adjustment_factor']:.2f} "

        f"(CrCl={derived.get('crcl_ml_min')}, fe={fe}, DDI×CL={ddi_cl_mult:.2f}). "

        f"{dose_assessment.suggested_adjustment_range}"

    )

    return SimulationReport(

        risk_level=risk,

        overall_confidence=overall_conf,

        summary_text=summary_text,

        patient_profile=patient_snap,

        drug_profile=drug_profile,

        pharmacokinetic_results=pk_results,

        dose_assessment=dose_assessment,

        drug_drug_interactions=interactions,

        adverse_effects=adverse,

        organ_flags=organ_flags,

        contraindications=contras,

        explainability=explain,

        confidence_and_quality=confidence,

    )

