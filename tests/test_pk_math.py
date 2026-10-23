"""Golden PK identities for CI."""

import math

from app.services.pk_engine import compute_metrics, one_compartment_iv_bolus

from app.utils.clearance import (

    fe_based_clearance_multiplier,

    cockcroft_gault,

    calculate_egfr_ckd_epi,

)

from app.data.drug_params import get_drug_params

def test_css_identity_oral():

                                                                  

    dose, F, cl, tau = 100.0, 1.0, 10.0, 12.0

    ke = cl / 50.0         

    m = compute_metrics(dose, ka=2.0, ke=ke, vd=50.0, F=F, tau=tau, route="oral")

    assert abs(m.auc - (F * dose / cl)) < 0.01

def test_double_cl_halves_auc():

    dose, F, vd, ka, tau = 100.0, 1.0, 50.0, 2.0, 12.0

    m1 = compute_metrics(dose, ka, ke=0.2, vd=vd, F=F, tau=tau, route="oral")

    m2 = compute_metrics(dose, ka, ke=0.4, vd=vd, F=F, tau=tau, route="oral")

    assert abs(m1.auc / m2.auc - 2.0) < 0.05

def test_accumulation_factor():

    ke, tau = 0.1, 12.0

    m = compute_metrics(100, 1.0, ke, 50.0, 1.0, tau, "iv")

    expected = 1.0 / (1.0 - math.exp(-ke * tau))

    assert abs(m.accumulation_factor - expected) < 0.01

def test_iv_bolus_monotonic_decline():

    c = one_compartment_iv_bolus(100, ke=0.2, vd=50, times=[0, 1, 2, 5, 10])

    assert c[0] >= c[1] >= c[-1]

def test_fe_split_renal_drug():

                                      

    assert abs(fe_based_clearance_multiplier(1.0, 0.5, 0.1) - 0.5) < 1e-6

                         

    assert abs(fe_based_clearance_multiplier(0.0, 0.5, 0.8) - 0.8) < 1e-6

def test_cockcroft_gault_male():

                                                        

    crcl = cockcroft_gault(40, "male", 70, 1.0)

    assert crcl is not None and 95 < crcl < 100

def test_metformin_in_kb():

    p = get_drug_params("Metformin")

    assert p["known"] is True

    assert p["fe"] >= 0.8

