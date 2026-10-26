"""Sharp bounds on the ascertainment ratio when designated screens are missing.

Setting. Household i has n designated windows; k_i observed positives and r_i windows
with no valid screen. With no assumption about the missing statuses, the completed
positive count can be any K_i in {k_i, ..., k_i + r_i} (every value is attained by some
binary completion, and p_miss depends on the history only through K_i). The target is

    M_m(K) = sum_i 1[K_i>0] A(K_i) / (C(n,m) * sum_i 1[K_i>0]),   A(K) = C(n-K, m),

over worlds with at least one reference-positive household. Completing missing
windows changes the numerator *and* the denominator, so "all missing negative" and
"all missing positive" are not in general the endpoints.

Sharpness argument (lower bound; the upper bound is symmetric).
  1. M_m is the mean of A(K_i) over the included set S = {i : K_i > 0}.
  2. Households with k_i > 0 are always in S. Households with k_i = 0 and r_i > 0 may be
     in S or not. Households with k_i = 0, r_i = 0 are never in S.
  3. For a fixed S, the mean is minimised by giving each member its smallest attainable
     A, i.e. K_i = k_i + r_i (A is decreasing in K).
  4. Given these values, the minimum-mean superset of the forced set adds exactly the
     optional households whose value is below the optimal mean; ordering optional
     values ascending, the optimum is therefore one of the prefixes. Evaluating every
     prefix is exhaustive, so the minimum found is attained by a feasible completion
     and no feasible completion does better. Exact rational arithmetic is used.
For the upper bound each member takes its largest attainable A: K_i = max(k_i, 1).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from math import comb

import numpy as np


@dataclass
class BoundResult:
    value: Fraction | None
    n_reference_positive: int
    completed_k: np.ndarray | None  # one optimal completion (positive counts)


def _optimise(k: np.ndarray, r: np.ndarray, n: int, m: int, sense: str) -> BoundResult:
    c_nm = comb(n, m)
    forced = k > 0
    optional = (k == 0) & (r > 0)
    K = np.zeros_like(k)
    if sense == "min":
        K[forced] = k[forced] + r[forced]
        opt_K = r[optional]  # optional household's best positive count when included
    else:
        K[forced] = k[forced]
        opt_K = np.ones(optional.sum(), dtype=k.dtype)
    vals = np.array([comb(n - x, m) for x in opt_K], dtype=object)
    order = np.argsort([int(v) for v in vals], kind="stable")
    if sense == "max":
        order = order[::-1]
    opt_idx = np.flatnonzero(optional)[order]
    opt_vals = [int(vals[j]) for j in order]

    s = sum(comb(n - x, m) for x in K[forced])
    d = int(forced.sum())
    best: Fraction | None = Fraction(s, d * c_nm) if d > 0 else None
    best_prefix = 0
    for j, v in enumerate(opt_vals, start=1):
        s += v
        d += 1
        cand = Fraction(s, d * c_nm)
        if best is None or (cand < best if sense == "min" else cand > best):
            best, best_prefix = cand, j
    if best is None:
        return BoundResult(None, 0, None)
    chosen = opt_idx[:best_prefix]
    K_opt = K.copy()
    if sense == "min":
        K_opt[chosen] = r[chosen]
    else:
        K_opt[chosen] = 1
    return BoundResult(best, int((K_opt > 0).sum()), K_opt)


def sharp_missing_bounds(k: Sequence[int], r: Sequence[int], n: int, m: int) -> dict:
    k = np.asarray(k, dtype=int)
    r = np.asarray(r, dtype=int)
    if np.any(k < 0) or np.any(r < 0) or np.any(k + r > n):
        raise ValueError("invalid (k, r) for n")
    lo = _optimise(k, r, n, m, "min")
    hi = _optimise(k, r, n, m, "max")
    return {
        "lower": lo,
        "upper": hi,
        "zero_positive_world_feasible": bool(np.all(k == 0)),
    }


def naive_imputations(k: Sequence[int], r: Sequence[int], n: int, m: int) -> dict:
    """Single-imputation comparators: every missing window negative / positive."""
    from .combinatorics import missed_fraction

    k = np.asarray(k, dtype=int)
    r = np.asarray(r, dtype=int)
    return {
        "all_missing_negative": missed_fraction(k, n, m),
        "all_missing_positive": missed_fraction(k + r, n, m),
    }
