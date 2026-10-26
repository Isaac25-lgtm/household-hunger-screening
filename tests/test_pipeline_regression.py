"""Regression checks on committed public aggregates (run in CI) and on the real source (local)."""

import numpy as np
import pandas as pd
import pytest
from conftest import RAW_PHONE, requires_raw

from hunger_screening.estimands import frontier_from_distribution

PUB = None


@pytest.fixture(scope="module")
def pub(root):
    p = root / "data" / "public_aggregates"
    if not (p / "frontier.csv").exists():
        pytest.skip("public aggregates not generated")
    return p


def test_frontier_recomputable_from_public_k_distribution(pub):
    f = pd.read_csv(pub / "frontier.csv")
    kd = pd.read_csv(pub / "k_distribution.csv")
    for (c, t), g in kd.groupby(["country", "threshold"]):
        for m in range(1, 7):
            v = f[(f.country == c) & (f.threshold == t) & (f.m == m)]["missed_fraction"].item()
            assert np.isclose(frontier_from_distribution(g, 6, m), v)


def test_bootstrap_interval_contains_point(pub):
    f = pd.read_csv(pub / "frontier.csv")
    f = f[f.threshold == 2]
    assert ((f.ci_low <= f.missed_fraction + 1e-12) & (f.missed_fraction <= f.ci_high + 1e-12)).all()


def test_label_error_zero_equals_missing_bounds_and_nests(pub):
    mb = pd.read_csv(pub / "missing_bounds.csv")
    le = pd.read_csv(pub / "label_error_bounds.csv")
    fr = le[le.scope == "frame_missing_arbitrary"]
    z = fr[fr.alpha == 0].merge(mb, on=["country", "m"], suffixes=("_le", "_mb"))
    assert (z.lower_exact_le == z.lower_exact_mb).all() and (z.upper_exact_le == z.upper_exact_mb).all()
    for (_c, _s, _m), g in le.groupby(["country", "scope", "m"]):
        g = g.sort_values("alpha")
        assert (np.diff(g.lower) <= 1e-12).all() and (np.diff(g.upper) >= -1e-12).all()
    assert (le.lower_certificate_F == 0).all() and (le.upper_certificate_F == 0).all()
    assert (le.lower_budget_used <= le.budget_flips).all() and (le.upper_budget_used <= le.budget_flips).all()


def test_complete_only_zero_budget_equals_point(pub):
    le = pd.read_csv(pub / "label_error_bounds.csv")
    f = pd.read_csv(pub / "frontier.csv")
    z = le[(le.scope == "complete_histories_only") & (le.alpha == 0)].merge(
        f[f.threshold == 2], on=["country", "m"])
    assert np.allclose(z.lower, z.missed_fraction) and np.allclose(z.upper, z.missed_fraction)


def test_reproduction_table_all_pass(pub):
    r = pd.read_csv(pub / "reproduction_comparison.csv")
    assert r["pass_with_tolerance"].all(), r[~r.pass_with_tolerance].to_string()


@requires_raw
def test_real_frontier_matches_public(pub):
    from hunger_screening import build_panels as bp
    from hunger_screening.combinatorics import missed_fraction

    phone, base = bp.load_sources(RAW_PHONE.parent, RAW_PHONE.name, "baseline_analysis_fullsample.dta")
    kept, _ = bp.deduplicate(bp.assign_slots(bp.valid_hhs(phone)))
    b = bp.binarize(bp.slot_matrix(kept, base, 2020, list(range(1, 7))), 2)
    f = pd.read_csv(pub / "frontier.csv")
    for c in ("Malawi", "Liberia"):
        k = bp.complete_k(b.xs(c, level="country")).to_numpy()
        for m in (1, 2, 3):
            v = f[(f.country == c) & (f.threshold == 2) & (f.m == m)]["missed_fraction"].item()
            assert np.isclose(float(missed_fraction(k, 6, m)), v)
