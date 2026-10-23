"""Resolve active dose from composition table vs stated regimen dose."""

from typing import List, Optional, Dict, Any

import re

def parse_strength(strength: str, unit: str) -> Optional[float]:

    if strength is None or strength == "":

        return None

    try:

        val = float(str(strength).replace(",", "").strip())

    except ValueError:

        m = re.search(r"(\d+(?:\.\d+)?)", str(strength))

        if not m:

            return None

        val = float(m.group(1))

    u = (unit or "mg").lower().strip()

    if u in ("g", "gram", "grams"):

        val *= 1000.0

    elif u in ("mcg", "µg", "ug"):

        val /= 1000.0

    return val      

def resolve_active_dose(

    drug_identifier: str,

    stated_dose_mg: float,

    composition_rows: Optional[List[Dict[str, Any]]] = None,

    composition_text: Optional[str] = None,

) -> dict:

    """
    Prefer composition row whose name matches the drug identifier.
    Returns effective_dose_mg and mismatch warning if any.
    """

    rows = composition_rows or []

    name_l = drug_identifier.strip().lower()

    active_mg = None

    matched_row = None

    for r in rows:

        n = (r.get("name") or "").strip().lower()

        if not n:

            continue

        if n in name_l or name_l in n or name_l.split()[0] in n:

            mg = parse_strength(str(r.get("strength") or ""), str(r.get("unit") or "mg"))

            if mg is not None:

                active_mg = mg

                matched_row = r

                break

                                       

    if active_mg is None:

        for r in rows:

            mg = parse_strength(str(r.get("strength") or ""), str(r.get("unit") or "mg"))

            if mg is not None and (r.get("name") or "").strip():

                active_mg = mg

                matched_row = r

                break

    warnings = []

    effective = stated_dose_mg

    if active_mg is not None:

        if abs(active_mg - stated_dose_mg) / max(stated_dose_mg, 1e-6) > 0.15:

            warnings.append(

                f"Composition active strength ({active_mg} mg) differs from stated dose "

                f"({stated_dose_mg} mg) by >15%. Using stated regimen dose for PK; review input."

            )

        else:

            effective = active_mg

            warnings.append(

                f"Active dose taken from composition: {active_mg} mg "

                f"({(matched_row or {}).get('name', 'ingredient')})."

            )

    elif composition_text:

        warnings.append("Composition text recorded but no parseable active strength; using stated dose.")

    return {

        "effective_dose_mg": effective,

        "composition_active_mg": active_mg,

        "warnings": warnings,

        "matched_row": matched_row,

    }

