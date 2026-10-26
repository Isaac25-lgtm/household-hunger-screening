"""Sharp missing-history bounds versus slot-level brute force over every binary completion."""

from fractions import Fraction
from itertools import combinations, product

import numpy as np
import pytest

from hunger_screening.missing_bounds import naive_imputations, sharp_missing_bounds


def _ratio_by_subsets(histories, m):
    """Independent evaluator: average over positive histories of enumerated miss share."""
    n = len(histories[0])
    subs = list(combinations(range(n), m))
    vals = [Fraction(sum(1 for s in subs if not any(h[i] for i in s)), len(subs)) for h in histories if any(h)]
    return None if not vals else sum(vals) / len(vals)


def brute_force(obs, m):
    """obs: list of tuples with entries 0, 1 or None (missing). Enumerates all completions."""
    per_hh = []
    for h in obs:
        miss = [i for i, x in enumerate(h) if x is None]
        comps = []
        for fill in product((0, 1), repeat=len(miss)):
            c = list(h)
            for i, v in zip(miss, fill):
                c[i] = v
            comps.append(tuple(c))
        per_hh.append(comps)
    lo = hi = None
    for world in product(*per_hh):
        r = _ratio_by_subsets(world, m)
        if r is None:
            continue
        lo = r if lo is None or r < lo else lo
        hi = r if hi is None or r > hi else hi
    return lo, hi


def random_instance(rng, n, n_hh, p_miss):
    obs = []
    for _ in range(n_hh):
        h = []
        for _ in range(n):
            if rng.uniform() < p_miss:
                h.append(None)
            else:
                h.append(int(rng.uniform() < 0.35))
        obs.append(tuple(h))
    return obs


def kr(obs):
    k = [sum(x for x in h if x is not None) for h in obs]
    r = [sum(1 for x in h if x is None) for h in obs]
    return np.array(k), np.array(r)


@pytest.mark.parametrize("seed", range(40))
def test_bounds_equal_brute_force(seed):
    rng = np.random.default_rng(seed)
    n = int(rng.integers(3, 5))
    n_hh = int(rng.integers(2, 5))
    obs = random_instance(rng, n, n_hh, p_miss=float(rng.uniform(0.1, 0.6)))
    k, r = kr(obs)
    for m in range(1, n + 1):
        b = sharp_missing_bounds(k, r, n, m)
        lo, hi = brute_force(obs, m)
        assert b["lower"].value == lo
        assert b["upper"].value == hi


def test_denominator_changes_and_naive_imputation_is_not_sharp():
    # forced positive with K fixed at 1 plus two fully missing households:
    # min ratio adds both optional households at K = n; max adds them at K = 1.
    obs = [(1, 0, 0, 0), (None, None, None, None), (None, None, None, None), (0, 0, 0, 0)]
    k, r = kr(obs)
    b = sharp_missing_bounds(k, r, 4, 1)
    lo, hi = brute_force(obs, 1)
    assert (b["lower"].value, b["upper"].value) == (lo, hi)
    naive = naive_imputations(k, r, 4, 1)
    assert lo <= naive["all_missing_positive"] <= hi
    assert lo <= naive["all_missing_negative"] <= hi


def test_all_negative_world_and_no_missing():
    b = sharp_missing_bounds([0, 0], [0, 0], 6, 1)
    assert b["lower"].value is None and b["upper"].value is None
    assert b["zero_positive_world_feasible"]
    b = sharp_missing_bounds([1, 2, 0], [0, 0, 0], 6, 2)
    assert b["lower"].value == b["upper"].value


def test_invalid_input():
    with pytest.raises(ValueError):
        sharp_missing_bounds([5], [2], 6, 1)
