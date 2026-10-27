"""Analyses answering the external review of 27 October 2026 (see reports/REVIEW_RESPONSE.md).

1. scoring_check      - is the supplied HHS standard frequency-weighted scoring or an occurrence count?
2. calendar_lean      - externally justified, calendar-based sensitivity analysis: the two-month window
                        with most months in the FEWS NET lean season, against six-window references.
                        Run after the exploratory findings, so it is not blind or prespecified.
3. second_scope       - missing-history bounds excluding never-contacted households
4. frozen_pair        - best two-window schedule chosen on Jul 2019-Jun 2020, tested on Jul 2020-Jun 2021
5. singletons         - households positive in only one window; persistent-only reference
6. random_error_sim   - non-adversarial (random) answer error at hypothetical flip rates
7. recall_overlap     - observed answer discordance between World Bank Malawi rounds 11 and 12 (< 30 days
                        apart). Reported as discordance only: it mixes real change, recall differences and
                        reporting error, so it is not a misclassification rate or bound.

Aggregates only are written to data/public_aggregates/review/.
"""

from __future__ import annotations

from itertools import combinations
from math import comb

import numpy as np
import pandas as pd

from . import build_panels as bp
from . import schedule_metrics as sm
from .config import Paths, load_config
from .extensions import CY_ORDER, _phone
from .hfps import load_investigation_config
from .missing_bounds import sharp_missing_bounds

ITEMS = ["i3_1_nofood_4w", "i3_2_night_4w", "i3_3_wholeday_4w"]
SIX = [1, 2, 3, 4, 5, 6]


def _wide(phone, base, country, sel, value, columns):
    sub = phone[(phone["country"] == country) & sel & phone[value].notna()]
    w = sub.pivot_table(index="id", columns="slot", values=value, aggfunc="first").reindex(columns=columns)
    fr = base[base["country"] == country].set_index("id")[["village_id"]]
    return fr.join(w, how="left")


def _year(phone, base, c, year, slots=SIX, value="HHS"):
    return _wide(phone, base, c, phone["year"] == year, value, slots)


def _cy(phone, base, c, cy, value="HHS"):
    return _wide(phone, base, c, phone["cy"] == cy, value, CY_ORDER)


def _bin(mat, thr=2):
    v = mat.drop(columns="village_id")
    return (v >= thr).astype(float).where(v.notna())


# ---------------------------------------------------------------- 1. scoring
def scoring_check(phone, base, raw_phone_file) -> tuple[pd.DataFrame, pd.DataFrame]:
    ph = phone.copy()
    items = ph[ITEMS]
    ph["occ"] = items.sum(axis=1).where(items.notna().all(axis=1))
    rec = ph.dropna(subset=["HHS", "occ"])
    excess = rec["HHS"] - rec["occ"]
    records = pd.DataFrame([{
        "records_with_score_and_items": len(rec),
        "score_equals_yes_count": int((excess == 0).sum()),
        "score_exceeds_yes_count": int((excess > 0).sum()),
        "score_below_yes_count": int((excess < 0).sum()),
        "max_excess": float(excess.max()),
        "excess_never_exceeds_yes_count": bool((excess <= rec["occ"]).all()),
        "interpretation": "consistent with standard HHS scoring (yes with rarely/sometimes = 1, often = 2): excess = number of 'often' answers",
    }])
    alt = pd.read_stata(raw_phone_file, convert_categoricals=False,
                        columns=["HHS", "i3_1_skip_4w", ITEMS[1], ITEMS[2]]).dropna()
    ex2 = alt["HHS"] - alt[["i3_1_skip_4w", ITEMS[1], ITEMS[2]]].sum(axis=1)
    records = pd.concat([records.assign(first_item="i3_1_nofood_4w (no food of any kind in the house; standard HHS item 1)"),
                         pd.DataFrame([{"records_with_score_and_items": len(alt), "score_equals_yes_count": int((ex2 == 0).sum()),
                                        "score_exceeds_yes_count": int((ex2 > 0).sum()), "score_below_yes_count": int((ex2 < 0).sum()),
                                        "max_excess": float(ex2.max()), "excess_never_exceeds_yes_count": bool((ex2 <= alt[["i3_1_skip_4w", ITEMS[1], ITEMS[2]]].sum(axis=1)).all()),
                                        "interpretation": "inconsistent with HHS scoring (scores below the yes count occur): the score is not built from the skipped-meal item",
                                        "first_item": "i3_1_skip_4w (skipped a meal; alternative)"}])], ignore_index=True)
    rows = []
    for c in ("Malawi", "Liberia"):
        a = _bin(_year(phone, base, c, 2020)).dropna()
        b = _bin(_year(ph, base, c, 2020, value="occ")).dropna()
        idx = a.index.intersection(b.index)
        A, B = a.loc[idx].to_numpy().astype(int), b.loc[idx].to_numpy().astype(int)
        for name, H in (("supplied HHS >= 2", A), ("two or more of three hunger experiences (occurrence count >= 2)", B)):
            K = H.sum(axis=1)
            for m in (1, 2, 3):
                pos = K > 0
                miss = np.array([comb(6 - k, m) / comb(6, m) for k in K[pos]])
                rows.append({"country": c, "definition": name, "n_complete": len(H), "n_reference_positive": int(pos.sum()),
                             "m": m, "missed_share": float(miss.mean())})
        rows.append({"country": c, "definition": "households whose reference status differs between definitions",
                     "n_complete": len(idx), "n_reference_positive": int(((A.max(axis=1) > 0) != (B.max(axis=1) > 0)).sum())})
    return records, pd.DataFrame(rows)


