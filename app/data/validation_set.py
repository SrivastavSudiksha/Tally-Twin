"""
Literature-style reference points for credibility checks (illustrative adult means).
Predicted values should ideally fall within ~2-fold of these anchors.
"""

VALIDATION_CASES = [

    {

        "drug": "metformin",

        "dose_mg": 500,

        "route": "oral",

        "weight_kg": 70,

        "published_auc_note": "~4–8 mg·h/L order (highly variable)",

        "auc_low": 2.0,

        "auc_high": 20.0,

        "source": "Illustrative adult oral metformin exposure range",

    },

    {

        "drug": "ibuprofen",

        "dose_mg": 400,

        "route": "oral",

        "weight_kg": 70,

        "published_auc_note": "tens of mg·h/L typical after 400 mg",

        "auc_low": 50.0,

        "auc_high": 250.0,

        "source": "Illustrative ibuprofen 400 mg oral",

    },

    {

        "drug": "digoxin",

        "dose_mg": 0.25,

        "route": "oral",

        "weight_kg": 70,

        "published_auc_note": "narrow TI; ug-level concentrations",

        "auc_low": 5.0,

        "auc_high": 40.0,

        "source": "Illustrative digoxin exposure band",

    },

    {

        "drug": "vancomycin",

        "dose_mg": 1000,

        "route": "iv",

        "weight_kg": 70,

        "published_auc_note": "AUC-guided dosing common",

        "auc_low": 200.0,

        "auc_high": 800.0,

        "source": "Illustrative vancomycin AUC24 band (simplified)",

    },

]

