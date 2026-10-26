"""Exact miss probabilities for uniformly sampled screening subsets.

A household has ``n`` designated reference screens, ``k`` of which are positive.
A reduced schedule retains ``m`` distinct screens chosen uniformly at random without
replacement. The household is missed when none of the retained screens is positive:

    p_miss(k; n, m) = C(n - k, m) / C(n, m)

(hypergeometric probability of zero successes). ``math.comb`` returns 0 when
``m > n - k``, which is the correct probability (every subset contains a positive).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from fractions import Fraction
from itertools import combinations
from math import comb

import numpy as np


def _check(k: int, n: int, m: int) -> None:
    if not (0 <= k <= n):
        raise ValueError(f"k={k} must lie in [0, n={n}]")
    if not (0 <= m <= n):
        raise ValueError(f"m={m} must lie in [0, n={n}]")


def miss_count(k: int, n: int, m: int) -> int:
    """Number of m-subsets of n slots containing no positive slot: C(n-k, m)."""
    _check(k, n, m)
    return comb(n - k, m)


def p_miss(k: int, n: int, m: int) -> Fraction:
    """Exact probability that a uniformly random m-subset contains no positive slot."""
    _check(k, n, m)
    return Fraction(comb(n - k, m), comb(n, m))


def p_miss_enumerated(history: Sequence[int], m: int) -> Fraction:
    """Same probability by explicit enumeration of every m-subset of the history.

    Used only to validate :func:`p_miss`; it never feeds the analysis.
    """
    n = len(history)
    if not (0 <= m <= n):
        raise ValueError("m out of range")
    subsets = list(combinations(range(n), m))
    missed = sum(1 for s in subsets if not any(history[i] for i in s))
    return Fraction(missed, len(subsets))


def missed_fraction(k_values: Iterable[int], n: int, m: int) -> Fraction | None:
    """Average miss probability over reference-positive households (k > 0).

    Households with k == 0 are not reference-positive and are excluded from both
    numerator and denominator. Returns ``None`` when no household is reference-positive.
    """
    num = 0
    den = 0
    for k in k_values:
        k = int(k)
        _check(k, n, m)
        if k > 0:
            num += comb(n - k, m)
            den += 1
    if den == 0:
        return None
    return Fraction(num, den * comb(n, m))


def p_miss_vector(k: np.ndarray, n: int, m: int) -> np.ndarray:
    """Vectorised float miss probabilities for an integer array of positive counts."""
    k = np.asarray(k, dtype=int)
    if k.size and (k.min() < 0 or k.max() > n):
        raise ValueError("k out of range")
    table = np.array([comb(n - j, m) for j in range(n + 1)], dtype=float) / comb(n, m)
    return table[k]
