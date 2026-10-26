"""Village-cluster bootstrap mechanics."""

import numpy as np
import pandas as pd

from hunger_screening.cluster_bootstrap import (
    cluster_jackknife_se,
    summarize,
    village_bootstrap,
    village_totals,
)
from hunger_screening.combinatorics import missed_fraction


def make_k(villages, ks):
    idx = pd.MultiIndex.from_arrays([["X"] * len(ks), villages, range(len(ks))],
                                    names=["country", "village_id", "id"])
    return pd.Series(ks, index=idx)


def test_totals_reproduce_point_estimate():
    k = make_k([1, 1, 2, 3, 3, 3], [0, 2, 1, 6, 3, 0])
    num, den = village_totals(k, 6, [1, 2])
    for j, m in enumerate([1, 2]):
        assert np.isclose(num[:, j].sum() / den.sum(), float(missed_fraction(k.to_numpy(), 6, m)))


def test_replicate_equals_stacked_households():
    """A replicate from village totals equals the estimand on the stacked drawn households."""
    k = make_k([1, 1, 2, 3, 3, 4], [1, 2, 0, 5, 1, 3])
    num, den = village_totals(k, 6, [1])
    vill = np.array(sorted(set(k.index.get_level_values("village_id"))))
    draw = np.array([0, 0, 3, 2])
    stacked = np.concatenate([k[k.index.get_level_values("village_id") == vill[d]].to_numpy() for d in draw])
    assert np.isclose(num[draw, 0].sum() / den[draw].sum(), float(missed_fraction(stacked, 6, 1)))


def test_whole_villages_are_resampled_not_households():
    # each village is homogeneous; any replicate is a mix of village values only
    k = make_k([1, 1, 1, 2, 2, 2], [1, 1, 1, 6, 6, 6])  # p_miss: 5/6 and 0
    res = village_bootstrap(k, 6, [1], draws=500, seed=1)
    reps = res.replicates[:, 0]
    allowed = {0.0, 5 / 6, 5 / 12}
    assert all(any(np.isclose(x, a) for a in allowed) for x in reps)


def test_seed_reproducible_and_zero_denominator_counted():
    k = make_k([1, 2, 3, 4], [0, 0, 0, 2])
    a = village_bootstrap(k, 6, [1, 2], 300, 7)
    b = village_bootstrap(k, 6, [1, 2], 300, 7)
    assert np.array_equal(a.replicates, b.replicates, equal_nan=True)
    assert a.zero_denominator_draws > 0
    assert np.isnan(a.replicates).any(axis=1).sum() == a.zero_denominator_draws
    s = summarize(a, [0.5, 0.2], 0.95)
    assert (s.ci_low <= s.ci_high).all()


def test_all_village_option_adds_empty_clusters():
    k = make_k([1, 2], [1, 2])
    num, den = village_totals(k, 6, [1], all_villages=[1, 2, 3, 4])
    assert den.shape[0] == 4 and den[2:].sum() == 0


def test_jackknife_finite():
    rng = np.random.default_rng(0)
    k = make_k(list(rng.integers(0, 20, 120)), list(rng.integers(0, 7, 120)))
    se = cluster_jackknife_se(k, 6, [1, 2, 3])
    assert np.all(np.isfinite(se)) and np.all(se > 0)
