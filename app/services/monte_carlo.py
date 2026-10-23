"""Monte Carlo uncertainty bands on Cmax / AUC (CL and Vd CV)."""

from typing import Dict, Any, List

import math

import random

def sample_lognormal(mean: float, cv: float) -> float:

    """mean on natural scale, cv = sd/mean."""

    if mean <= 0:

        return mean

    sigma = math.sqrt(math.log(1 + cv * cv))

    mu = math.log(mean) - 0.5 * sigma * sigma

    return math.exp(random.gauss(mu, sigma))

def monte_carlo_bands(

    dose_mg: float,

    F: float,

    cl_mean: float,

    vd_mean: float,

    tau: float,

    route: str,

    n: int = 200,

    cv_cl: float = 0.30,

    cv_vd: float = 0.20,

    seed: int = 42,

) -> Dict[str, Any]:

    random.seed(seed)

    cmax_s: List[float] = []

    auc_s: List[float] = []

    for _ in range(n):

        cl = sample_lognormal(cl_mean, cv_cl)

        vd = sample_lognormal(vd_mean, cv_vd)

        ke = cl / vd if vd > 0 else 0.1

        if route == "iv":

            cmax = dose_mg / vd

            auc = dose_mg / cl if cl > 0 else 0

        else:

                                                                                 

            cmax = (F * dose_mg) / vd

            auc = (F * dose_mg) / cl if cl > 0 else 0

        cmax_s.append(cmax)

        auc_s.append(auc)

    cmax_s.sort()

    auc_s.sort()

    def pct(arr, p):

        if not arr:

            return None

        i = min(len(arr) - 1, max(0, int(p * (len(arr) - 1))))

        return round(arr[i], 3)

    return {

        "n_samples": n,

        "cmax_p5": pct(cmax_s, 0.05),

        "cmax_p50": pct(cmax_s, 0.50),

        "cmax_p95": pct(cmax_s, 0.95),

        "auc_p5": pct(auc_s, 0.05),

        "auc_p50": pct(auc_s, 0.50),

        "auc_p95": pct(auc_s, 0.95),

        "cv_cl": cv_cl,

        "cv_vd": cv_vd,

    }

