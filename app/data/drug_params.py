"""
Drug-specific PK parameter table (MVP seed).

Values are approximate population means for adults; sources are indicative
(label / textbook / open literature). Always show provenance + confidence
in the report. Prefer "data unavailable" over inventing numbers.
"""

from typing import Any, Dict, Optional

        

                                                                         

                                              

                             

                                      

                                                  

                                        

                                                     

                                                          

                                          

                                  

                                   

DRUG_PARAMS: Dict[str, Dict[str, Any]] = {

    "ibuprofen": {

        "display_name": "Ibuprofen",

        "cl_l_h": 3.5,

        "vd_l_per_kg": 0.15,

        "F": 0.80,

        "ka": 1.5,

        "fe": 0.01,

        "fu": 0.01,

        "half_life_h": 2.0,

        "therapeutic_low": 10.0,

        "therapeutic_high": 50.0,

        "toxic_threshold": 100.0,

        "cyp": ["CYP2C9"],

        "protein_binding": 0.99,

        "source": "Approximate adult means; product monographs / clinical PK texts",

        "confidence": 0.7,

    },

    "paracetamol": {

        "display_name": "Paracetamol (Acetaminophen)",

        "cl_l_h": 20.0,

        "vd_l_per_kg": 0.95,

        "F": 0.88,

        "ka": 1.8,

        "fe": 0.05,

        "fu": 0.80,

        "half_life_h": 2.5,

        "therapeutic_low": 10.0,

        "therapeutic_high": 20.0,

        "toxic_threshold": 50.0,

        "cyp": ["CYP2E1"],

        "protein_binding": 0.20,

        "source": "Adult PK summaries; hepatotoxicity threshold illustrative",

        "confidence": 0.75,

    },

    "acetaminophen": {

        "display_name": "Acetaminophen (Paracetamol)",

        "cl_l_h": 20.0,

        "vd_l_per_kg": 0.95,

        "F": 0.88,

        "ka": 1.8,

        "fe": 0.05,

        "fu": 0.80,

        "half_life_h": 2.5,

        "therapeutic_low": 10.0,

        "therapeutic_high": 20.0,

        "toxic_threshold": 50.0,

        "cyp": ["CYP2E1"],

        "protein_binding": 0.20,

        "source": "Adult PK summaries; hepatotoxicity threshold illustrative",

        "confidence": 0.75,

    },

    "metformin": {

        "display_name": "Metformin",

        "cl_l_h": 30.0,

        "vd_l_per_kg": 1.1,

        "F": 0.55,

        "ka": 0.6,

        "fe": 0.90,

        "fu": 1.0,

        "half_life_h": 6.0,

        "therapeutic_low": 1.0,

        "therapeutic_high": 4.0,

        "toxic_threshold": 5.0,

        "cyp": [],

        "protein_binding": 0.0,

        "source": "Renally cleared; labels emphasize eGFR-based dosing",

        "confidence": 0.8,

    },

    "vancomycin": {

        "display_name": "Vancomycin",

        "cl_l_h": 5.5,

        "vd_l_per_kg": 0.7,

        "F": 0.0,                

        "ka": 0.0,

        "fe": 0.90,

        "fu": 0.45,

        "half_life_h": 6.0,

        "therapeutic_low": 10.0,

        "therapeutic_high": 20.0,

        "toxic_threshold": 30.0,

        "cyp": [],

        "protein_binding": 0.55,

        "source": "TDM literature; AUC/MIC guided in practice — simplified here",

        "confidence": 0.75,

    },

    "gentamicin": {

        "display_name": "Gentamicin",

        "cl_l_h": 4.5,

        "vd_l_per_kg": 0.25,

        "F": 0.0,

        "ka": 0.0,

        "fe": 0.90,

        "fu": 0.90,

        "half_life_h": 2.5,

        "therapeutic_low": 4.0,

        "therapeutic_high": 10.0,

        "toxic_threshold": 12.0,

        "cyp": [],

        "protein_binding": 0.10,

        "source": "Aminoglycoside TDM texts; peak/trough simplified to levels",

        "confidence": 0.7,

    },

    "digoxin": {

        "display_name": "Digoxin",

        "cl_l_h": 8.0,

        "vd_l_per_kg": 5.0,

        "F": 0.70,

        "ka": 0.8,

        "fe": 0.70,

        "fu": 0.75,

        "half_life_h": 36.0,

        "therapeutic_low": 0.5,

        "therapeutic_high": 2.0,

        "toxic_threshold": 2.5,

        "cyp": [],

        "protein_binding": 0.25,

        "source": "Classic narrow therapeutic index; renal + P-gp relevant",

        "confidence": 0.75,

    },

    "warfarin": {

        "display_name": "Warfarin",

        "cl_l_h": 0.2,

        "vd_l_per_kg": 0.14,

        "F": 0.95,

        "ka": 1.0,

        "fe": 0.0,

        "fu": 0.01,

        "half_life_h": 40.0,

        "therapeutic_low": None,              

        "therapeutic_high": None,

        "toxic_threshold": None,

        "cyp": ["CYP2C9", "CYP3A4", "CYP1A2"],

        "protein_binding": 0.99,

        "source": "INR-guided; concentration window not primary",

        "confidence": 0.65,

    },

    "amlodipine": {

        "display_name": "Amlodipine",

        "cl_l_h": 25.0,

        "vd_l_per_kg": 21.0,

        "F": 0.64,

        "ka": 0.5,

        "fe": 0.10,

        "fu": 0.07,

        "half_life_h": 40.0,

        "therapeutic_low": None,

        "therapeutic_high": None,

        "toxic_threshold": None,

        "cyp": ["CYP3A4"],

        "protein_binding": 0.93,

        "source": "Long t½ CCB; hepatic metabolism dominant",

        "confidence": 0.7,

    },

    "omeprazole": {

        "display_name": "Omeprazole",

        "cl_l_h": 30.0,

        "vd_l_per_kg": 0.3,

        "F": 0.40,

        "ka": 1.2,

        "fe": 0.0,

        "fu": 0.05,

        "half_life_h": 1.0,

        "therapeutic_low": None,

        "therapeutic_high": None,

        "toxic_threshold": None,

        "cyp": ["CYP2C19", "CYP3A4"],

        "protein_binding": 0.95,

        "source": "CYP2C19 dependent; short plasma t½",

        "confidence": 0.7,

    },

}

                                                            

DEFAULT_PARAMS: Dict[str, Any] = {

    "display_name": None,

    "cl_l_h": 12.0,

    "vd_l_per_kg": 0.8,

    "F": 0.75,

    "ka": 1.2,

    "fe": 0.30,

    "fu": 0.5,

    "half_life_h": 6.0,

    "therapeutic_low": None,

    "therapeutic_high": None,

    "toxic_threshold": None,

    "cyp": [],

    "protein_binding": 0.5,

    "source": "Generic default — drug not in knowledge base",

    "confidence": 0.25,

}

def normalize_drug_key(identifier: str) -> str:

    return identifier.strip().lower().replace("-", " ").replace("  ", " ")

def get_drug_params(identifier: str) -> Dict[str, Any]:

    key = normalize_drug_key(identifier)

           

    if key in DRUG_PARAMS:

        p = dict(DRUG_PARAMS[key])

        p["matched_key"] = key

        p["known"] = True

        return p

                      

    for k, v in DRUG_PARAMS.items():

        if k in key or key in k:

            p = dict(v)

            p["matched_key"] = k

            p["known"] = True

            return p

    p = dict(DEFAULT_PARAMS)

    p["matched_key"] = None

    p["known"] = False

    p["display_name"] = identifier

    return p

