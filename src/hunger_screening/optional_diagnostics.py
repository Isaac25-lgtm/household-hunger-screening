"""Secondary analyses: thresholds, fixed schedules, observation patterns, attrition, IPW.

All of these are secondary to the primary estimand and are labelled as such in reports.
The IPW estimate in particular rests on a missing-at-random assumption given baseline
covariates and is reported only next to the assumption-free bounds, never instead of them.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd

from .build_panels import SLOT_LABELS
from .combinatorics import p_miss_vector

BASELINE_COVARIATES = {
    "baseline_hhs_ge2": "Baseline HHS >= 2",
    "hh_size": "Household size",
    "female": "Respondent female",
    "age": "Respondent age (years)",
    "years_educ": "Respondent years of education",
    "log_total_expend": "log(1 + monthly expenditure, USD)",
    "thatch_roof": "Thatch roof",
}


def fixed_schedule_table(binary_complete: pd.DataFrame, m_values) -> pd.DataFrame:
    """Missed fraction for every fixed m-subset of slots, among reference-positive households."""
    pos = binary_complete[binary_complete.sum(axis=1) > 0]
    slots = list(binary_complete.columns)
    rows = []
    for m in m_values:
        for sub in combinations(slots, m):
            missed = float((pos[list(sub)].sum(axis=1) == 0).mean())
            gaps = np.diff(sorted(sub))
            even = m > 1 and len(set(gaps)) == 1 and (sub[0] + len(slots) - sub[-1]) == gaps[0]
            rows.append({"m": m, "schedule": "+".join(SLOT_LABELS[s] for s in sub),
                         "slots": ",".join(str(s) for s in sub), "evenly_spaced": bool(even),
                         "missed_fraction": missed, "n_reference_positive": len(pos)})
    return pd.DataFrame(rows)


def observation_pattern(mat: pd.DataFrame) -> pd.DataFrame:
    """Share of frame households with a valid screen by country and slot (aggregate)."""
    rows = []
    for c in mat.index.get_level_values("country").unique():
        sub = mat.xs(c, level="country")
        for s in sub.columns:
            rows.append({"country": c, "year": mat.attrs.get("year"), "slot": int(s),
                         "slot_label": SLOT_LABELS[int(s)], "frame_households": len(sub),
                         "observed": int(sub[s].notna().sum()),
                         "observed_share": float(sub[s].notna().mean())})
    return pd.DataFrame(rows)


def slot_positive_share(mat: pd.DataFrame, threshold: int) -> pd.DataFrame:
    """Share HHS >= threshold among observed screens, by country and slot (descriptive)."""
    rows = []
    for c in mat.index.get_level_values("country").unique():
        sub = mat.xs(c, level="country")
        for s in sub.columns:
            obs = sub[s].dropna()
            rows.append({"country": c, "year": mat.attrs.get("year"), "slot": int(s),
                         "slot_label": SLOT_LABELS[int(s)], "observed": len(obs),
                         "positive": int((obs >= threshold).sum()),
                         "positive_share": float((obs >= threshold).mean()) if len(obs) else np.nan})
    return pd.DataFrame(rows)


def observed_count_distribution(binary: pd.DataFrame) -> pd.DataFrame:
    n_obs = binary.notna().sum(axis=1)
    df = pd.DataFrame({"country": n_obs.index.get_level_values("country"), "n_observed_slots": n_obs.to_numpy()})
    return (df.groupby(["country", "n_observed_slots"]).size().rename("households").reset_index()
            .sort_values(["country", "n_observed_slots"]))


def prepare_covariates(baseline: pd.DataFrame) -> pd.DataFrame:
    b = baseline.set_index(["country", "village_id", "id"]).sort_index()
    out = pd.DataFrame(index=b.index)
    out["baseline_hhs_ge2"] = (b["HHS"] >= 2).astype(float)
    out["hh_size"] = b["hh_size"].astype(float)
    out["female"] = b["female"].astype(float)
    out["age"] = b["age"].astype(float)
    out["years_educ"] = b["years_educ"].astype(float)
    out["log_total_expend"] = np.log1p(b["total_expend_mon_usd"].astype(float))
    out["thatch_roof"] = b["thatch_roof"].astype(float)
    return out


def cluster_robust_diff(y: np.ndarray, d: np.ndarray, g: np.ndarray) -> tuple[float, float]:
    """OLS of y on [1, d] with CR1 village-clustered SE for the coefficient on d."""
    ok = ~np.isnan(y)
    y, d, g = y[ok], d[ok], g[ok]
    X = np.column_stack([np.ones_like(d), d])
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    u = y - X @ beta
    meat = np.zeros((2, 2))
    for grp in np.unique(g):
        s = X[g == grp].T @ u[g == grp]
        meat += np.outer(s, s)
    G, N, K = len(np.unique(g)), len(y), 2
    V = XtX_inv @ meat @ XtX_inv * (G / (G - 1)) * ((N - 1) / (N - K))
    return float(beta[1]), float(np.sqrt(V[1, 1]))


def attrition_balance(cov: pd.DataFrame, complete: pd.Series) -> pd.DataFrame:
    rows = []
    for c in cov.index.get_level_values("country").unique():
        sub = cov.xs(c, level="country", drop_level=False)
        d = complete.reindex(sub.index).fillna(False).astype(float).to_numpy()
        g = sub.index.get_level_values("village_id").to_numpy()
        for var, label in BASELINE_COVARIATES.items():
            y = sub[var].to_numpy(dtype=float)
            diff, se = cluster_robust_diff(y, d, g)
            rows.append({
                "country": c, "covariate": label,
                "mean_complete": float(np.nanmean(y[d == 1])), "mean_incomplete": float(np.nanmean(y[d == 0])),
                "n_complete": int((d == 1).sum()), "n_incomplete": int((d == 0).sum()),
                "difference": diff, "cluster_se": se, "z": diff / se if se > 0 else np.nan,
            })
    return pd.DataFrame(rows)


def _logit_irls(X: np.ndarray, y: np.ndarray, ridge: float = 1e-6, iters: int = 100) -> np.ndarray:
    beta = np.zeros(X.shape[1])
    for _ in range(iters):
        eta = np.clip(X @ beta, -30, 30)
        p = 1 / (1 + np.exp(-eta))
        W = p * (1 - p)
        H = X.T @ (X * W[:, None]) + ridge * np.eye(X.shape[1])
        step = np.linalg.solve(H, X.T @ (y - p) - ridge * beta)
        beta += step
        if np.max(np.abs(step)) < 1e-10:
            break
    return beta


def ipw_frontier(cov: pd.DataFrame, binary2020: pd.DataFrame, n: int, m_values) -> pd.DataFrame:
    """Secondary MAR-type estimate: complete histories weighted by 1 / P(complete | baseline).

    Assumption: conditional on the listed baseline covariates, having a complete 2020
    history is independent of the 2020 hunger history. Not verifiable from these data.
    """
    rows = []
    for c in cov.index.get_level_values("country").unique():
        sub = cov.xs(c, level="country", drop_level=False).copy()
        sub = sub.fillna(sub.median())
        Z = (sub - sub.mean()) / sub.std(ddof=0).replace(0, 1)
        X = np.column_stack([np.ones(len(Z)), Z.to_numpy()])
        b = binary2020.reindex(sub.index)
        comp = b.notna().all(axis=1).to_numpy()
        beta = _logit_irls(X, comp.astype(float))
        p = 1 / (1 + np.exp(-(X @ beta)))
        bc = b[comp]
        k = bc.sum(axis=1).to_numpy().astype(int)
        w = 1 / p[comp]
        pos = k > 0
        for m in m_values:
            pm = p_miss_vector(k, n, m)
            est = float((w[pos] * pm[pos]).sum() / w[pos].sum())
            rows.append({"country": c, "m": m, "ipw_missed_fraction": est,
                         "n_complete": int(comp.sum()), "n_frame": len(sub),
                         "min_propensity": float(p[comp].min()), "max_weight": float(w.max()),
                         "effective_n_positive": float(w[pos].sum() ** 2 / (w[pos] ** 2).sum())})
    return pd.DataFrame(rows)
