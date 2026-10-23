"""Lightweight 2-compartment IV bolus for distribution-phase drugs."""

from typing import List, Tuple

import math

def two_comp_iv_concentrations(

    dose_mg: float,

    v1: float,

    k10: float,

    k12: float,

    k21: float,

    times: List[float],

) -> List[float]:

    """
    Standard 2-compartment IV bolus micro-constants.
    alpha/beta eigenvalues of the disposition matrix.
    """

    a = k10 + k12 + k21

    b = k10 * k21

    disc = max(a * a - 4 * b, 0)

    alpha = (a + math.sqrt(disc)) / 2

    beta = (a - math.sqrt(disc)) / 2

    if abs(alpha - beta) < 1e-9:

        return [max(0.0, (dose_mg / v1) * math.exp(-k10 * t)) for t in times]

    A = (dose_mg / v1) * (alpha - k21) / (alpha - beta)

    B = (dose_mg / v1) * (k21 - beta) / (alpha - beta)

    out = []

    for t in times:

        c = A * math.exp(-alpha * t) + B * math.exp(-beta * t)

        out.append(max(0.0, c))

    return out

def should_use_two_compartment(drug_key: str) -> bool:

    return drug_key in ("vancomycin", "digoxin", "gentamicin")

def micro_constants_from_params(cl: float, vd_ss: float) -> Tuple[float, float, float, float]:

    """Rough micro-constants from CL and Vss for MVP demo."""

    v1 = max(vd_ss * 0.35, 5.0)

    v2 = max(vd_ss - v1, 1.0)

    k10 = cl / v1

    k12 = 0.5

    k21 = k12 * v1 / v2

    return v1, k10, k12, k21

