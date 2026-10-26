"""Calendar timing: choose one screening window in 2020, evaluate it frozen in 2021.

Separate design from the primary six-slot estimand: only the four two-month windows
observed in both years (Jan-Feb, Mar-Apr, May-Jun, Jul-Aug) are used. Among households
complete in those four windows, the reference is "HHS >= threshold in >= 1 window" and
the loss of a single fixed window s is the share of reference-positive households
negative in s.

``select_slot`` only accepts a training-year matrix and returns an immutable rule;
``evaluate_rule`` applies the frozen rule to any other matrix. Selection never sees
test-year outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


class LeakageError(RuntimeError):
    pass


@dataclass(frozen=True)
class FrozenRule:
    slot: int
    train_year: int
    threshold: int
    tie_break: str
    train_missed: float
    train_n_reference_positive: int


def candidate_table(binary: pd.DataFrame) -> pd.DataFrame:
    comp = binary.dropna()
    pos = comp[comp.sum(axis=1) > 0]
    n_pos = len(pos)
    k = pos.sum(axis=1)
    rows = []
    for s in comp.columns:
        missed = float((pos[s] == 0).mean()) if n_pos else np.nan
        rows.append({"slot": int(s), "missed_fraction": missed, "n_reference_positive": n_pos,
                     "n_complete": len(comp), "n_missed": int((pos[s] == 0).sum())})
    df = pd.DataFrame(rows)
    df.attrs["random_one_slot"] = float(((comp.shape[1] - k) / comp.shape[1]).mean()) if n_pos else np.nan
    return df


def select_slot(train: pd.DataFrame, train_year: int, threshold: int, tie_break: str = "earliest") -> FrozenRule:
    if train.attrs.get("year") != train_year:
        raise LeakageError(f"selection received data for year {train.attrs.get('year')}, expected {train_year}")
    if tie_break != "earliest":
        raise ValueError("only the prespecified 'earliest' tie-break is implemented")
    cand = candidate_table(train)
    best = cand["missed_fraction"].min()
    winner = cand[np.isclose(cand["missed_fraction"], best)].sort_values("slot").iloc[0]
    return FrozenRule(int(winner["slot"]), train_year, threshold, tie_break,
                      float(winner["missed_fraction"]), int(winner["n_reference_positive"]))


def evaluate_rule(rule: FrozenRule, test: pd.DataFrame) -> dict:
    comp = test.dropna()
    pos = comp[comp.sum(axis=1) > 0]
    n_pos = len(pos)
    k = pos.sum(axis=1)
    return {
        "year": test.attrs.get("year"),
        "slot": rule.slot,
        "n_complete": len(comp),
        "n_reference_positive": n_pos,
        "n_missed_frozen": int((pos[rule.slot] == 0).sum()),
        "missed_frozen": float((pos[rule.slot] == 0).mean()) if n_pos else np.nan,
        "missed_random_one_slot": float(((comp.shape[1] - k) / comp.shape[1]).mean()) if n_pos else np.nan,
    }


def restrict(mat: pd.DataFrame, ids: pd.Index) -> pd.DataFrame:
    out = mat.loc[mat.index.intersection(ids)]
    out.attrs.update(mat.attrs)
    return out


def bootstrap_timing(train: pd.DataFrame, test: pd.DataFrame, rule: FrozenRule, draws: int, seed: int) -> dict:
    """Village bootstrap of (a) 2020 selection stability and (b) frozen-rule 2021 loss.

    (a) resamples 2020 villages and re-runs the selection rule, recording which slot wins.
    (b) resamples 2021 villages, holding the 2020-frozen slot fixed, and records the
        frozen-slot loss, the random-slot benchmark and their difference.
    """
    rng = np.random.default_rng(seed)
    slots = list(train.columns)

    tc = train.dropna()
    tpos = tc[tc.sum(axis=1) > 0]
    tv = tpos.index.get_level_values("village_id")
    neg_by_slot = pd.DataFrame({s: (tpos[s] == 0).astype(int) for s in slots}).groupby(tv).sum()
    cnt = tpos.groupby(tv).size().reindex(neg_by_slot.index)
    all_tv = sorted(set(tc.index.get_level_values("village_id")))
    neg_by_slot = neg_by_slot.reindex(all_tv, fill_value=0)
    cnt = cnt.reindex(all_tv, fill_value=0).to_numpy()
    negs = neg_by_slot.to_numpy()
    wins = np.zeros(len(slots), dtype=int)
    for _ in range(draws):
        idx = rng.integers(0, len(all_tv), size=len(all_tv))
        d = cnt[idx].sum()
        if d == 0:
            continue
        miss = negs[idx].sum(axis=0) / d
        wins[int(np.flatnonzero(np.isclose(miss, miss.min()))[0])] += 1

    ec = test.dropna()
    epos = ec[ec.sum(axis=1) > 0]
    ev = epos.index.get_level_values("village_id")
    all_ev = sorted(set(ec.index.get_level_values("village_id")))
    k = epos.sum(axis=1)
    g = pd.DataFrame({"n": 1, "frozen": (epos[rule.slot] == 0).astype(int),
                      "rand": (ec.shape[1] - k) / ec.shape[1]}).groupby(ev).sum().reindex(all_ev, fill_value=0)
    G = g.to_numpy(dtype=float)
    reps = np.full((draws, 3), np.nan)
    for b in range(draws):
        idx = rng.integers(0, len(all_ev), size=len(all_ev))
        tot = G[idx].sum(axis=0)
        if tot[0] > 0:
            reps[b] = [tot[1] / tot[0], tot[2] / tot[0], (tot[1] - tot[2]) / tot[0]]
    lo = np.nanquantile(reps, 0.025, axis=0)
    hi = np.nanquantile(reps, 0.975, axis=0)
    return {
        "selection_frequency": {int(s): float(w / draws) for s, w in zip(slots, wins)},
        "test_frozen_ci": (float(lo[0]), float(hi[0])),
        "test_random_ci": (float(lo[1]), float(hi[1])),
        "test_difference_ci": (float(lo[2]), float(hi[2])),
        "test_zero_denominator_draws": int(np.isnan(reps[:, 0]).sum()),
        "draws": draws,
        "seed": seed,
    }