# ---------------------------------------------------------------- 2. calendar-based lean window
def _calendar_window(lean_months: list[int], slots: list[int]) -> int:
    def overlap(s):
        return len({2 * s - 1, 2 * s} & set(lean_months))
    best = max(slots, key=lambda s: (overlap(s), -slots.index(s)))
    return best


def _contrast(H, j, clusters, boot):
    pos = (H.max(axis=1) > 0).astype(float)
    fm = pos * (H[:, j] == 0)
    rm, _ = sm.household_terms(H, m=1)
    reps, _ = sm.ratio_bootstrap(clusters, {"f": (fm, pos), "r": (rm, pos)}, boot["draws"], boot["seed"])
    d = reps["f"] - reps["r"]
    return {"n_complete": len(H), "n_reference_positive": int(pos.sum()), "window_missed": fm.sum() / pos.sum(),
            "random_missed": rm.sum() / pos.sum(), "diff": (fm.sum() - rm.sum()) / pos.sum(),
            "diff_ci_low": sm.interval(d, boot["level"])[0], "diff_ci_high": sm.interval(d, boot["level"])[1]}


def calendar_lean(phone, base, lean: dict, boot: dict) -> pd.DataFrame:
    rows = []
    specs = [("Malawi", "calendar 2020 (six windows)", "year", 2020, SIX), ("Malawi", "Jul 2019 - Jun 2020 (six windows)", "cy", 2019, CY_ORDER),
             ("Malawi", "Jul 2020 - Jun 2021 (six windows)", "cy", 2020, CY_ORDER), ("Malawi", "calendar 2021 (Jan-Aug, four windows)", "year", 2021, [1, 2, 3, 4]),
             ("Liberia", "calendar 2020 (six windows)", "year", 2020, SIX), ("Liberia", "Jul 2020 - Jun 2021 (six windows)", "cy", 2020, CY_ORDER),
             ("Liberia", "calendar 2021 (Jan-Aug, four windows)", "year", 2021, [1, 2, 3, 4])]
    for c, label, kind, yr, slots in specs:
        mat = _year(phone, base, c, yr, slots) if kind == "year" else _cy(phone, base, c, yr)
        b = _bin(mat).dropna()
        w = _calendar_window(lean[c], slots)
        r = _contrast(b.to_numpy().astype(int), slots.index(w), mat.loc[b.index, "village_id"].to_numpy(), boot)
        rows.append({"country": c, "horizon": label, "reference_windows": len(slots),
                     "fews_lean_months": "-".join(str(m) for m in lean[c]), "calendar_window": bp.SLOT_LABELS[w], **r})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 3. bounds, second scope
