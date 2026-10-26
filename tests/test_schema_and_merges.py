"""Schema and merge integrity: synthetic always; real source when present locally."""

import pandas as pd
from conftest import RAW_PHONE, requires_raw
from fixtures.synthetic import synthetic_sources

from hunger_screening import build_panels as bp
from hunger_screening.schema_audit import integrity_checks


def test_synthetic_panel_structure():
    phone, base = synthetic_sources()
    p = bp.assign_slots(bp.valid_hhs(phone))
    kept, _ = bp.deduplicate(p)
    m = bp.slot_matrix(kept, base, 2020, list(range(1, 7)))
    assert len(m) == len(base)
    assert m.index.is_unique
    assert set(m.index.get_level_values("country")) == {"Malawi", "Liberia"}
    b = bp.binarize(m, 2)
    cnt = bp.observed_counts(b)
    assert ((cnt.k + cnt.r) <= 6).all()
    assert (cnt.n_obs + cnt.r == 6).all()


@requires_raw
def test_real_source_integrity():
    phone = pd.read_stata(RAW_PHONE, convert_categoricals=False)
    base = pd.read_stata(RAW_PHONE.parent / "baseline_analysis_fullsample.dta", convert_categoricals=False)
    checks = integrity_checks(phone, base)
    failed = checks[~checks["pass"]]
    assert failed.empty, failed.to_string()


@requires_raw
def test_real_cohort_counts():
    phone, base = bp.load_sources(RAW_PHONE.parent, RAW_PHONE.name, "baseline_analysis_fullsample.dta")
    p = bp.assign_slots(bp.valid_hhs(phone))
    kept, info = bp.deduplicate(p)
    assert info.household_slots_with_multiple == 1
    assert info.binary_outcome_differs[2] == 0
    b = bp.binarize(bp.slot_matrix(kept, base, 2020, list(range(1, 7))), 2)
    for c, n_comp, n_pos in (("Malawi", 227, 185), ("Liberia", 67, 34)):
        k = bp.complete_k(b.xs(c, level="country"))
        assert len(k) == n_comp and int((k > 0).sum()) == n_pos
