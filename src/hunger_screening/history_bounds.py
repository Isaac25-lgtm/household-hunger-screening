"""Exact bounds for any ratio-of-sums screening contrast over completed histories.

Setting. Household i has n screens, each observed positive (1), observed negative (0)
or missing (-1). A *contrast* maps a completed binary history h to integers
(num(h), den(h)); the target is the ratio sum_i num(h_i) / sum_i den(h_i). Examples:

  * missed share of a fixed schedule S:   num = 1[K>0, h_S = 0],         den = 1[K>0]
  * expected missed share, random m:      num = C(n-K, m),               den = C(n,m) 1[K>0]
  * fixed S minus random m (difference):  num = C(n,m) 1[K>0, h_S = 0] - C(n-K, m),
                                          den = C(n,m) 1[K>0]

Feasible worlds. Missing screens may take either value at no cost. Optionally, up to B
*observed* screens across all households may be flipped (a hypothetical response-error
budget, not an estimated error rate). A world must have sum_i den > 0.

Exactness. For fixed lambda = P/Q, Dinkelbach's subproblem
    F(lambda) = min sum_i (Q num(h_i) - P den(h_i))  subject to  sum_i cost(h_i) <= B
depends on each household only through the pair (cost, value), so for every possible
cost c in 0..n we keep the minimum value over histories with that cost; the subproblem
is then an exact multiple-choice knapsack solved by dynamic programming over the
integer budget. Dinkelbach terminates at the exact optimum; at termination
F(lambda*) = 0 is the optimality certificate. With B = 0 the households separate and
the same code reduces to independent per-household choices.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from math import comb

import numpy as np

Contrast = Callable[[tuple[int, ...]], tuple[int, int]]


def fixed_missed(schedule: Sequence[int]) -> Contrast:
    s = tuple(schedule)

    def f(h: tuple[int, ...]) -> tuple[int, int]:
        pos = any(h)
        return (int(pos and not any(h[j] for j in s)), int(pos))

    return f


def random_missed(n: int, m: int) -> Contrast:
    c = comb(n, m)

    def f(h: tuple[int, ...]) -> tuple[int, int]:
        K = sum(h)
        return (comb(n - K, m) if K > 0 else 0, c if K > 0 else 0)

    return f


def fixed_minus_random(schedule: Sequence[int], n: int, m: int) -> Contrast:
    s = tuple(schedule)
    c = comb(n, m)

    def f(h: tuple[int, ...]) -> tuple[int, int]:
        K = sum(h)
        if K == 0:
            return (0, 0)
        return (c * int(not any(h[j] for j in s)) - comb(n - K, m), c)

    return f


def _histories(obs: tuple[int, ...], flips: bool):
    """Yield (history, cost) for every binary history reachable from ``obs``."""
    n = len(obs)
    for h in product((0, 1), repeat=n):
        cost = sum(1 for j in range(n) if obs[j] >= 0 and h[j] != obs[j])
        if cost and not flips:
            continue
        yield h, cost


@dataclass
class _Pattern:
    obs: tuple[int, ...]
    count: int
    options: list[tuple[tuple[int, ...], int, int, int]]  # (history, cost, num, den)


@dataclass
class ContrastBound:
    value: Fraction | None
    numerator: int
    denominator: int
    budget: int
    budget_used: int
    iterations: int
    certificate_F: int


def _patterns(histories: np.ndarray, contrast: Contrast, flips: bool) -> list[_Pattern]:
    rows, counts = np.unique(np.asarray(histories, dtype=int), axis=0, return_counts=True)
    out = []
    for row, cnt in zip(rows, counts):
        obs = tuple(int(x) for x in row)
        opts = [(h, c, *contrast(h)) for h, c in _histories(obs, flips)]
        out.append(_Pattern(obs, int(cnt), opts))
    return out


def _solve(pats: list[_Pattern], P: int, Q: int, B: int, sense: str):
    """Exact min (sense='min') or max of sum (Q num - P den) under the flip budget."""
    sign = 1 if sense == "min" else -1
    INF = np.iinfo(np.int64).max // 4
    f = np.zeros(B + 1, dtype=np.int64)
    trace = []  # per household unit: (pattern index, best option index per cost, chosen cost per b)
    for pi, pat in enumerate(pats):
        best_by_cost: dict[int, tuple[int, int]] = {}
        for oi, (_, c, num, den) in enumerate(pat.options):
            if c > B:
                continue
            v = sign * (Q * num - P * den)
            if c not in best_by_cost or v < best_by_cost[c][0]:
                best_by_cost[c] = (v, oi)
        for _ in range(pat.count):
            g = np.full(B + 1, INF, dtype=np.int64)
            gc = np.zeros(B + 1, dtype=np.int16)
            for c, (v, _) in best_by_cost.items():
                cand = np.full(B + 1, INF, dtype=np.int64)
                cand[c:] = f[: B + 1 - c] + v
                better = cand < g
                g[better] = cand[better]
                gc[better] = c
            f = g
            trace.append((pi, {c: oi for c, (_, oi) in best_by_cost.items()}, gc))
    b = int(np.argmin(f))  # any budget up to B is allowed
    total = sign * int(f[b])
    chosen = []
    for pi, opt_of_cost, gc in reversed(trace):
        c = int(gc[b])
        chosen.append((pi, opt_of_cost[c]))
        b -= c
    return total, chosen


def _start_world(pats: list[_Pattern], budget: int) -> tuple[int, int, int] | None:
    """A complete feasible world with den > 0: (num, den, cost), or None if none exists.

    Every household takes a zero-cost history (observed screens kept); if that world has
    no reference positive, the cheapest affordable history with den > 0 is swapped in for
    one household.
    """
    num = den = 0
    zero = []
    for pat in pats:
        h0 = next(o for o in pat.options if o[1] == 0)
        zero.append(h0)
        num += pat.count * h0[2]
        den += pat.count * h0[3]
    if den > 0:
        return num, den, 0
    for pi, pat in enumerate(pats):
        for o in pat.options:
            if o[3] > 0 and o[1] == 0:
                return num - zero[pi][2] + o[2], den - zero[pi][3] + o[3], 0
    best = None
    for pi, pat in enumerate(pats):
        for o in pat.options:
            if o[3] > 0 and o[1] <= budget and (best is None or o[1] < best[2]):
                best = (num - zero[pi][2] + o[2], den - zero[pi][3] + o[3], o[1])
    return best


def contrast_bounds(histories: np.ndarray, contrast: Contrast, budget: int = 0,
                    max_iter: int = 500) -> dict[str, ContrastBound]:
    """Exact lower and upper values of the contrast over all feasible worlds.

    ``histories``: integer array (households x n) with 1/0 observed and -1 missing.
    """
    flips = budget > 0
    pats = _patterns(histories, contrast, flips)
    out: dict[str, ContrastBound] = {}
    start = _start_world(pats, budget)
    for sense in ("min", "max"):
        if start is None:
            out["lower" if sense == "min" else "upper"] = ContrastBound(None, 0, 0, budget, 0, 0, 0)
            continue
        num_best, den_best, used_best = start
        lam = Fraction(num_best, den_best)
        it = 0
        while True:
            it += 1
            if it > max_iter:
                raise RuntimeError("Dinkelbach did not converge")
            F, chosen = _solve(pats, lam.numerator, lam.denominator, budget, sense)
            improved = F < 0 if sense == "min" else F > 0
            if not improved:
                break
            num = sum(pats[pi].options[oi][2] for pi, oi in chosen)
            den = sum(pats[pi].options[oi][3] for pi, oi in chosen)
            used = sum(pats[pi].options[oi][1] for pi, oi in chosen)
            if den <= 0:
                break
            lam, num_best, den_best, used_best = Fraction(num, den), num, den, used
        assert used_best <= budget
        out["lower" if sense == "min" else "upper"] = ContrastBound(
            lam, num_best, den_best, budget, used_best, it, int(F))
    return out


def observed_value(histories: np.ndarray, contrast: Contrast) -> Fraction | None:
    """Contrast on households with no missing screens (complete-case point value)."""
    h = np.asarray(histories, dtype=int)
    full = h[(h >= 0).all(axis=1)]
    num = den = 0
    for row in full:
        a, b = contrast(tuple(int(x) for x in row))
        num, den = num + a, den + b
    return Fraction(num, den) if den else None


def tipping_budget(histories: np.ndarray, contrast: Contrast, sense: str = "max",
                   threshold: Fraction = Fraction(0), cap: int = 100000) -> int | None:
    """Smallest flip budget B whose bound reaches ``threshold``.

    sense='max': smallest B with upper bound >= threshold (e.g. a negative difference
    can be pushed to zero). Returns None if not reached by ``cap``. Uses monotonicity of
    the bound in B (the feasible set only grows).
    """
    key = "upper" if sense == "max" else "lower"

    def reached(B: int) -> bool:
        v = contrast_bounds(histories, contrast, B)[key].value
        if v is None:
            return False
        return v >= threshold if sense == "max" else v <= threshold

    if reached(0):
        return 0
    hi = 1
    while not reached(hi):
        hi *= 2
        if hi > cap:
            return None
    lo = hi // 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if reached(mid):
            hi = mid
        else:
            lo = mid
    return hi


def brute_force_bounds(histories: np.ndarray, contrast: Contrast, budget: int = 0):
    """Exhaustive enumeration over every household's histories (validation only)."""
    h = np.asarray(histories, dtype=int)
    opts = [[(c, *contrast(hist)) for hist, c in _histories(tuple(int(x) for x in row), budget > 0)]
            for row in h]
    lo = hi = None
    for combo in product(*opts):
        if sum(o[0] for o in combo) > budget:
            continue
        den = sum(o[2] for o in combo)
        if den <= 0:
            continue
        r = Fraction(sum(o[1] for o in combo), den)
        lo = r if lo is None or r < lo else lo
        hi = r if hi is None or r > hi else hi
    return lo, hi
