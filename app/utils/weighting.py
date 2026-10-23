"""Ideal body weight and adjusted body weight for Vd scaling."""

from typing import Optional, Literal

def ideal_body_weight_kg(sex: str, height_cm: Optional[float]) -> Optional[float]:

    if not height_cm or height_cm < 100:

        return None

    height_in = height_cm / 2.54

                    

    if sex.lower() == "female":

        ibw = 45.5 + 2.3 * (height_in - 60)

    else:

        ibw = 50.0 + 2.3 * (height_in - 60)

    return round(max(ibw, 30.0), 1)

def adjusted_body_weight_kg(weight_kg: float, ibw: float) -> float:

    return round(ibw + 0.4 * (weight_kg - ibw), 1)

def dosing_weight_kg(

    sex: str,

    weight_kg: float,

    height_cm: Optional[float],

    vd_l_per_kg: float,

    mode: Literal["auto", "tbw", "ibw", "abw"] = "auto",

) -> dict:

    """
    Hydrophilic (low Vd) → prefer IBW/ABW when obese; lipophilic → TBW.
    """

    ibw = ideal_body_weight_kg(sex, height_cm)

    abw = adjusted_body_weight_kg(weight_kg, ibw) if ibw else None

    obese = ibw is not None and weight_kg > 1.2 * ibw

    if mode == "tbw":

        w, used = weight_kg, "total_body_weight"

    elif mode == "ibw" and ibw:

        w, used = ibw, "ideal_body_weight"

    elif mode == "abw" and abw:

        w, used = abw, "adjusted_body_weight"

    else:

                                               

        if obese and vd_l_per_kg < 0.5 and abw:

            w, used = abw, "adjusted_body_weight"

        elif obese and vd_l_per_kg < 1.0 and ibw:

            w, used = ibw, "ideal_body_weight"

        else:

            w, used = weight_kg, "total_body_weight"

    return {

        "dosing_weight_kg": round(w, 1),

        "weight_basis": used,

        "ibw_kg": ibw,

        "abw_kg": abw,

        "tbw_kg": weight_kg,

    }

