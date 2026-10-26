"""Village-cluster percentile bootstrap for the complete-history ratio estimand.

Villages (not household rows) are resampled with replacement, separately by country.
Every complete-history household in a drawn village enters the replicate, with
multiplicity equal to the number of times the village was drawn. Because the
statistic is a ratio of village sums, each replicate is computed from per-village
numerator and denominator totals, which is algebraically identical to stacking the
drawn households.

The interval describes resampling variability of the within-sample statistic
conditional on complete histories. It is not a national confidence interval and does
not correct for selection into complete histories.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .combinatorics import p_miss_vector


@dataclass
class BootstrapResult:
    m_values: list[int]
    replicates: np.ndarray  # draws x len(m_values); NaN when a replicate has no positives
    n_villages: int
    n_households: int
    zero_denominator_draws: int
    seed: int
    draws: int


def village_totals(k: pd.Series, n: int, m_values: Sequence[int],
                   all_villages: Sequence[int] | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Per-village numerator (sum of miss probabilities) and denominator (# positives).

    ``k`` is indexed by a MultiIndex containing level ``village_id``. By default the
    resampling units are villages with at least one household in ``k``; passing
    ``all_villages`` adds villages that contribute no households (sensitivity option).
    """
    villages = k.index.get_level_values("village_id")
    df = pd.DataFrame({"village": villages, "pos": (k.to_numpy() > 0).astype(float)})
    for m in m_values:
        df[f"num_{m}"] = np.where(k.to_numpy() > 0, p_miss_vector(k.to_numpy(), n, m), 0.0)
    agg = df.groupby("village").sum()
    if all_villages is not None:
        agg = agg.reindex(sorted(set(all_villages) | set(agg.index)), fill_value=0.0)
    num = agg[[f"num_{m}" for m in m_values]].to_numpy()
    den = agg["pos"].to_numpy()
    return num, den


def village_bootstrap(k: pd.Series, n: int, m_values: Sequence[int], draws: int, seed: int,
                      all_villages: Sequence[int] | None = None) -> BootstrapResult:
    num, den = village_totals(k, n, m_values, all_villages)
    v = den.shape[0]
    rng = np.random.default_rng(seed)
    reps = np.empty((draws, len(m_values)))
    zero = 0
    batch = 1000
    for start in range(0, draws, batch):
        b = min(batch, draws - start)
        idx = rng.integers(0, v, size=(b, v))
        d = den[idx].sum(axis=1)
        nm = num[idx].sum(axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            reps[start:start + b] = nm / d[:, None]
        zero += int((d == 0).sum())
    return BootstrapResult(list(m_values), reps, v, int(k.size), zero, seed, draws)


def percentile_interval(reps: np.ndarray, level: float, method: str = "linear") -> tuple[np.ndarray, np.ndarray]:
    a = (1 - level) / 2
    lo = np.nanquantile(reps, a, axis=0, method=method)
    hi = np.nanquantile(reps, 1 - a, axis=0, method=method)
    return lo, hi


def summarize(res: BootstrapResult, point: Sequence[float], level: float, method: str = "linear") -> pd.DataFrame:
    lo, hi = percentile_interval(res.replicates, level, method)
    return pd.DataFrame(
        {
            "m": res.m_values,
            "point": list(point),
            "ci_low": lo,
            "ci_high": hi,
            "bootstrap_se": np.nanstd(res.replicates, axis=0, ddof=1),
            "bootstrap_mean": np.nanmean(res.replicates, axis=0),
            "draws": res.draws,
            "zero_denominator_draws": res.zero_denominator_draws,
            "villages_resampled": res.n_villages,
            "households": res.n_households,
            "seed": res.seed,
            "interval": f"{int(level * 100)}% village-cluster percentile ({method})",
        }
    )


def cluster_jackknife_se(k: pd.Series, n: int, m_values: Sequence[int]) -> np.ndarray:
    """Delete-one-village jackknife standard error (secondary diagnostic)."""
    num, den = village_totals(k, n, m_values)
    v = den.shape[0]
    tot_n, tot_d = num.sum(axis=0), den.sum()
    loo = (tot_n[None, :] - num) / (tot_d - den)[:, None]
    mean = loo.mean(axis=0)
    return np.sqrt((v - 1) / v * ((loo - mean) ** 2).sum(axis=0))
