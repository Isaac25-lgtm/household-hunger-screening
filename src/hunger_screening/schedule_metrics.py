"""Equal-budget schedule metrics and a generic cluster ratio bootstrap.

All metrics are computed on complete binary histories H (households x rounds). A
household is reference-positive when it is positive in at least one observed round of
the horizon; this reference is the observed rounds, not true hunger status.

Denominators (kept distinct on purpose):
  * missed share           = missed reference positives / reference positives
  * identified per 100 hh  = identified reference positives / complete households x 100
  * identified per 100 contacts = identified / (contacts per household x households) x 100
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations
from math import comb

import numpy as np
import pandas as pd


def binary_complete(mat: pd.DataFrame) -> pd.DataFrame:
    """Rows with every round observed (values 0/1), as int."""
    full = mat.dropna()
    return full.astype(int)


def household_terms(H: np.ndarray, schedule: Sequence[int] | None = None, m: int | None = None):
    """Per-household (miss numerator, reference-positive indicator).

    ``schedule`` gives column indices of a fixed schedule; otherwise ``m`` gives the
    random-retention benchmark with exact hypergeometric miss probability.
    """
    H = np.asarray(H, dtype=int)
    n = H.shape[1]
    K = H.sum(axis=1)
    pos = (K > 0).astype(float)
    if schedule is not None:
        miss = pos * (H[:, list(schedule)].sum(axis=1) == 0)
    else:
        table = np.array([comb(n - j, m) for j in range(n + 1)], dtype=float) / comb(n, m)
        miss = pos * table[K]
    return miss.astype(float), pos


def schedule_row(H: np.ndarray, schedule: Sequence[int], labels: Sequence[str]) -> dict:
    miss, pos = household_terms(H, schedule=schedule)
    n_hh = H.shape[0]
    n_pos = int(pos.sum())
    n_missed = int(miss.sum())
    ident = n_pos - n_missed
    m = len(schedule)
    return {
        "schedule": " + ".join(labels[j] for j in schedule),
        "contacts_per_household": m,
        "n_complete": n_hh,
        "n_reference_positive": n_pos,
        "n_missed": n_missed,
        "missed_share": n_missed / n_pos if n_pos else np.nan,
        "identified_per_100_households": 100 * ident / n_hh if n_hh else np.nan,
        "identified_per_100_contacts": 100 * ident / (m * n_hh) if n_hh else np.nan,
    }


def random_row(H: np.ndarray, m: int) -> dict:
    miss, pos = household_terms(H, m=m)
    n_hh = H.shape[0]
    n_pos = pos.sum()
    ident = n_pos - miss.sum()
    return {
        "schedule": f"random {m} of {H.shape[1]}",
        "contacts_per_household": m,
        "n_complete": n_hh,
        "n_reference_positive": int(n_pos),
        "n_missed": float(miss.sum()),
        "missed_share": miss.sum() / n_pos if n_pos else np.nan,
        "identified_per_100_households": 100 * ident / n_hh if n_hh else np.nan,
        "identified_per_100_contacts": 100 * ident / (m * n_hh) if n_hh else np.nan,
    }


def all_schedules(H: np.ndarray, labels: Sequence[str], budgets: Sequence[int]) -> pd.DataFrame:
    rows = []
    n = H.shape[1]
    for m in budgets:
        for s in combinations(range(n), m):
            rows.append(schedule_row(H, s, labels))
        rows.append(random_row(H, m))
    return pd.DataFrame(rows)


def ratio_bootstrap(clusters: np.ndarray, stats: dict[str, tuple[np.ndarray, np.ndarray]],
                    draws: int, seed: int) -> tuple[dict[str, np.ndarray], dict[str, int]]:
    """Percentile-bootstrap replicates of sum(num)/sum(den) for each named statistic.

    Whole clusters are resampled with replacement; every statistic uses the same draw,
    so differences between statistics computed from the replicates are paired. Returns
    replicate arrays (NaN for zero-denominator draws) and zero-denominator draw counts.
    """
    clusters = np.asarray(clusters)
    uniq, inv = np.unique(clusters, return_inverse=True)
    C = uniq.size
    tot = {k: (np.bincount(inv, weights=np.asarray(n, float), minlength=C),
               np.bincount(inv, weights=np.asarray(d, float), minlength=C)) for k, (n, d) in stats.items()}
    rng = np.random.default_rng(seed)
    reps = {k: np.empty(draws) for k in stats}
    zero = dict.fromkeys(stats, 0)
    batch = 500
    for start in range(0, draws, batch):
        b = min(batch, draws - start)
        idx = rng.integers(0, C, size=(b, C))
        for k, (nc, dc) in tot.items():
            d = dc[idx].sum(axis=1)
            zero[k] += int((d == 0).sum())
            with np.errstate(invalid="ignore", divide="ignore"):
                reps[k][start:start + b] = nc[idx].sum(axis=1) / d
    return reps, zero


def interval(rep: np.ndarray, level: float) -> tuple[float, float]:
    a = (1 - level) / 2
    return float(np.nanquantile(rep, a)), float(np.nanquantile(rep, 1 - a))
