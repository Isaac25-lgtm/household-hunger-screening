"""Shared-budget label-error bounds versus slot-level brute force; identity and nesting."""

from fractions import Fraction
from itertools import combinations, product

import numpy as np
import pytest

from hunger_screening.misclassification_bounds import flip_cost, label_error_bounds
from hunger_screening.missing_bounds import sharp_missing_bounds


def _miss_share(h, m):
    subs = list(combinations(range(len(h)), m))
    return Fraction(sum(1 for s in subs if not any(h[i] for i in s)), len(subs))


def brute_force(obs, m, budget):
    """Every corrected history: any value for missing slots, observed slots may flip at
    a cost of 1 each; the total cost across households must be <= budget."""
    n = len(obs[0])
    options = []
    for h in obs:
        opts = []
        for c in product((0, 1), repeat=n):
            cost = sum(1 for x, y in zip(h, c) if x is not None and x != y)
            opts.append((c, cost))
        options.append(opts)
    lo = hi = None
    for world in product(*options):
        if sum(c for _, c in world) > budget:
            continue
        pos = [h for h, _ in world if any(h)]
        if not pos:
            continue
        r = sum(_miss_share(h, m) for h in pos) / len(pos)
        lo = r if lo is None or r < lo else lo
        hi = r if hi is None or r > hi else hi
    return lo, hi


def kr(obs):
    k = np.array([sum(x for x in h if x is not None) for h in obs])
    r = np.array([sum(1 for x in h if x is None) for h in obs])
    return k, r


@pytest.mark.parametrize("seed", range(25))
def test_matches_brute_force(seed):
    rng = np.random.default_rng(100 + seed)
    n = 3
    n_hh = int(rng.integers(2, 4))
    obs = [tuple(None if rng.uniform() < 0.25 else int(rng.uniform() < 0.4) for _ in range(n))
           for _ in range(n_hh)]
    k, r = kr(obs)
    for budget in (0, 1, 2, 3):
        for m in (1, 2):
            res = label_error_bounds(k, r, n, m, budget)
            lo, hi = brute_force(obs, m, budget)
            assert res["lower"].value == lo, (obs, m, budget)
            assert res["upper"].value == hi, (obs, m, budget)
            assert res["lower"].budget_used <= budget and res["upper"].budget_used <= budget
            assert res["lower"].certificate_F == 0 and res["upper"].certificate_F == 0


def test_flip_cost_is_minimum_hamming_distance():
    n = 4
    for obs in product((0, 1, None), repeat=n):
        k = sum(x for x in obs if x is not None)
        r = sum(1 for x in obs if x is None)
        best = {}
        for c in product((0, 1), repeat=n):
            cost = sum(1 for x, y in zip(obs, c) if x is not None and x != y)
            K = sum(c)
            best[K] = min(best.get(K, 99), cost)
        for K in range(n + 1):
            assert flip_cost(k, r, K) == best[K]


@pytest.mark.parametrize("seed", range(10))
def test_zero_budget_identity_and_nesting(seed):
    rng = np.random.default_rng(seed)
    n = 6
    N = 60
    r = rng.integers(0, 3, size=N)
    k = np.array([rng.integers(0, n - ri + 1) for ri in r])
    for m in (1, 2, 3):
        sb = sharp_missing_bounds(k, r, n, m)
        prev_lo, prev_hi = None, None
        for budget in (0, 2, 5, 10, 25):
            le = label_error_bounds(k, r, n, m, budget)
            if budget == 0:
                assert le["lower"].value == sb["lower"].value
                assert le["upper"].value == sb["upper"].value
            if prev_lo is not None:
                assert le["lower"].value <= prev_lo and le["upper"].value >= prev_hi
            prev_lo, prev_hi = le["lower"].value, le["upper"].value


def test_shared_budget_is_not_per_household():
    # two households, each one flip away from K=0; budget 1 cannot zero both.
    k = np.array([1, 1])
    r = np.array([0, 0])
    res = label_error_bounds(k, r, 3, 1, 1)
    assert not res["zero_positive_world_feasible"]
    assert res["upper"].n_reference_positive >= 1
