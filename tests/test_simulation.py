"""Basic smoke tests for the simulation pipeline."""

from app.schemas.patient import PatientInput, Medicine, Sex

from app.schemas.drug import DrugInput

from app.services.simulation_service import run_full_simulation

def test_ibuprofen_simulation():

    patient = PatientInput(

        age=58,

        sex=Sex.male,

        weight_kg=82,

        height_cm=175,

        serum_creatinine=1.4,

        alt=45,

        ast=38,

        conditions=["hypertension", "diabetes"],

        current_medicines=[

            Medicine(name="Metformin", dose_mg=500, frequency="BD"),

            Medicine(name="Amlodipine", dose_mg=5, frequency="OD"),

        ],

        allergies=[],

        smoking=False,

        alcohol="occasional",

    )

    drug = DrugInput(

        identifier="Ibuprofen",

        dose_mg=400,

        route="oral",

        frequency="TDS",

        duration_days=5,

    )

    report = run_full_simulation(patient, drug)

    assert report.risk_level in ("Safe", "Caution", "High Risk")

    assert report.overall_confidence in ("Low", "Medium", "High")

    assert report.patient_profile.egfr is not None

    assert report.patient_profile.clearance_adjustment_factor > 0

    assert report.pharmacokinetic_results.metrics_patient.cmax > 0

    assert len(report.adverse_effects) <= 5

    print("All assertions passed")

if __name__ == "__main__":

    test_ibuprofen_simulation()

