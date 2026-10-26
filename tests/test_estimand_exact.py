"""Exact miss probabilities and the ratio estimand versus explicit subset enumeration."""

from fractions import Fraction
from itertools import combinations, product

import numpy as np
import pytest

from hunger_screening.combinatorics import missed_fraction, p_miss, p_miss_enumerated, p_miss_vector
from hunger_screening.estimands import frontier, frontier_from_distribution, k_distribution


@pytest.mark.parametrize("n", range(1, 8))
def test_formula_matches_enumeration_for_every_history(n):
    for hist in product((0, 1), repeat=n):
        k = sum(hist)
        for m in range(0, n + 1):
            assert p_miss(k, n, m) == p_miss_enumerated(hist, m)


def test_edge_cases():
    assert p_miss(0, 6, 1) == 1          # nothing positive: always missed
    assert p_miss(6, 6, 1) == 0          # all positive: never missed
    assert p_miss(1, 6, 6) == 0          # keeping every slot detects any positive
    assert p_miss(5, 6, 2) == 0          # m > n - k: every subset contains a positive
    assert p_miss(1, 6, 1) == Fraction(5, 6)
    assert p_miss(2, 6, 3) == Fraction(1, 5)
    with pytest.raises(ValueError):
        p_miss(7, 6, 1)
    with pytest.raises(ValueError):
        p_miss(1, 6, 7)


def test_reference_negative_households_excluded():
    assert missed_fraction([0, 0, 0], 6, 1) is None
    a = missed_fraction([0, 0, 1, 3], 6, 1)
    b = missed_fraction([1, 3], 6, 1)
    assert a == b == (Fraction(5, 6) + Fraction(3, 6)) / 2


def test_synthetic_panel_against_direct_subset_enumeration():
    rng = np.random.default_rng(3)
    hist = rng.integers(0, 2, size=(40, 6))
    k = hist.sum(axis=1)
    for m in range(1, 7):
        num, den = Fraction(0), 0
        for h in hist:
            if h.sum() == 0:
                continue
            subs = list(combinations(range(6), m))
            num += Fraction(sum(1 for s in subs if h[list(s)].sum() == 0), len(subs))
            den += 1
        assert missed_fraction(k, 6, m) == num / den


def test_vector_and_frontier_consistency():
    k = np.array([0, 1, 2, 3, 6, 1, 0, 4])
    f = frontier(k, 6, range(1, 7))
    assert f.loc[f.m == 6, "missed_fraction"].item() == 0
    assert (np.diff(f["missed_fraction"]) <= 0).all()           # more screens never miss more
    for m in range(1, 7):
        pos = k[k > 0]
        assert np.isclose(p_miss_vector(pos, 6, m).mean(), f.loc[f.m == m, "missed_fraction"].item())
        assert np.isclose(frontier_from_distribution(k_distribution(k, 6), 6, m),
                          f.loc[f.m == m, "missed_fraction"].item())
    assert f["n_reference_positive"].iloc[0] == 6
