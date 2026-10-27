"""Generic contrast bounds: exact equality with brute force and with the existing solvers."""

import zlib
from fractions import Fraction

import numpy as np
import pytest

from hunger_screening import history_bounds as hb
from hunger_screening.misclassification_bounds import label_error_bounds
from hunger_screening.missing_bounds import sharp_missing_bounds


def _random_instance(rng, n_hh, n, p_missing=0.3):
    h = (rng.random((n_hh, n)) < 0.4).astype(int)
    h[rng.random((n_hh, n)) < p_missing] = -1
    return h


CONTRASTS = [
    ("fixed_first", lambda n: hb.fixed_missed([0])),
    ("fixed_last", lambda n: hb.fixed_missed([n - 1])),
    ("random_1", lambda n: hb.random_missed(n, 1)),
    ("diff_first_vs_random", lambda n: hb.fixed_minus_random([0], n, 1)),
    ("diff_pair_vs_random2", lambda n: hb.fixed_minus_random([0, 1], n, 2)),
]


@pytest.mark.parametrize("name,make", CONTRASTS)
@pytest.mark.parametrize("budget", [0, 1, 2])
def test_equals_brute_force(name, make, budget):
    rng = np.random.default_rng(zlib.crc32(f"{name}-{budget}".encode()))
    for _ in range(12):
        n = int(rng.integers(2, 4))
        if "pair" in name and n < 2:
            continue
        h = _random_instance(rng, int(rng.integers(1, 5)), n)
        c = make(n)
        res = hb.contrast_bounds(h, c, budget)
        lo, hi = hb.brute_force_bounds(h, c, budget)
        assert res["lower"].value == lo
        assert res["upper"].value == hi
        if lo is not None:
            assert res["lower"].certificate_F == 0 and res["upper"].certificate_F == 0
            assert res["lower"].budget_used <= budget and res["upper"].budget_used <= budget


def test_random_contrast_matches_existing_missing_bounds():
    rng = np.random.default_rng(7)
    for _ in range(20):
        n = 4
        h = _random_instance(rng, 15, n)
        k = (h == 1).sum(axis=1)
        r = (h == -1).sum(axis=1)
        old = sharp_missing_bounds(k, r, n, 1)
        new = hb.contrast_bounds(h, hb.random_missed(n, 1), 0)
        assert new["lower"].value == old["lower"].value
        assert new["upper"].value == old["upper"].value


def test_random_contrast_matches_existing_label_error_solver():
    rng = np.random.default_rng(11)
    for _ in range(10):
        n = 4
        h = _random_instance(rng, 12, n)
        k = (h == 1).sum(axis=1)
        r = (h == -1).sum(axis=1)
        for B in (1, 3):
            old = label_error_bounds(k, r, n, 1, B)
            new = hb.contrast_bounds(h, hb.random_missed(n, 1), B)
            assert new["lower"].value == old["lower"].value
            assert new["upper"].value == old["upper"].value


def test_complete_data_bounds_collapse_to_point():
    h = np.array([[1, 0, 0], [0, 1, 1], [0, 0, 0], [1, 1, 0]])
    c = hb.fixed_minus_random([0], 3, 1)
    res = hb.contrast_bounds(h, c, 0)
    pt = hb.observed_value(h, c)
    assert res["lower"].value == res["upper"].value == pt
    # hand check: positives are rows 0,1,3 with K=1,2,2; fixed slot 0 misses row 1 only
    # fixed missed = 1/3; random missed = (2/3 + 1/3 + 1/3)/3 = 4/9; difference = -1/9
    assert pt == Fraction(1, 3) - Fraction(4, 9)


def test_bounds_nest_in_budget_and_tipping_point():
    rng = np.random.default_rng(3)
    h = _random_instance(rng, 30, 3, p_missing=0.1)
    h[:, 0] = np.where(h[:, 0] == -1, -1, 1)  # make the fixed slot look strong
    c = hb.fixed_minus_random([0], 3, 1)
    prev = None
    for B in range(0, 6):
        r = hb.contrast_bounds(h, c, B)
        if prev is not None:
            assert r["lower"].value <= prev["lower"].value
            assert r["upper"].value >= prev["upper"].value
        prev = r
    tb = hb.tipping_budget(h, c, "max", Fraction(0))
    assert tb is not None
    assert hb.contrast_bounds(h, c, tb)["upper"].value >= 0
    if tb > 0:
        assert hb.contrast_bounds(h, c, tb - 1)["upper"].value < 0


def test_no_positive_world_returns_none():
    h = np.array([[0, 0], [0, 0]])
    res = hb.contrast_bounds(h, hb.fixed_missed([0]), 0)
    assert res["lower"].value is None and res["upper"].value is None