def second_scope(phone, base) -> pd.DataFrame:
    rows = []
    for c in ("Malawi", "Liberia"):
        b = _bin(_year(phone, base, c, 2020))
        for scope, frame in (("all baseline-frame households", b), ("households with >= 1 observed 2020 window", b[b.notna().any(axis=1)])):
            k = frame.sum(axis=1, skipna=True).astype(int).to_numpy()
            r = frame.isna().sum(axis=1).astype(int).to_numpy()
            for m in (1, 2, 3):
                res = sharp_missing_bounds(k, r, 6, m)
                rows.append({"country": c, "scope": scope, "households": len(frame), "never_observed": int((r == 6).sum()),
                             "m": m, "lower": float(res["lower"].value), "upper": float(res["upper"].value)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 4. frozen best pair
def frozen_pair(phone, base, boot) -> pd.DataFrame:
    tr = _bin(_cy(phone, base, "Malawi", 2019)).dropna().to_numpy().astype(int)
    te_m = _cy(phone, base, "Malawi", 2020)
    te_b = _bin(te_m).dropna()
    te = te_b.to_numpy().astype(int)
    pairs = list(combinations(range(6), 2))

    def missed(H, p):
        pos = H.max(axis=1) > 0
        return float((H[pos][:, list(p)].sum(axis=1) == 0).mean())

    trm = {p: missed(tr, p) for p in pairs}
    best = min(pairs, key=lambda p: (trm[p], p))
    tem = {p: missed(te, p) for p in pairs}
    pos = (te.max(axis=1) > 0).astype(float)
    fm = pos * (te[:, list(best)].sum(axis=1) == 0)
    rm, _ = sm.household_terms(te, m=2)
    reps, _ = sm.ratio_bootstrap(te_m.loc[te_b.index, "village_id"].to_numpy(), {"f": (fm, pos), "r": (rm, pos)}, boot["draws"], boot["seed"])
    lab = lambda p: " + ".join(bp.SLOT_LABELS[CY_ORDER[i]] for i in p)  # noqa: E731
    test_best = min(pairs, key=lambda p: (tem[p], p))
    return pd.DataFrame([{
        "train": "Jul 2019 - Jun 2020", "test": "Jul 2020 - Jun 2021", "selected_pair": lab(best),
        "train_missed": trm[best], "n_train_complete": len(tr), "n_test_complete": len(te), "n_test_reference_positive": int(pos.sum()),
        "test_missed_frozen_pair": tem[best], "test_missed_random_pair": float(rm.sum() / pos.sum()),
        "diff": tem[best] - float(rm.sum() / pos.sum()),
        "diff_ci_low": sm.interval(reps["f"] - reps["r"], boot["level"])[0], "diff_ci_high": sm.interval(reps["f"] - reps["r"], boot["level"])[1],
        "in_sample_best_pair_in_test_year": lab(test_best), "in_sample_best_missed": tem[test_best]}])


# ---------------------------------------------------------------- 5. singletons
def singletons(phone, base, lean, boot) -> pd.DataFrame:
    rows = []
    for c in ("Malawi", "Liberia"):
        mat = _year(phone, base, c, 2020)
        raw = mat.drop(columns="village_id").dropna()
        H = (raw >= 2).astype(int).to_numpy()
        K = H.sum(axis=1)
        single = K == 1
        score_at_single = raw.to_numpy()[single][H[single] == 1]
        w = SIX.index(_calendar_window(lean[c], SIX))
        base_row = {"country": c, "n_complete": len(H), "reference_positive": int((K > 0).sum()), "positive_in_one_window": int(single.sum()),
                    "single_positive_with_score_exactly_2": int((score_at_single == 2).sum()),
                    "single_positive_with_score_3_plus": int((score_at_single >= 3).sum())}
        vill = mat.loc[raw.index, "village_id"].to_numpy()
        for ref, keep in (("all reference positives", K >= 0), ("persistent only (positive in >= 2 windows)", (K >= 2) | (K == 0))):
            Hk = H[keep]
            Kk = Hk.sum(axis=1)
            fr = {f"random_missed_m{m}": float(np.mean([comb(6 - k, m) / comb(6, m) for k in Kk[Kk > 0]])) for m in (1, 2, 3)}
            r = _contrast(Hk, w, vill[keep], boot)
            rows.append({**base_row, "reference": ref, **fr, "calendar_window": bp.SLOT_LABELS[SIX[w]],
                         "calendar_window_missed": r["window_missed"], "calendar_diff_vs_random": r["diff"],
                         "diff_ci_low": r["diff_ci_low"], "diff_ci_high": r["diff_ci_high"]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 6. random error
def random_error_sim(phone, base, lean, rates, sims, seed) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(seed)
    for label, mat, slots in (("Malawi Jul 2020 - Jun 2021", _cy(phone, base, "Malawi", 2020), CY_ORDER),
                              ("Malawi calendar 2021 (four windows)", _year(phone, base, "Malawi", 2021, [1, 2, 3, 4]), [1, 2, 3, 4])):
        H = _bin(mat).dropna().to_numpy().astype(int)
        j = slots.index(_calendar_window(lean["Malawi"], slots))
        for e in rates:
            ds = []
            for _ in range(sims):
                Hn = np.where(rng.random(H.shape) < e, 1 - H, H)
                pos = Hn.max(axis=1) > 0
                rmiss = np.array([comb(Hn.shape[1] - k, 1) / Hn.shape[1] for k in Hn[pos].sum(axis=1)])
                ds.append(float((Hn[pos][:, j] == 0).mean() - rmiss.mean()))
            ds = np.array(ds)
            rows.append({"horizon": label, "calendar_window": bp.SLOT_LABELS[slots[j]], "error_rate_per_answer": e, "simulations": sims,
                         "mean_diff": float(ds.mean()), "p2_5": float(np.quantile(ds, 0.025)), "p97_5": float(np.quantile(ds, 0.975)),
                         "share_sims_diff_ge_0": float((ds >= 0).mean())})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 7. recall overlap discordance (World Bank Malawi)
def recall_overlap(paths: Paths) -> pd.DataFrame:
    from . import hfps
    cfg = load_investigation_config(paths)["hfps"]
    if not (paths.root / cfg["extracted_dir"]).exists():
        return pd.DataFrame()
    h = hfps.load(cfg, paths.root)
    rows = []
    for item in ("s8q7", "s8q8"):
        m = hfps.matrix(h, [11, 12], item).dropna()
        d = h.long.pivot(index="hh", columns="round", values="date").reindex(m.index)
        mm = m[(d[12] - d[11]).dt.days < 30]
        disc = float((mm[11] != mm[12]).mean())
        rows.append({"item": item, "pairs_under_30_days": len(mm), "discordance": disc,
                                          "yes_then_no": int(((mm[11] == 1) & (mm[12] == 0)).sum()), "no_then_yes": int(((mm[11] == 0) & (mm[12] == 1)).sum())})
    return pd.DataFrame(rows)


def run(paths: Paths | None = None) -> dict:
    paths = paths or Paths()
    cfg = load_config(paths.config)
    rc = load_investigation_config(paths)["review"]
    boot = load_investigation_config(paths)["aggarwal_extensions"]["bootstrap"]
    out = paths.public / "review"
    out.mkdir(parents=True, exist_ok=True)
    phone, base = _phone(paths, cfg)
    rec, fr = scoring_check(phone, base, paths.extracted / cfg["source"]["phone_file"])
    rec.to_csv(out / "hhs_scoring_check_records.csv", index=False)
    fr.to_csv(out / "hhs_scoring_frontier_comparison.csv", index=False)
    calendar_lean(phone, base, rc["lean_months"], boot).to_csv(out / "calendar_lean_season_sensitivity.csv", index=False)
    second_scope(phone, base).to_csv(out / "missing_bounds_second_scope.csv", index=False)
    frozen_pair(phone, base, boot).to_csv(out / "frozen_best_pair.csv", index=False)
    singletons(phone, base, rc["lean_months"], boot).to_csv(out / "single_window_positives.csv", index=False)
    random_error_sim(phone, base, rc["lean_months"], rc["random_error_rates"], rc["random_error_sims"], rc["seed"]).to_csv(
        out / "random_error_simulation.csv", index=False)
    ro = recall_overlap(paths)
    if len(ro):
        ro.to_csv(out / "recall_overlap_discordance.csv", index=False)
    return {"written": sorted(p.name for p in out.glob("*.csv"))}
