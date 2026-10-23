"""
1-compartment PK with drug-specific parameters + patient-adjusted clearance.
"""

from typing import List, Optional, Dict, Any

import math

from app.schemas.report import ConcentrationPoint, PKMetrics, PKResults

def _parse_frequency_to_tau(frequency: str) -> float:

    f = frequency.strip().upper()

    mapping = {

        "OD": 24.0, "QD": 24.0, "ONCE DAILY": 24.0,

        "BD": 12.0, "BID": 12.0, "TWICE DAILY": 12.0,

        "TDS": 8.0, "TID": 8.0, "THREE TIMES DAILY": 8.0,

        "QID": 6.0, "FOUR TIMES DAILY": 6.0,

        "Q6H": 6.0, "Q8H": 8.0, "Q12H": 12.0, "Q24H": 24.0,

    }

    if f in mapping:

        return mapping[f]

    if "EVERY" in f and "HOUR" in f:

        try:

            return float("".join(c for c in f if c.isdigit() or c == "."))

        except ValueError:

            pass

    return 12.0

def one_compartment_oral(dose_mg, ka, ke, vd, F=0.8, times=None):

    if times is None:

        times = [i * 0.5 for i in range(0, 49)]

    concs = []

    for t in times:

        if t == 0:

            concs.append(0.0)

            continue

        if abs(ka - ke) < 1e-6:

            c = (F * dose_mg / vd) * ka * t * math.exp(-ke * t)

        else:

            c = (F * dose_mg * ka) / (vd * (ka - ke)) * (

                math.exp(-ke * t) - math.exp(-ka * t)

            )

        concs.append(max(0.0, c))

    return concs

def one_compartment_iv_bolus(dose_mg, ke, vd, times=None):

    if times is None:

        times = [i * 0.5 for i in range(0, 49)]

    return [max(0.0, (dose_mg / vd) * math.exp(-ke * t)) for t in times]

def compute_metrics(dose_mg, ka, ke, vd, F, tau, route) -> PKMetrics:

    half_life = 0.693 / ke if ke > 0 else 999.0

    cl = ke * vd

    if route == "iv":

        cmax = dose_mg / vd

        tmax = 0.0

        auc = dose_mg / cl if cl > 0 else 0.0

    else:

        if abs(ka - ke) > 1e-6:

            tmax = math.log(ka / ke) / (ka - ke)

        else:

            tmax = 1.0 / ka if ka > 0 else 0.0

        if abs(ka - ke) > 1e-6:

            cmax = (F * dose_mg * ka) / (vd * (ka - ke)) * (

                math.exp(-ke * tmax) - math.exp(-ka * tmax)

            )

        else:

            cmax = (F * dose_mg / vd) * ka * tmax * math.exp(-ke * tmax)

        auc = (F * dose_mg) / cl if cl > 0 else 0.0

    accum = 1.0 / (1.0 - math.exp(-ke * tau)) if ke * tau > 0.01 else 1.0

    return PKMetrics(

        cmax=round(max(0.0, cmax), 3),

        tmax_h=round(tmax, 2),

        half_life_h=round(half_life, 2),

        auc=round(auc, 2),

        accumulation_factor=round(accum, 2),

        clearance_adjusted=round(cl, 3),

        vd_adjusted=round(vd, 2),

    )

def run_pk_simulation(

    dose_mg: float,

    route: str,

    frequency: str,

    duration_days: int,

    patient_cl_factor: float,

    patient_weight_kg: float,

    drug_params: Optional[Dict[str, Any]] = None,

) -> PKResults:

    """
    drug_params keys: cl_l_h, vd_l_per_kg, F, ka, therapeutic_*, toxic_threshold
    """

    dp = drug_params or {}

    typical_cl = float(dp.get("cl_l_h") or 12.0)

    vd_per_kg = float(dp.get("vd_l_per_kg") or 0.8)

    F = float(dp.get("F") if dp.get("F") is not None else 0.75)

    ka = float(dp.get("ka") or 1.2)

    if route == "iv":

        F = 1.0

    tau = _parse_frequency_to_tau(frequency)

    times = [round(i * 0.5, 2) for i in range(0, 49)]

                          

    vd_avg = vd_per_kg * 70.0

    cl_avg = typical_cl

    ke_avg = cl_avg / vd_avg if vd_avg > 0 else 0.1

                                               

    vd_pat = vd_per_kg * patient_weight_kg

    cl_pat = typical_cl * patient_cl_factor * (patient_weight_kg / 70.0)

    ke_pat = cl_pat / vd_pat if vd_pat > 0 else ke_avg

    if route == "iv":

        conc_avg = one_compartment_iv_bolus(dose_mg, ke_avg, vd_avg, times)

        conc_pat = one_compartment_iv_bolus(dose_mg, ke_pat, vd_pat, times)

    else:

        conc_avg = one_compartment_oral(dose_mg, ka, ke_avg, vd_avg, F, times)

        conc_pat = one_compartment_oral(dose_mg, ka, ke_pat, vd_pat, F, times)

    metrics_avg = compute_metrics(dose_mg, ka, ke_avg, vd_avg, F, tau, route)

    metrics_pat = compute_metrics(dose_mg, ka, ke_pat, vd_pat, F, tau, route)

    if metrics_pat.accumulation_factor > 3.0 or metrics_pat.half_life_h > 24:

        accum_risk = "high"

    elif metrics_pat.accumulation_factor > 1.8 or metrics_pat.half_life_h > 12:

        accum_risk = "moderate"

    else:

        accum_risk = "low"

    tw_low = dp.get("therapeutic_low")

    tw_high = dp.get("therapeutic_high")

    toxic = dp.get("toxic_threshold")

    return PKResults(

        average_person_curve=[

            ConcentrationPoint(time_h=t, concentration=round(c, 4))

            for t, c in zip(times, conc_avg)

        ],

        patient_curve=[

            ConcentrationPoint(time_h=t, concentration=round(c, 4))

            for t, c in zip(times, conc_pat)

        ],

        metrics_average=metrics_avg,

        metrics_patient=metrics_pat,

        therapeutic_window_low=tw_low,

        therapeutic_window_high=tw_high,

        toxic_threshold=toxic,

        accumulation_risk=accum_risk,

    )

def exposure_risk_level(

    cmax: float,

    therapeutic_low: Optional[float],

    therapeutic_high: Optional[float],

    toxic_threshold: Optional[float],

    accum_risk: str,

) -> str:

    """
    Map exposure to Safe / Caution / High Risk when window known.
    """

    if toxic_threshold is not None and cmax >= toxic_threshold:

        return "High Risk"

    if therapeutic_high is not None and cmax > therapeutic_high * 1.25:

        return "High Risk" if cmax > therapeutic_high * 1.5 else "Caution"

    if therapeutic_low is not None and cmax < therapeutic_low * 0.5:

        return "Caution"                         

    if accum_risk == "high":

        return "Caution"

    return "Safe"

