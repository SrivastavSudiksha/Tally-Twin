from app.data.validation_set import VALIDATION_CASES

from app.data.drug_params import get_drug_params

from app.services.pk_engine import run_pk_simulation

def test_validation_cases_run():

    for case in VALIDATION_CASES:

        params = get_drug_params(case["drug"])

        r = run_pk_simulation(

            dose_mg=case["dose_mg"],

            route=case["route"],

            frequency="OD",

            duration_days=1,

            patient_cl_factor=1.0,

            patient_weight_kg=case["weight_kg"],

            drug_params=params,

        )

        auc = r.metrics_patient.auc

                                                    

        assert auc > 0

