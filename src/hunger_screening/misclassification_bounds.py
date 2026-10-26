"""Bounds under missing windows plus a shared budget of observed-label flips.

Hypothetical sensitivity analysis: up to B = floor(alpha * total observed binary
screens) of the *observed* binary labels (across all households in a country) may be
wrong; missing windows remain unrestricted. This is a sensitivity budget, not an
estimated misclassification rate.

Minimum flips to reach a completed count K (derivation). With k observed positives,
o = n - r observed windows (o - k observed negatives) and r missing windows, a
completion with a positive->negative flips, b negative->positive flips and u missing
windows set positive has K = k - a + b + u, with 0<=a<=k, 0<=b<=o-k, 0<=u<=r.
  * If k <= K <= k + r: a = b = 0 suffices, cost 0.
  * If K < k: missing windows can only add positives, so a >= k - K; a = k - K, b = u = 0
    is feasible because K >= 0. Cost k - K.
  * If K > k + r: b >= K - k - r; feasible iff K - k - r <= o - k, i.e. K <= n, which
    always holds. Cost K - k - r.
Hence cost(K) = max(0, k - K, K - k - r), feasible for every K in 0..n. Only observed
windows consume budget, and p_miss depends only on K, so which windows flip is
irrelevant to the objective.

Optimisation. Minimise (or maximise) the ratio sum_i R_i A(K_i) / sum_i R_i subject to
sum_i cost_i(K_i) <= B. Dinkelbach's method reduces this to a sequence of problems
    F(lambda) = min_K sum_i R_i (A(K_i) - lambda)  s.t. budget,
each solved *exactly* as a multiple-choice knapsack by dynamic programming over the
integer budget with integer arithmetic (lambda = P/Q is rational; values are scaled by
Q). Dinkelbach terminates finitely at the exact optimum when each subproblem is solved
exactly; at termination F(lambda*) = 0, which certifies that no feasible completion has
a smaller ratio. alpha = 0 reproduces the missing-history bounds exactly.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from math import comb

import numpy as np


def flip_cost(k: int, r: int, K: int) -> int:
    return max(0, k - K, K - k - r)


@dataclass
class LabelErrorBound:
    value: Fraction | None
    n_reference_positive: int
    budget: int
    budget_used: int
    dinkelbach_iterations: int
    certificate_F: int  # scaled F(lambda*) at termination; 0 certifies optimality
    completed_k: np.ndarray | None


def _solve_parametric(cost: np.ndarray, A: np.ndarray, B: int, P: int, Q: int, sense: str):
    """Exact DP for min (sense='min') or max of sum_i R_i (Q*A_i - P) under budget B."""
    N, nk = cost.shape
    sign = 1 if sense == "min" else -1
    vals = np.zeros(nk, dtype=np.int64)
    vals[1:] = sign * (Q * A[1:].astype(np.int64) - P)
    INF = np.iinfo(np.int64).max // 4
    f = np.zeros(B + 1, dtype=np.int64)
    choice = np.zeros((N, B + 1), dtype=np.int8)
    for i in range(N):
        best = np.full(B + 1, INF, dtype=np.int64)
        bestK = np.zeros(B + 1, dtype=np.int8)
        for K in range(nk):
            c = int(cost[i, K])
            if c > B:
                continue
            cand = np.full(B + 1, INF, dtype=np.int64)
            cand[c:] = f[: B + 1 - c] + vals[K]
            better = cand < best
            best[better] = cand[better]
            bestK[better] = K
        f = best
        choice[i] = bestK
    b = B
    Ks = np.zeros(N, dtype=int)
    for i in range(N - 1, -1, -1):
        K = int(choice[i, b])
        Ks[i] = K
        b -= int(cost[i, K])
    return sign * int(f[B]), Ks


def label_error_bounds(k: Sequence[int], r: Sequence[int], n: int, m: int, budget: int,
                       max_iter: int = 200) -> dict:
    k = np.asarray(k, dtype=int)
    r = np.asarray(r, dtype=int)
    if np.any(k + r > n):
        raise ValueError("invalid (k, r)")
    N = k.size
    cost = np.array([[flip_cost(int(k[i]), int(r[i]), K) for K in range(n + 1)] for i in range(N)], dtype=int)
    A = np.array([comb(n - K, m) for K in range(n + 1)], dtype=object)
    c_nm = comb(n, m)

    def ratio(Ks: np.ndarray) -> Fraction | None:
        pos = Ks > 0
        d = int(pos.sum())
        if d == 0:
            return None
        return Fraction(int(sum(A[x] for x in Ks[pos])), d)

    out = {}
    for sense in ("min", "max"):
        # feasible start with at least one positive household
        start = np.where(k > 0, k, 0)
        if (start > 0).sum() == 0:
            cand = np.flatnonzero((r > 0) | (cost[:, 1] <= budget))
            if cand.size == 0:
                out["lower" if sense == "min" else "upper"] = LabelErrorBound(None, 0, budget, 0, 0, 0, None)
                continue
            start = start.copy()
            start[cand[0]] = 1
        lam = ratio(start)
        Ks_best = start
        iters = 0
        F = None
        while iters < max_iter:
            iters += 1
            F, Ks = _solve_parametric(cost, A, budget, lam.numerator, lam.denominator, sense)
            improved = F < 0 if sense == "min" else F > 0
            if not improved:
                break
            new = ratio(Ks)
            if new is None:  # cannot happen when F != 0, guard anyway
                break
            lam, Ks_best = new, Ks
        else:
            raise RuntimeError("Dinkelbach did not converge")
        used = int(sum(cost[i, Ks_best[i]] for i in range(N)))
        assert used <= budget
        out["lower" if sense == "min" else "upper"] = LabelErrorBound(
            value=lam / c_nm,
            n_reference_positive=int((Ks_best > 0).sum()),
            budget=budget,
            budget_used=used,
            dinkelbach_iterations=iters,
            certificate_F=int(F),
            completed_k=Ks_best,
        )
    out["zero_positive_world_feasible"] = bool(int(k.sum()) <= budget)
    return out
