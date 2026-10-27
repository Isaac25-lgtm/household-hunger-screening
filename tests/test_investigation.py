"""Investigation modules: schedule metrics, bootstrap, selection/leakage, rules, outputs."""

from fractions import Fraction
from itertools import product

import numpy as np
import pandas as pd
import pytest
from conftest import ROOT

from hunger_screening import hfps
from hunger_screening import schedule_metrics as sm
from hunger_screening.combinatorics import p_miss_enumerated

INV = ROOT / "data" / "public_aggregates" / "investigation"
HFPS_RAW = ROOT / "data" / "raw" / "worldbank_mwi_hfps_v20" / "extracted" / "sect8_food_security_r7.dta"
requires_hfps = pytest.mark.skipif(not HFPS_RAW.exists(), reason="World Bank microdata not present (expected in CI)")
requires_outputs = pytest.mark.skipif(not (INV / "hfps_single_round.csv").exists(), reason="investigation outputs not generated")


# ---------------------------------------------------------------- schedule metrics
def test_random_terms_equal_enumeration():
    hist = np.array(list(product((0, 1), repeat=4)))
    for m in range(1, 5):
        miss, pos = sm.household_terms(hist, m=m)
        for row, mi, po in zip(hist, miss, pos):
            if row.sum() == 0:
                assert mi == 0 and po == 0
            else:
                assert abs(mi - float(p_miss_enumerated(list(row), m))) < 1e-12


def test_schedule_row_denominators():
    H = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 0], [1, 1, 1]])
    r = sm.schedule_row(H, [0], ["a", "b", "c"])
    assert r["n_reference_positive"] == 3 and r["n_missed"] == 1
    assert r["missed_share"] == pytest.approx(1 / 3)
    assert r["identified_per_100_households"] == pytest.approx(50.0)  # 2 identified of 4 households
    r2 = sm.schedule_row(H, [0, 1], ["a", "b", "c"])
    assert r2["identified_per_100_contacts"] == pytest.approx(100 * 3 / 8)


def test_cluster_bootstrap_resamples_whole_clusters_and_pairs():
    clusters = np.repeat([0, 1, 2], 4)
    num = np.tile([1, 0, 1, 0], 3).astype(float)  # every cluster has ratio 0.5
    den = np.ones(12)
    reps, zero = sm.ratio_bootstrap(clusters, {"a": (num, den), "b": (num, den)}, 200, 1)
    assert np.allclose(reps["a"], 0.5) and np.allclose(reps["a"] - reps["b"], 0) and zero["a"] == 0
    den2 = np.where(clusters == 0, 1.0, 0.0)
    reps2, zero2 = sm.ratio_bootstrap(clusters, {"a": (num * den2, den2)}, 500, 2)
    assert zero2["a"] == int(np.isnan(reps2["a"]).sum()) and zero2["a"] > 0


def test_select_candidate_tie_break_and_training_only():
    train = np.array([[1, 1, 0], [0, 1, 1], [1, 0, 1]])  # every column misses exactly one positive
    sel, miss = hfps.select_candidate(train, [2, 0, 1])
    assert miss == [pytest.approx(1 / 3)] * 3 and sel == 2  # earliest in the supplied date order


def _toy_hfps(test_flip: bool) -> hfps.HFPS:
    rng = np.random.default_rng(0)
    hh = [f"h{i}" for i in range(40)]
    rows = []
    for r, month in ((1, 6), (6, 12), (9, 4), (18, 6), (19, 12), (21, 4)):
        year = 2020 if r in (1, 6) else 2021 if r == 9 else 2023 if r in (18, 19) else 2024
        for h in hh:
            v = float(rng.random() < 0.5)
            if test_flip and r in (18, 19, 21):
                v = 1.0 - v
            rows.append({"hh": h, "round": r, "date": pd.Timestamp(year, month, 15), "s8q7": v, "weight": 1.0,
                         "sample_type": 2.0 if r in (19, 21) else np.nan})
    long = pd.DataFrame(rows)
    static = pd.DataFrame({"district": [i % 5 for i in range(40)], "region": 100, "urban": 0, "wealth_quintile": 1,
                           "sample_type": 2.0}, index=pd.Index(hh, name="hh"))
    return hfps.HFPS(long, static, pd.DataFrame(), {r: f"R{r}" for r in (1, 6, 9, 18, 19, 21)}, 0)


def test_transfer_selection_ignores_test_data():
    boot = {"draws": 50, "seed": 1, "level": 0.95}
    a, _ = hfps.transfer_test(_toy_hfps(False), "t", "s8q7", ["Jun", "Dec", "Apr"], [1, 6, 9], [18, 19, 21], boot, 2.0)
    b, _ = hfps.transfer_test(_toy_hfps(True), "t", "s8q7", ["Jun", "Dec", "Apr"], [1, 6, 9], [18, 19, 21], boot, 2.0)
    assert list(a.selected_on_train) == list(b.selected_on_train)
    assert list(a.train_missed) == list(b.train_missed)
    assert not np.allclose(a.test_missed, b.test_missed)


