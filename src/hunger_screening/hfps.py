"""External-data analyses with the World Bank Malawi High-Frequency Phone Survey 2020-2024.

Source: Malawi High-Frequency Phone Survey 2020-2024, version 20, World Bank Microdata
Library catalog 3766, doi:10.48529/s2n6-9f47. Public-use files: aggregates may be
published with citation; microdata, household identifiers and household-level
intermediates are never written outside data/raw (gitignored).

Measurement. The food-security module is the 8-item FIES with a 30-day recall ("During
the last 30 days, was there a time when you, or others in your household, ..."). The
primary item s8q7 ("hungry but did not eat") and secondary item s8q8 ("went without
eating for a whole day") are *not* HHS items; results are related-item triangulation,
not an HHS replication. Rounds 20-21 add HHS-style frequency follow-ups for items 6-8.

Design facts verified in this module's audit: no refreshment sample (all panel
households enter in round 1); later rounds alternate Sample_Type A/B; fieldwork per
round lasts 1-3 weeks; the public files contain no PSU or stratum, so cluster
resampling uses districts (coarse and not survey-design-correct) alongside households.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from fractions import Fraction
from math import floor
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import history_bounds as hb
from . import schedule_metrics as sm
from .config import Paths
from .provenance import sha256_file, utc_now

log = logging.getLogger("hunger_screening.hfps")
ITEMS = [f"s8q{i}" for i in range(1, 9)]
FREQ = ["s8q6a", "s8q7a", "s8q8a"]


def load_investigation_config(paths: Paths) -> dict:
    with open(paths.root / "config" / "investigation.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _norm(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: "HHID" for c in df.columns if c.lower() == "hhid"})


@dataclass
class HFPS:
    long: pd.DataFrame      # one row per household-round with food-security data
    static: pd.DataFrame    # one row per panel household: district, region, urban, wealth
    attempts: pd.DataFrame  # per round: logged call attempts for completed interviews
    labels: dict[int, str]
    unlinked_records: int   # food-security records without a cover-page match


def load(cfg: dict, root: Path) -> HFPS:
    d = root / cfg["extracted_dir"]
    yes, no = cfg["yes_code"], cfg["no_code"]
    frames, att = [], []
    unlinked = 0
    for r in cfg["food_security_rounds"]:
        fs = _norm(pd.read_stata(d / f"sect8_food_security_r{r}.dta", convert_categoricals=False))
        cv = _norm(pd.read_stata(d / f"secta_cover_page_r{r}.dta", convert_categoricals=False))
        wcol = next(c for c in cv.columns if c.startswith("wt_"))
        cv = cv[["HHID", "y4_hhid", "interviewDate", wcol]].rename(columns={wcol: "weight", "y4_hhid": "y4_cover"})
        m = fs.merge(cv, on="HHID", how="left", validate="one_to_one", indicator=True)
        unlinked += int(((m["_merge"] != "both") | (m["y4_cover"] != m["y4_hhid"])).sum())
        out = pd.DataFrame({"hh": m["y4_hhid"].astype(str), "round": r,
                            "date": pd.to_datetime(m["interviewDate"], errors="coerce").dt.normalize(),
                            "weight": m["weight"].astype(float)})
        for c in ITEMS:
            v = m[c]
            out[c] = np.where(v == yes, 1.0, np.where(v == no, 0.0, np.nan))
        for c in FREQ:
            out[c] = m[c].astype(float) if c in m else np.nan
        out["sample_type"] = m["Sample_Type"].astype(float) if "Sample_Type" in m else np.nan
        frames.append(out)
        f1 = d / f"sect1_interview_info_r{r}.dta"
        if f1.exists():
            ii = pd.read_stata(f1, convert_categoricals=False, columns=["y4_hhid"])
            att.append({"round": r, "attempt_rows": len(ii), "households_in_attempt_log": ii.y4_hhid.nunique(),
                        "completed_interviews": len(fs)})
    long = pd.concat(frames, ignore_index=True)
    cv1 = pd.read_stata(d / "secta_cover_page_r1.dta", convert_categoricals=False)
    static = pd.DataFrame({"hh": cv1["y4_hhid"].astype(str), "region": cv1["hh_a00"].astype(int),
                           "district": cv1["hh_a01"].astype(int), "urban": (cv1["urb_rural"] == 1).astype(int)})
    ai = pd.read_stata(d / "asset_index_panel_2019.dta", convert_categoricals=False)
    static = static.merge(ai.rename(columns={"y4_hhid": "hh", "wealthquintile": "wealth_quintile"}),
                          on="hh", how="left", validate="one_to_one")
    static = static[static.hh.isin(long.hh)].set_index("hh")
    grp = long.dropna(subset=["sample_type"]).groupby("hh").sample_type.agg(["min", "max"])
    if (grp["min"] != grp["max"]).any():
        raise ValueError("Sample_Type not constant within household")
    static["sample_type"] = grp["min"].reindex(static.index)
    attempts = pd.DataFrame(att)
    attempts["attempts_per_completed_interview"] = attempts.attempt_rows / attempts.completed_interviews
    med = long.groupby("round").date.median()
    labels = {r: f"R{r} {med[r]:%b %Y}" for r in med.index}
    return HFPS(long, static, attempts, labels, unlinked)


def matrix(h: HFPS, rounds: list[int], item: str, households=None) -> pd.DataFrame:
    sub = h.long[h.long["round"].isin(rounds)]
    mat = sub.pivot(index="hh", columns="round", values=item).reindex(columns=rounds)
    if households is not None:
        mat = mat.reindex(households)
    return mat


# ---------------------------------------------------------------- audit
def audit(h: HFPS) -> dict[str, pd.DataFrame]:
    L = h.long
    rows = []
    for r, g in L.groupby("round"):
        row = {"round": r, "label": h.labels[r], "records": len(g), "fieldwork_start": g.date.min().date(),
               "fieldwork_end": g.date.max().date(), "date_missing": int(g.date.isna().sum()),
               "sample_type": "/".join(sorted({"A" if x == 1 else "B" for x in g.sample_type.dropna()})) or "all"}
        for c in ("s8q7", "s8q8"):
            row[f"{c}_valid"] = int(g[c].notna().sum())
            row[f"{c}_yes"] = int((g[c] == 1).sum())
            row[f"{c}_missing"] = int(g[c].isna().sum())
        rows.append(row)
    rounds = pd.DataFrame(rows)
    rounds = rounds.merge(h.attempts, on="round", how="left")
    ids = {r: set(g.hh) for r, g in L.groupby("round")}
    sets = {
        "all 15 food-security rounds (any)": set(L.hh),
        "2020 rounds 1,2,3,5,6 (all five)": set.intersection(*(ids[r] for r in (1, 2, 3, 5, 6))),
        "2021 rounds 7,9,11 (all three)": set.intersection(*(ids[r] for r in (7, 9, 11))),
        "2021 rounds 7,8,9,11,12 (all five)": set.intersection(*(ids[r] for r in (7, 8, 9, 11, 12))),
        "rounds 19 and 20": ids[19] & ids[20],
        "rounds 20 and 21": ids[20] & ids[21],
        "rounds 19 and 21": ids[19] & ids[21],
        "rounds 18,19,21 (group B horizon)": ids[18] & ids[19] & ids[21],
        "rounds 18,20 (group A horizon)": ids[18] & ids[20],
    }
    overlap = pd.DataFrame({"set": list(sets), "households": [len(v) for v in sets.values()]})
    integrity = pd.DataFrame([
        {"check": "household id unique within every round", "pass": bool(not L.duplicated(["hh", "round"]).any())},
        {"check": "every food-security record links one-to-one to a cover-page record with the same panel id",
         "pass": h.unlinked_records == 0},
        {"check": "no refreshment sample: every household appears in round 1",
         "pass": bool(set(L.hh) <= ids[1])},
        {"check": "Sample_Type constant within household (load() raises otherwise)", "pass": True},
        {"check": "rounds 19/21 vs 20 have disjoint households", "pass": len(ids[19] & ids[20]) == 0 and len(ids[20] & ids[21]) == 0},
        {"check": "items coded only YES/NO/missing after recode", "pass": bool(L[ITEMS].isin([0.0, 1.0]).sum().sum() + L[ITEMS].isna().sum().sum() == L[ITEMS].size)},
    ])
    return {"rounds": rounds, "overlap": overlap, "integrity": integrity}


def date_gaps(h: HFPS, pairs: list[tuple[int, int]]) -> pd.DataFrame:
    d = h.long.pivot(index="hh", columns="round", values="date")
    rows = []
    for a, b in pairs:
        g = (d[b] - d[a]).dt.days.dropna()
        rows.append({"from_round": a, "to_round": b, "households_with_both_dates": int(g.size),
                     "median_days": float(g.median()), "p05_days": float(g.quantile(0.05)),
                     "p95_days": float(g.quantile(0.95)), "share_under_30_days": float((g < 30).mean()),
                     "min_days": int(g.min()), "max_days": int(g.max())})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- core tables
def single_round_table(h: HFPS, rounds: list[int], item: str, boot: dict, weighted_round: int | None = None,
                       cohort_label: str = "") -> pd.DataFrame:
    mat = sm.binary_complete(matrix(h, rounds, item))
    H = mat.to_numpy()
    hhs = mat.index
    dist = h.static.loc[hhs, "district"].to_numpy()
    n = len(rounds)
    rmiss, pos = sm.household_terms(H, m=1)
    stats = {"random": (rmiss, pos)}
    for j, r in enumerate(rounds):
        stats[f"r{r}"] = (sm.household_terms(H, schedule=[j])[0], pos)
    reps_d, _ = sm.ratio_bootstrap(dist, stats, boot["draws"], boot["seed"])
    reps_h, _ = sm.ratio_bootstrap(np.arange(len(hhs)), stats, boot["draws"], boot["seed"])
    w = None
    if weighted_round is not None:
        w = h.long[h.long["round"] == weighted_round].set_index("hh").weight.reindex(hhs).to_numpy()
    rows = []
    for j, r in enumerate(rounds + ["random"]):
        key = "random" if r == "random" else f"r{r}"
        row = sm.random_row(H, 1) if r == "random" else sm.schedule_row(H, [j], [h.labels[x] for x in rounds])
        if r == "random":
            row["schedule"] = f"random 1 of {n}"
        lo, hi = sm.interval(reps_d[key], boot["level"])
        hlo, hhi = sm.interval(reps_h[key], boot["level"])
        row.update({"cohort": cohort_label, "item": item, "missed_ci_district_low": lo, "missed_ci_district_high": hi,
                    "missed_ci_household_low": hlo, "missed_ci_household_high": hhi})
        if r != "random":
            dd = reps_d[key] - reps_d["random"]
            dh = reps_h[key] - reps_h["random"]
            row["diff_vs_random"] = row["missed_share"] - (rmiss.sum() / pos.sum())
            row["diff_ci_district_low"], row["diff_ci_district_high"] = sm.interval(dd, boot["level"])
            row["diff_ci_household_low"], row["diff_ci_household_high"] = sm.interval(dh, boot["level"])
        if w is not None:
            num = stats[key][0]
            row["weighted_missed_share"] = float((w * num).sum() / (w * pos).sum())
            row["weight_variable_round"] = weighted_round
        rows.append(row)
    return pd.DataFrame(rows)


def frontier_table(h: HFPS, rounds: list[int], item: str, cohort_label: str) -> pd.DataFrame:
    H = sm.binary_complete(matrix(h, rounds, item)).to_numpy()
    rows = []
    for m in range(1, len(rounds) + 1):
        r = sm.random_row(H, m)
        r.update({"cohort": cohort_label, "item": item, "m": m})
        rows.append(r)
    return pd.DataFrame(rows)


def schedules_table(h: HFPS, rounds: list[int], item: str, cohort_label: str, budgets=(1, 2)) -> pd.DataFrame:
    mat = sm.binary_complete(matrix(h, rounds, item))
    H = mat.to_numpy()
    labels = [h.labels[r] for r in rounds]
    df = sm.all_schedules(H, labels, budgets)
    apc = h.attempts.set_index("round").attempts_per_completed_interview
    att = []
    for s in df.schedule:
        if s.startswith("random"):
            att.append(np.nan)
            continue
        rs = [rounds[labels.index(x)] for x in s.split(" + ")]
        att.append(sum(apc.get(r, np.nan) for r in rs))
    df["logged_attempts_per_household"] = att
    ident = df.identified_per_100_households / 100 * df.n_complete
    df["identified_per_100_logged_attempts"] = 100 * ident / (df.logged_attempts_per_household * df.n_complete)
    df.insert(0, "item", item)
    df.insert(0, "cohort", cohort_label)
    return df


def saturation(h: HFPS, rounds: list[int], item: str) -> pd.DataFrame:
    H = sm.binary_complete(matrix(h, rounds, item)).to_numpy()
    rows = []
    for j in range(len(rounds)):
        rows.append({"rounds_included": j + 1, "through_round": h.labels[rounds[j]], "n_complete": H.shape[0],
                     "point_prevalence_this_round": float(H[:, j].mean()),
                     "ever_positive_share": float(H[:, : j + 1].max(axis=1).mean()), "item": item})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- transfer tests
def select_candidate(train: np.ndarray, order: list[int]) -> tuple[int, list[float]]:
    """Index of the column with the lowest missed share (ties -> earliest in ``order``).

    Only training data enter this function; it is the single selection step.
    """
    pos = train.max(axis=1) > 0
    miss = [float((train[pos, j] == 0).mean()) for j in range(train.shape[1])]
    best = min(order, key=lambda j: (miss[j], order.index(j)))
    return best, miss


def transfer_test(h: HFPS, name: str, item: str, cand: list[str], train_rounds: list[int],
                  test_rounds: list[int], boot: dict, test_group: float | None = None,
                  train_group: float | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    trm = sm.binary_complete(matrix(h, train_rounds, item))
    if train_group is not None:
        trm = trm[h.static.loc[trm.index, "sample_type"] == train_group]
    train = trm.to_numpy()
    tdates = [h.long[h.long["round"] == r].date.median() for r in train_rounds]
    order = list(np.argsort(tdates))
    sel, train_miss = select_candidate(train, [int(x) for x in order])
    tem = sm.binary_complete(matrix(h, test_rounds, item))
    if test_group is not None:
        tem = tem[h.static.loc[tem.index, "sample_type"] == test_group]
    test = tem.to_numpy()
    tpos = test.max(axis=1) > 0
    dist = h.static.loc[tem.index, "district"].to_numpy()
    rmiss, pos = sm.household_terms(test, m=1)
    stats = {"random": (rmiss, pos)}
    for j in range(len(cand)):
        stats[cand[j]] = (sm.household_terms(test, schedule=[j])[0], pos)
    reps, zero = sm.ratio_bootstrap(dist, stats, boot["draws"], boot["seed"])
    rows = []
    for j, c in enumerate(cand):
        miss = float((test[tpos, j] == 0).mean())
        lo, hi = sm.interval(reps[c], boot["level"])
        dlo, dhi = sm.interval(reps[c] - reps["random"], boot["level"])
        rows.append({"test": name, "item": item, "candidate": c, "train_round": train_rounds[j],
                     "test_round": test_rounds[j], "train_missed": train_miss[j], "selected_on_train": j == sel,
                     "n_train_complete": train.shape[0], "n_train_reference_positive": int((train.max(axis=1) > 0).sum()),
                     "n_test_complete": test.shape[0], "n_test_reference_positive": int(tpos.sum()),
                     "test_missed": miss, "test_missed_ci_low": lo, "test_missed_ci_high": hi,
                     "test_random_missed": float(rmiss.sum() / pos.sum()),
                     "diff_vs_random": miss - float(rmiss.sum() / pos.sum()),
                     "diff_ci_low": dlo, "diff_ci_high": dhi,
                     "test_group": {1.0: "A", 2.0: "B"}.get(test_group, "all"),
                     "train_group": {1.0: "A", 2.0: "B"}.get(train_group, "all"),
                     "zero_denominator_draws": zero[c]})
    # selection stability: district bootstrap of the training data only
    tdist = h.static.loc[trm.index, "district"].to_numpy()
    uniq = np.unique(tdist)
    rng = np.random.default_rng(boot["seed"] + 1)
    counts = np.zeros(len(cand))
    for _ in range(boot["draws"]):
        pick = rng.choice(uniq, size=uniq.size, replace=True)
        idx = np.concatenate([np.flatnonzero(tdist == u) for u in pick])
        s, _ = select_candidate(train[idx], [int(x) for x in order])
        counts[s] += 1
    stab = pd.DataFrame({"test": name, "item": item, "candidate": cand,
                         "selection_frequency": counts / boot["draws"], "draws": boot["draws"]})
    return pd.DataFrame(rows), stab


# ---------------------------------------------------------------- who is missed
def subgroup_table(h: HFPS, rounds: list[int], item: str, boot: dict, min_pos: int, fixed_index: int = 0) -> pd.DataFrame:
    mat = sm.binary_complete(matrix(h, rounds, item))
    H = mat.to_numpy()
    st = h.static.loc[mat.index]
    dist = st.district.to_numpy()
    fmiss, pos = sm.household_terms(H, schedule=[fixed_index])
    rmiss, _ = sm.household_terms(H, m=1)
    groups = {"all": np.ones(len(st), bool)}
    groups.update({f"urban={u}": (st.urban == u).to_numpy() for u in (1, 0)})
    groups.update({f"wealth_quintile={q}": (st.wealth_quintile == q).to_numpy() for q in range(1, 6)})
    groups.update({f"region={g}": (st.region == g).to_numpy() for g in (100, 200, 300)})
    stats = {}
    for g, msk in groups.items():
        stats[f"{g}|fixed"] = (fmiss * msk, pos * msk)
        stats[f"{g}|random"] = (rmiss * msk, pos * msk)
    reps, zero = sm.ratio_bootstrap(dist, stats, boot["draws"], boot["seed"])
    names = {"urban=1": "Urban", "urban=0": "Rural", "region=100": "North", "region=200": "Central",
             "region=300": "Southern"}
    rows = []
    for g, msk in groups.items():
        npos = int(pos[msk].sum())
        f = fmiss[msk].sum() / npos if npos else np.nan
        r = rmiss[msk].sum() / npos if npos else np.nan
        d = reps[f"{g}|fixed"] - reps[f"{g}|random"]
        rows.append({"item": item, "group": names.get(g, g), "n_complete": int(msk.sum()), "n_reference_positive": npos,
                     "reference_positive_share": npos / msk.sum() if msk.sum() else np.nan,
                     "fixed_round": h.labels[rounds[fixed_index]], "fixed_missed": f, "random_missed": r,
                     "diff_vs_random": f - r,
                     "fixed_ci_low": sm.interval(reps[f"{g}|fixed"], boot["level"])[0],
                     "fixed_ci_high": sm.interval(reps[f"{g}|fixed"], boot["level"])[1],
                     "diff_ci_low": sm.interval(d, boot["level"])[0], "diff_ci_high": sm.interval(d, boot["level"])[1],
                     "small_cell_flag": npos < min_pos, "zero_denominator_draws": zero[f"{g}|fixed"]})
    out = pd.DataFrame(rows)
    q1 = reps["wealth_quintile=1|fixed"] - reps["wealth_quintile=1|random"]
    q5 = reps["wealth_quintile=5|fixed"] - reps["wealth_quintile=5|random"]
    gap = q1 - q5
    lo, hi = sm.interval(gap, boot["level"])
    pt = out.set_index("group").diff_vs_random
    out = pd.concat([out, pd.DataFrame([{"item": item, "group": "Q1 minus Q5 (difference in diff_vs_random)",
                                         "diff_vs_random": pt["wealth_quintile=1"] - pt["wealth_quintile=5"],
                                         "diff_ci_low": lo, "diff_ci_high": hi}])], ignore_index=True)
    return out


# ---------------------------------------------------------------- decision robustness
def robustness(h: HFPS, rounds: list[int], item: str, fixed_index: int, alphas: list[float], label: str) -> pd.DataFrame:
    mat = matrix(h, rounds, item)
    mat = mat[mat.notna().any(axis=1)]
    H = mat.fillna(-1).astype(int).to_numpy()
    n = len(rounds)
    c = hb.fixed_minus_random([fixed_index], n, 1)
    observed_screens = int((H >= 0).sum())
    point = hb.observed_value(H, c)
    rows = []
    b0 = hb.contrast_bounds(H, c, 0)
    rows.append({"analysis": label, "item": item, "fixed_round": h.labels[rounds[fixed_index]],
                 "frame_households": H.shape[0], "households_with_missing": int((H < 0).any(axis=1).sum()),
                 "observed_screens": observed_screens, "alpha": 0.0, "flip_budget": 0,
                 "complete_case_diff": float(point), "lower": float(b0["lower"].value), "upper": float(b0["upper"].value),
                 "lower_exact": str(b0["lower"].value), "upper_exact": str(b0["upper"].value),
                 "certificate_lower": b0["lower"].certificate_F, "certificate_upper": b0["upper"].certificate_F})
    for a in alphas:
        B = floor(a * observed_screens)
        b = hb.contrast_bounds(H, c, B)
        rows.append({**rows[0], "alpha": a, "flip_budget": B, "lower": float(b["lower"].value),
                     "upper": float(b["upper"].value), "lower_exact": str(b["lower"].value),
                     "upper_exact": str(b["upper"].value), "certificate_lower": b["lower"].certificate_F,
                     "certificate_upper": b["upper"].certificate_F})
    tip = hb.tipping_budget(H, c, "max", Fraction(0))
    out = pd.DataFrame(rows)
    out["tipping_budget_to_reach_zero"] = tip
    out["tipping_budget_share_of_observed_screens"] = tip / observed_screens if tip is not None else np.nan
    return out


# ---------------------------------------------------------------- measurement triangulation
def hhs_analogue(h: HFPS, rounds: list[int]) -> pd.DataFrame:
    rows = []
    for r in rounds:
        g = h.long[h.long["round"] == r]
        parts = []
        for occ, fq in (("s8q6", "s8q6a"), ("s8q7", "s8q7a"), ("s8q8", "s8q8a")):
            p = np.where(g[occ] == 0, 0.0,
                         np.where((g[occ] == 1) & g[fq].isin([1, 2]), 1.0,
                                  np.where((g[occ] == 1) & (g[fq] == 3), 2.0, np.nan)))
            parts.append(p)
        score = np.sum(parts, axis=0)
        ok = ~np.isnan(score) & g.s8q7.notna().to_numpy()
        s = score[ok]
        q7 = g.s8q7.to_numpy()[ok]
        f7 = g.s8q7a.to_numpy()[ok]
        rows.append({"round": r, "label": h.labels[r], "valid_households": int(ok.sum()),
                     "s8q7_yes_share": float(q7.mean()),
                     "hhs_analogue_ge2_share": float((s >= 2).mean()),
                     "hhs_analogue_ge4_share": float((s >= 4).mean()),
                     "share_of_s8q7_yes_with_analogue_ge2": float((s[q7 == 1] >= 2).mean()),
                     "share_of_analogue_ge2_with_s8q7_yes": float((q7[s >= 2] == 1).mean()),
                     "s8q7_yes_freq_rarely": float((f7[q7 == 1] == 1).mean()),
                     "s8q7_yes_freq_sometimes": float((f7[q7 == 1] == 2).mean()),
                     "s8q7_yes_freq_often": float((f7[q7 == 1] == 3).mean())})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- second-contact rule
def second_contact(first: np.ndarray, later: np.ndarray, warning: np.ndarray, poverty_rank: np.ndarray,
                   clusters: np.ndarray, boot: dict, label: str) -> pd.DataFrame:
    """Compare rules for choosing which first-contact negatives to keep re-contacting.

    first: 0/1 primary outcome at first contact; later: households x later rounds (0/1);
    warning: bool milder-signal at first contact; poverty_rank: smaller = poorer (ties allowed).
    Budget = number of warning-sign negatives. Random and poverty rules use exact
    expectations (ties split proportionally), so no simulation noise enters.
    """
    neg = first == 0
    later_pos = later.max(axis=1) > 0
    W = int((neg & warning).sum())
    n_neg = int(neg.sum())
    base = later_pos[neg].mean()
    capt_warn = int((neg & warning & later_pos).sum())
    # poverty rule: fill budget from poorest upward; split the boundary rank proportionally
    ranks = poverty_rank[neg]
    lp = later_pos[neg]
    exp_pov = 0.0
    left = W
    for q in np.unique(ranks):
        sel = ranks == q
        k = int(sel.sum())
        take = min(left, k)
        exp_pov += take * lp[sel].mean() if k else 0.0
        left -= take
        if left == 0:
            break
    rows = [{"analysis": label, "rule": rule, "first_contact_negatives": n_neg, "recontact_budget_households": W,
             "later_positive_among_negatives": int(lp.sum()), "expected_captured": cap,
             "captured_per_100_recontacted": 100 * cap / W if W else np.nan,
             "share_of_later_positives_captured": cap / lp.sum() if lp.sum() else np.nan,
             "recontacts_used": W * later.shape[1]}
            for rule, cap in (("warning-sign (milder item positive at first contact)", float(capt_warn)),
                              ("random among negatives (exact expectation)", float(W * base)),
                              ("poorest first by baseline wealth (exact expectation)", float(exp_pov)))]
    # paired cluster bootstrap for warning minus random precision
    stats = {"warn": ((neg & warning & later_pos).astype(float), (neg & warning).astype(float)),
             "base": ((neg & later_pos).astype(float), neg.astype(float))}
    reps, _ = sm.ratio_bootstrap(clusters, stats, boot["draws"], boot["seed"])
    lo, hi = sm.interval(100 * (reps["warn"] - reps["base"]), boot["level"])
    out = pd.DataFrame(rows)
    out["warning_minus_random_per_100_ci_low"] = lo
    out["warning_minus_random_per_100_ci_high"] = hi
    return out


def hfps_second_contact(h: HFPS, item: str, first_round: int, later_rounds: list[int], milder: list[str],
                        boot: dict, label: str) -> pd.DataFrame:
    rounds = [first_round] + later_rounds
    mat = sm.binary_complete(matrix(h, rounds, item))
    f = h.long[h.long["round"] == first_round].set_index("hh")[milder].reindex(mat.index)
    keep = f.notna().all(axis=1) & h.static.loc[mat.index, "wealth_quintile"].notna()
    mat, f = mat[keep], f[keep]
    H = mat.to_numpy()
    warning = (f.to_numpy() == 1).any(axis=1)
    pr = h.static.loc[mat.index, "wealth_quintile"].to_numpy()
    out = second_contact(H[:, 0], H[:, 1:], warning, pr, h.static.loc[mat.index, "district"].to_numpy(), boot, label)
    out.insert(1, "item", item)
    out.insert(2, "warning_items", ",".join(milder))
    return out


def _top_budget_expected(score: np.ndarray, y: np.ndarray, budget: int) -> float:
    """Expected captured positives when the ``budget`` highest scores are chosen (ties split)."""
    order = np.unique(score)[::-1]
    got, left = 0.0, budget
    for s in order:
        sel = score == s
        k = int(sel.sum())
        take = min(left, k)
        got += take * y[sel].mean()
        left -= take
        if left == 0:
            break
    return got


def _features(h: HFPS, hhs: pd.Index, first_round: int, milder: list[str]) -> np.ndarray:
    f = h.long[h.long["round"] == first_round].set_index("hh")[milder].reindex(hhs).to_numpy()
    st = h.static.loc[hhs]
    return np.column_stack([np.ones(len(hhs)), f, st.wealth_quintile.to_numpy(), st.urban.to_numpy(),
                            (st.region == 100).to_numpy(), (st.region == 300).to_numpy()]).astype(float)


def model_vs_rule(h: HFPS, item: str, milder: list[str], train: tuple[int, list[int]],
                  test: tuple[int, list[int]]) -> pd.DataFrame:
    """Time-held-out check: does a logistic score beat the one-line warning-sign rule?

    The model is fitted on an earlier first-contact/later-rounds problem (2020) using only
    information available at first contact, then applied unchanged to the 2021 problem.
    All rules get the same re-contact budget (number of warning-sign negatives in 2021).
    """
    from .optional_diagnostics import _logit_irls

    def problem(first, later):
        mat = sm.binary_complete(matrix(h, [first] + later, item))
        f = h.long[h.long["round"] == first].set_index("hh")[milder].reindex(mat.index)
        keep = f.notna().all(axis=1) & h.static.loc[mat.index, "wealth_quintile"].notna()
        mat = mat[keep]
        H = mat.to_numpy()
        neg = H[:, 0] == 0
        idx = mat.index[neg]
        return idx, (H[neg, 1:].max(axis=1) > 0).astype(float), (f[keep].to_numpy()[neg] == 1)

    tr_idx, tr_y, _ = problem(*train)
    te_idx, te_y, te_mild = problem(*test)
    beta = _logit_irls(_features(h, tr_idx, train[0], milder), tr_y, ridge=1e-3)
    score = _features(h, te_idx, test[0], milder) @ beta
    anym = te_mild.any(axis=1).astype(float)
    W_full = int(anym.sum())
    rows = []
    # At the full budget every rule that ranks warning-sign households first selects the same
    # set, so the half budget is where ranking within that set can matter.
    for label, W in (("budget = all warning-sign negatives", W_full), ("budget = half of them", W_full // 2)):
        for rule, cap in (("warning-sign rule (any milder item; ties split)", _top_budget_expected(anym, te_y, W)),
                          ("graded rule (number of milder items, highest first)", _top_budget_expected(te_mild.sum(axis=1).astype(float), te_y, W)),
                          ("logistic score trained on 2020 (milder items, wealth, urban, region)", _top_budget_expected(np.round(score, 12), te_y, W)),
                          ("random among negatives (exact expectation)", W * te_y.mean())):
            rows.append({"item": item, "train_problem": f"first R{train[0]}, later " + "/".join(f"R{r}" for r in train[1]),
                         "test_problem": f"first R{test[0]}, later " + "/".join(f"R{r}" for r in test[1]),
                         "n_train_negatives": len(tr_idx), "n_test_negatives": len(te_idx), "budget_definition": label,
                         "recontact_budget": W, "rule": rule, "expected_captured": cap,
                         "captured_per_100_recontacted": 100 * cap / W})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- runner
def run(paths: Paths | None = None) -> dict:
    paths = paths or Paths()
    icfg = load_investigation_config(paths)
    cfg = icfg["hfps"]
    out = paths.public / "investigation"
    out.mkdir(parents=True, exist_ok=True)
    archive = paths.root / cfg["archive"]
    digest = sha256_file(archive)
    if digest != cfg["expected_sha256"]:
        raise RuntimeError(f"HFPS archive checksum mismatch: {digest}")
    if not (paths.root / cfg["extracted_dir"]).exists():
        raise FileNotFoundError("extract the HFPS archive into " + cfg["extracted_dir"])
    h = load(cfg, paths.root)
    boot = cfg["bootstrap"]
    A = cfg["analyses"]
    summary = {"generated_utc": utc_now(), "archive_sha256": digest, "archive_bytes": archive.stat().st_size,
               "catalog": cfg["catalog_url"], "doi": cfg["doi"]}

    au = audit(h)
    au["rounds"].to_csv(out / "hfps_round_audit.csv", index=False)
    au["overlap"].to_csv(out / "hfps_household_overlap.csv", index=False)
    au["integrity"].to_csv(out / "hfps_integrity_checks.csv", index=False)
    date_gaps(h, [(1, 2), (2, 3), (3, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 11), (11, 12), (7, 9), (7, 11),
                  (16, 18), (18, 19), (19, 21), (18, 20)]).to_csv(out / "hfps_interview_gaps.csv", index=False)
    summary["panel_households"] = int(h.long.hh.nunique())
    summary["records"] = int(len(h.long))

    singles, fronts, scheds, sats, rob, subs, trans, stabs, sc, mvr = [], [], [], [], [], [], [], [], [], []
    for item in (cfg["primary_item"], cfg["secondary_item"]):
        r3 = A["reproduce_2021"]
        r5 = A["five_round_2021"]
        singles.append(single_round_table(h, r3, item, boot, weighted_round=r3[-1], cohort_label="2021 rounds 7/9/11"))
        singles.append(single_round_table(h, r5, item, boot, weighted_round=r5[-1], cohort_label="2021 rounds 7/8/9/11/12"))
        singles.append(single_round_table(h, A["train_2020"], item, boot, weighted_round=A["train_2020"][-1],
                                          cohort_label="2020 rounds 1/2/3/5/6"))
        for rr, lab in ((r3, "2021 rounds 7/9/11"), (r5, "2021 rounds 7/8/9/11/12"), (A["train_2020"], "2020 rounds 1/2/3/5/6")):
            fronts.append(frontier_table(h, rr, item, lab))
            scheds.append(schedules_table(h, rr, item, lab))
        sats.append(saturation(h, A["train_2020"] + r5, item))
        rob.append(robustness(h, r3, item, 0, cfg["label_error_alphas"], "2021 rounds 7/9/11: R7 vs random"))
        rob.append(robustness(h, r5, item, 0, cfg["label_error_alphas"], "2021 rounds 7/8/9/11/12: R7 vs random"))
        subs.append(subgroup_table(h, r3, item, boot, cfg["min_reference_positives_for_subgroup"]))
        # transfer tests
        tr = A["train_2020"]
        cand = [h.labels[r] for r in tr]
        trm = sm.binary_complete(matrix(h, tr, item)).to_numpy()
        tdates = [h.long[h.long["round"] == r].date.median() for r in tr]
        sel, miss = select_candidate(trm, [int(x) for x in np.argsort(tdates)])
        target = {1: A["transfer_target_2021_round"]}.get(tr[sel])
        rows = [{"test": "HFPS 2020 -> 2021 (reproduction)", "item": item, "candidate": cand[j], "train_round": tr[j],
                 "train_missed": miss[j], "selected_on_train": j == sel, "n_train_complete": trm.shape[0],
                 "n_train_reference_positive": int((trm.max(axis=1) > 0).sum()),
                 "test_round": target if j == sel else np.nan} for j in range(len(tr))]
        t21 = single_round_table(h, r3, item, boot, cohort_label="2021 rounds 7/9/11")
        if target is not None:
            hit = t21[t21.schedule == h.labels[target]].iloc[0]
            for row in rows:
                if row["selected_on_train"]:
                    row.update({"n_test_complete": hit.n_complete, "n_test_reference_positive": hit.n_reference_positive,
                                "test_missed": hit.missed_share, "test_missed_ci_low": hit.missed_ci_district_low,
                                "test_missed_ci_high": hit.missed_ci_district_high,
                                "test_random_missed": float(t21[t21.schedule.str.startswith("random")].missed_share.iloc[0]),
                                "diff_vs_random": hit.diff_vs_random, "diff_ci_low": hit.diff_ci_district_low,
                                "diff_ci_high": hit.diff_ci_district_high})
        trans.append(pd.DataFrame(rows))
        gB, gA = A["matched_groupB"], A["matched_groupA"]
        for nm, trr, grp_train in (("HFPS matched Jun/Dec/Apr, 2020-21 -> 2023-24, group B", gB["train"], None),
                                   ("HFPS matched (train: group-B households only)", gB["train"], gB["test_sample_type"]),
                                   ("HFPS matched, training June = round 11 (pandemic-onset round excluded)", gB["train_variant"], None)):
            t, s = transfer_test(h, nm, item, gB["candidates"], trr, gB["test"], boot, gB["test_sample_type"], grp_train)
            trans.append(t)
            stabs.append(s)
        t, s = transfer_test(h, "HFPS matched Jun/Feb-Mar, 2020-21 -> 2023-24, group A", item, gA["candidates"],
                             gA["train"], gA["test"], boot, gA["test_sample_type"])
        trans.append(t)
        stabs.append(s)
        sc.append(hfps_second_contact(h, item, 7, [9, 11], cfg["milder_items"], boot, "HFPS 2021: first contact R7, later R9/R11"))
        sc.append(hfps_second_contact(h, item, 7, [8, 9, 11, 12], cfg["milder_items"], boot,
                                      "HFPS 2021: first contact R7, later R8/R9/R11/R12"))
        mvr.append(model_vs_rule(h, item, cfg["milder_items"], (2, [3, 5]), (7, [9, 11])))
    pd.concat(singles).to_csv(out / "hfps_single_round.csv", index=False)
    pd.concat(fronts).to_csv(out / "hfps_frontier.csv", index=False)
    pd.concat(scheds).to_csv(out / "hfps_fixed_schedules.csv", index=False)
    pd.concat(sats).to_csv(out / "hfps_saturation.csv", index=False)
    pd.concat(rob).to_csv(out / "hfps_decision_robustness.csv", index=False)
    pd.concat(subs).to_csv(out / "hfps_subgroups.csv", index=False)
    pd.concat(trans).to_csv(out / "hfps_transfer_tests.csv", index=False)
    pd.concat(stabs).to_csv(out / "hfps_transfer_selection_stability.csv", index=False)
    pd.concat(sc).to_csv(out / "hfps_second_contact.csv", index=False)
    pd.concat(mvr).to_csv(out / "hfps_model_vs_rule.csv", index=False)
    hhs_analogue(h, A["hhs_analogue_rounds"]).to_csv(out / "hfps_hhs_analogue.csv", index=False)
    with open(out / "hfps_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)
    return summary
