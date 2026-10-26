"""Primary estimand: expected fraction of reference-positive households missed.

For complete histories with K_i positive screens among n designated windows,

    M_m = sum_i 1[K_i > 0] * p_miss(K_i; n, m) / sum_i 1[K_i > 0].

M_m is conditional on the analysed households and on the n observed 30-day recall
windows. It is not a prevalence, not an annual incidence and not a causal effect of
collecting fewer interviews.
"""

from __future__ import annotations

from collections.abc import Sequence
from math import comb

import numpy as np
import pandas as pd

from .combinatorics import missed_fraction


def frontier(k_values: Sequence[int], n: int, m_values: Sequence[int]) -> pd.DataFrame:
    """Interview-count frontier for one group of complete histories."""
    k = np.asarray(list(k_values), dtype=int)
    n_complete = int(k.size)
    n_pos = int((k > 0).sum())
    rows = []
    for m in m_values:
        frac = missed_fraction(k, n, m)
        exp_missed = float(sum(comb(n - x, m) for x in k[k > 0]) / comb(n, m))
        rows.append(
            {
                "m": int(m),
                "n_complete": n_complete,
                "n_reference_positive": n_pos,
                "missed_fraction": float(frac) if frac is not None else np.nan,
                "missed_fraction_exact": str(frac) if frac is not None else "",
                "detected_fraction": 1 - float(frac) if frac is not None else np.nan,
                "expected_missed_households": exp_missed,
                "expected_detected_households": n_pos - exp_missed,
            }
        )
    return pd.DataFrame(rows)


def k_distribution(k_values: Sequence[int], n: int) -> pd.DataFrame:
    """Counts of complete households by number of positive windows (0..n)."""
    k = np.asarray(list(k_values), dtype=int)
    counts = np.bincount(k, minlength=n + 1)
    return pd.DataFrame({"k_positive_windows": np.arange(n + 1), "households": counts})


def frontier_from_distribution(dist: pd.DataFrame, n: int, m: int) -> float:
    """Recompute M_m from an aggregate K distribution (used for public-data checks)."""
    k = np.repeat(dist["k_positive_windows"].to_numpy(), dist["households"].to_numpy())
    frac = missed_fraction(k, n, m)
    return float(frac) if frac is not None else float("nan")