def test_second_contact_exact_expectations():
    first = np.array([0, 0, 0, 0, 1, 0])
    later = np.array([[1], [0], [1], [0], [1], [0]])
    warning = np.array([True, False, True, False, True, False])
    poverty = np.array([1, 1, 2, 3, 1, 3])
    out = hfps.second_contact(first, later, warning, poverty, np.arange(6), {"draws": 20, "seed": 1, "level": 0.95}, "t")
    o = out.set_index("rule").expected_captured
    # negatives: rows 0,1,2,3,5; budget = 2 warning-sign negatives (rows 0, 2), both later positive
    assert o.iloc[0] == 2
    assert o.iloc[1] == pytest.approx(2 * 2 / 5)       # random: base rate 2/5
    assert o.iloc[2] == pytest.approx(1.0)             # poorest rank 1 = rows 0,1 -> one later positive


def test_top_budget_expected_splits_ties():
    score = np.array([2.0, 1.0, 1.0, 1.0, 0.0])
    y = np.array([1.0, 1.0, 0.0, 0.0, 1.0])
    assert hfps._top_budget_expected(score, y, 2) == pytest.approx(1 + 1 / 3)


def test_hhs_analogue_scoring():
    long = pd.DataFrame({"hh": list("abcd"), "round": 20, "date": pd.Timestamp(2024, 3, 1),
                         "s8q6": [0, 1, 1, 1], "s8q6a": [np.nan, 1, 3, 2], "s8q7": [0, 1, 1, 0], "s8q7a": [np.nan, 2, 3, np.nan],
                         "s8q8": [0, 0, 1, 0], "s8q8a": [np.nan, np.nan, 3, np.nan]})
    h = hfps.HFPS(long, pd.DataFrame(), pd.DataFrame(), {20: "R20"}, 0)
    out = hfps.hhs_analogue(h, [20]).iloc[0]
    # scores: a=0, b=1+1=2, c=2+2+2=6, d=1 -> >=2 share 0.5, >=4 share 0.25
    assert out.hhs_analogue_ge2_share == 0.5 and out.hhs_analogue_ge4_share == 0.25
    assert out.share_of_s8q7_yes_with_analogue_ge2 == 1.0


# ---------------------------------------------------------------- published aggregates
@requires_outputs
def test_hfps_single_round_internal_consistency():
    s = pd.read_csv(INV / "hfps_single_round.csv")
    fixed = s[~s.schedule.str.startswith("random")]
    assert np.allclose(fixed.missed_share, fixed.n_missed / fixed.n_reference_positive)
    assert np.allclose(s.identified_per_100_households,
                       100 * (s.n_reference_positive - s.n_missed) / s.n_complete)
    assert (s.missed_ci_district_low <= s.missed_share + 1e-12).all()
    assert (s.missed_ci_district_high >= s.missed_share - 1e-12).all()


@requires_outputs
def test_robustness_bounds_contain_point_nest_and_certify():
    for f in ("hfps_decision_robustness.csv", "aggarwal_timing_robustness.csv"):
        r = pd.read_csv(INV / f)
        assert (r.lower <= r.complete_case_diff + 1e-12).all() and (r.upper >= r.complete_case_diff - 1e-12).all()
        assert (r.certificate_lower == 0).all() and (r.certificate_upper == 0).all()
        for _, g in r.groupby(["analysis"] + (["item"] if "item" in r else [])):
            g = g.sort_values("flip_budget")
            assert g.lower.is_monotonic_decreasing and g.upper.is_monotonic_increasing
        for v in r.lower_exact:
            Fraction(v)


@requires_outputs
def test_each_transfer_test_selects_exactly_one_candidate():
    t = pd.read_csv(INV / "hfps_transfer_tests.csv")
    assert (t.groupby(["test", "item"]).selected_on_train.sum() == 1).all()
    j = pd.read_csv(INV / "aggarwal_july_june_test.csv")
    assert j.selected_on_train.sum() == 1


# ---------------------------------------------------------------- real microdata
@requires_hfps
def test_real_hfps_audit_and_key_reproduction():
    cfg = hfps.load_investigation_config(hfps.Paths())["hfps"]
    h = hfps.load(cfg, ROOT)
    assert h.long.hh.nunique() == 1729 and len(h.long) == 20610 and h.unlinked_records == 0
    assert hfps.audit(h)["integrity"]["pass"].all()
    t = hfps.single_round_table(h, [7, 9, 11], "s8q7", {"draws": 20, "seed": 1, "level": 0.95})
    r7 = t.iloc[0]
    assert (r7.n_complete, r7.n_reference_positive, r7.n_missed) == (1443, 933, 223)
