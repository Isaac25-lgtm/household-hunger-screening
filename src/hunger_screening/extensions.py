"""Extensions of the Aggarwal et al. (2022) HHS analysis (same data, new questions).

1. July-June ("consumption year") re-specification of the frozen timing test for Malawi,
   where the phone panel starts in July 2019: train on Jul 2019 - Jun 2020 with all six
   two-month windows as candidates, evaluate on Jul 2020 - Jun 2021.
2. Exact decision robustness of the timing contrast (frozen window minus random window)
   to missing windows and to a shared budget of hypothetical label flips, with the
   smallest budget that can erase the advantage (tipping point).
3. Equal-budget schedule metrics with per-household and per-contact denominators.
4. Second-contact rule: which first-contact negatives to keep re-contacting.

Panels are rebuilt with the baseline project's loaders and outcome-blind duplicate rule.
Only aggregates are written.
"""

from __future__ import annotations

from fractions import Fraction
from math import floor

import numpy as np
import pandas as pd

from . import build_panels as bp
from . import history_bounds as hb
from . import schedule_metrics as sm
from .config import Paths, load_config
from .hfps import load_investigation_config, second_contact, select_candidate

CY_ORDER = [4, 5, 6, 1, 2, 3]  # Jul-Aug ... May-Jun within a July-June year


def _phone(paths: Paths, cfg: dict):
    phone, base = bp.load_sources(paths.extracted, cfg["source"]["phone_file"], cfg["source"]["baseline_file"])
    phone = bp.assign_slots(bp.valid_hhs(phone))
    phone, _ = bp.deduplicate(phone)
    phone = phone[phone["id"].isin(base["id"])]
    phone["cy"] = np.where(phone["month"] >= 7, phone["year"], phone["year"] - 1)
    return phone, base


def cy_matrix(phone: pd.DataFrame, base: pd.DataFrame, country: str, cy: int) -> pd.DataFrame:
    """HHS by window within a July-June year, every frame household (NaN = no screen)."""
    sub = phone[(phone["country"] == country) & (phone["cy"] == cy) & phone["HHS"].notna()]
    wide = sub.pivot_table(index="id", columns="slot", values="HHS", aggfunc="first").reindex(columns=CY_ORDER)
    fr = base[base["country"] == country].set_index("id")[["village_id"]]
    return fr.join(wide, how="left")


def year_matrix(phone: pd.DataFrame, base: pd.DataFrame, country: str, year: int, slots: list[int]) -> pd.DataFrame:
    sub = phone[(phone["country"] == country) & (phone["year"] == year) & phone["HHS"].notna()]
    wide = sub.pivot_table(index="id", columns="slot", values="HHS", aggfunc="first").reindex(columns=slots)
    fr = base[base["country"] == country].set_index("id")[["village_id"]]
    return fr.join(wide, how="left")


def _binary(mat: pd.DataFrame, thr: int) -> pd.DataFrame:
    v = mat.drop(columns="village_id")
    return (v >= thr).astype(float).where(v.notna())


def july_june_test(phone, base, ecfg: dict, thr: int, boot: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    c = ecfg["country"]
    jj = ecfg["july_june"]
    tr = _binary(cy_matrix(phone, base, c, jj["train_consumption_year"]), thr).dropna()
    te_full = cy_matrix(phone, base, c, jj["test_consumption_year"])
    te = _binary(te_full, thr).dropna()
    labels = [bp.SLOT_LABELS[s] for s in CY_ORDER]
    sel, train_miss = select_candidate(tr.to_numpy().astype(int), list(range(6)))
    T = te.to_numpy().astype(int)
    vill = te_full.loc[te.index, "village_id"].to_numpy()
    rmiss, pos = sm.household_terms(T, m=1)
    stats = {"random": (rmiss, pos)}
    for j in range(6):
        stats[labels[j]] = (sm.household_terms(T, schedule=[j])[0], pos)
    reps, zero = sm.ratio_bootstrap(vill, stats, boot["draws"], boot["seed"])
    rnd = float(rmiss.sum() / pos.sum())
    rows = []
    for j, lab in enumerate(labels):
        miss = float(stats[lab][0].sum() / pos.sum())
        rows.append({"test": "Aggarwal Malawi July-June: Jul 2019-Jun 2020 -> Jul 2020-Jun 2021", "threshold": thr,
                     "candidate": lab, "train_missed": train_miss[j], "selected_on_train": j == sel,
                     "n_train_complete": len(tr), "n_train_reference_positive": int((tr.max(axis=1) > 0).sum()),
                     "n_test_complete": len(te), "n_test_reference_positive": int(pos.sum()),
                     "test_missed": miss, "test_missed_ci_low": sm.interval(reps[lab], boot["level"])[0],
                     "test_missed_ci_high": sm.interval(reps[lab], boot["level"])[1], "test_random_missed": rnd,
                     "diff_vs_random": miss - rnd,
                     "diff_ci_low": sm.interval(reps[lab] - reps["random"], boot["level"])[0],
                     "diff_ci_high": sm.interval(reps[lab] - reps["random"], boot["level"])[1],
                     "villages_resampled": int(np.unique(vill).size), "zero_denominator_draws": zero[lab]})
    # selection stability: village bootstrap of the training year only
    trv = cy_matrix(phone, base, c, jj["train_consumption_year"]).loc[tr.index, "village_id"].to_numpy()
    uniq = np.unique(trv)
    rng = np.random.default_rng(boot["seed"] + 1)
    A = tr.to_numpy().astype(int)
    groups = {u: np.flatnonzero(trv == u) for u in uniq}
    counts = np.zeros(6)
    for _ in range(boot["draws"]):
        idx = np.concatenate([groups[u] for u in rng.choice(uniq, size=uniq.size, replace=True)])
        counts[select_candidate(A[idx], list(range(6)))[0]] += 1
    stab = pd.DataFrame({"test": rows[0]["test"], "threshold": thr, "candidate": labels,
                         "selection_frequency": counts / boot["draws"], "draws": boot["draws"]})
    return pd.DataFrame(rows), stab


def timing_robustness(binary: pd.DataFrame, fixed_index: int, alphas: list[float], label: str, thr: int) -> pd.DataFrame:
    b = binary[binary.notna().any(axis=1)]
    H = b.fillna(-1).astype(int).to_numpy()
    n = H.shape[1]
    c = hb.fixed_minus_random([fixed_index], n, 1)
    obs = int((H >= 0).sum())
    pt = hb.observed_value(H, c)
    rows = []
    for a in [0.0] + list(alphas):
        B = floor(a * obs)
        r = hb.contrast_bounds(H, c, B)
        rows.append({"analysis": label, "threshold": thr, "frame_households_observed": H.shape[0],
                     "households_with_missing": int((H < 0).any(axis=1).sum()), "observed_screens": obs,
                     "alpha": a, "flip_budget": B, "complete_case_diff": float(pt) if pt is not None else np.nan,
                     "lower": float(r["lower"].value), "upper": float(r["upper"].value),
                     "lower_exact": str(r["lower"].value), "upper_exact": str(r["upper"].value),
                     "certificate_lower": r["lower"].certificate_F, "certificate_upper": r["upper"].certificate_F})
    tip = hb.tipping_budget(H, c, "max", Fraction(0))
    out = pd.DataFrame(rows)
    out["tipping_budget_to_reach_zero"] = tip
    out["tipping_budget_share_of_observed_screens"] = tip / obs if tip is not None else np.nan
    return out


def schedules(binary: pd.DataFrame, labels: list[str], label: str, budgets=(1, 2, 3)) -> pd.DataFrame:
    H = binary.dropna().to_numpy().astype(int)
    df = sm.all_schedules(H, labels, budgets)
    df.insert(0, "cohort", label)
    return df


def aggarwal_second_contact(phone, base, country: str, year: int, slots: list[int], boot: dict, thr: int) -> pd.DataFrame:
    mat = year_matrix(phone, base, country, year, slots)
    v = mat.drop(columns="village_id").dropna()
    H = (v >= thr).astype(int).to_numpy()
    first_hhs = v.iloc[:, 0].to_numpy()
    warning = (first_hhs >= 1) & (first_hhs < thr)
    b = base.set_index("id").loc[v.index]
    keep = b["total_expend_mon_usd"].notna().to_numpy()
    out = second_contact(H[keep, 0], H[keep, 1:], warning[keep], b["total_expend_mon_usd"].to_numpy()[keep],
                         mat.loc[v.index, "village_id"].to_numpy()[keep], boot,
                         f"Aggarwal {country} {year}: first contact {bp.SLOT_LABELS[slots[0]]}, later windows "
                         + "/".join(bp.SLOT_LABELS[s] for s in slots[1:]))
    out.insert(1, "warning_rule", f"HHS = 1 at first contact (threshold {thr})")
    out = out.replace({"poorest first by baseline wealth (exact expectation)":
                       "poorest first by baseline monthly expenditure (exact expectation)",
                       "warning-sign (milder item positive at first contact)": "warning-sign (HHS = 1 at first contact)"})
    return out


def run(paths: Paths | None = None) -> dict:
    paths = paths or Paths()
    cfg = load_config(paths.config)
    ecfg = load_investigation_config(paths)["aggarwal_extensions"]
    out = paths.public / "investigation"
    out.mkdir(parents=True, exist_ok=True)
    thr = cfg["outcome"]["primary_threshold"]
    boot = ecfg["bootstrap"]
    phone, base = _phone(paths, cfg)

    jj, stab = july_june_test(phone, base, ecfg, thr, boot)
    jj.to_csv(out / "aggarwal_july_june_test.csv", index=False)
    stab.to_csv(out / "aggarwal_july_june_selection_stability.csv", index=False)

    rob = []
    slots = ecfg["timing_bounds_slots"]
    frozen = pd.read_csv(paths.public / "timing_validation.csv").drop_duplicates("country").set_index("country").slot
    if int(frozen["Malawi"]) != ecfg["frozen_slot_2021"]:
        raise RuntimeError("baseline frozen Malawi slot differs from configuration")
    for country in ("Malawi", "Liberia"):
        fixed_slot = int(frozen[country])
        b = _binary(year_matrix(phone, base, country, ecfg["timing_bounds_year"], slots), thr)
        rob.append(timing_robustness(b, slots.index(fixed_slot), ecfg["label_error_alphas"],
                                     f"Aggarwal {country} 2021: frozen {bp.SLOT_LABELS[fixed_slot]} vs random of 4", thr))
    sel = int(jj.index[jj.selected_on_train][0])
    bcy = _binary(cy_matrix(phone, base, ecfg["country"], ecfg["july_june"]["test_consumption_year"]), thr)
    rob.append(timing_robustness(bcy, sel, ecfg["label_error_alphas"],
                                 f"Aggarwal Malawi Jul 2020-Jun 2021: frozen {jj.candidate[sel]} vs random of 6", thr))
    pd.concat(rob).to_csv(out / "aggarwal_timing_robustness.csv", index=False)

    sch = []
    six = list(range(1, 7))
    for country in ("Malawi", "Liberia"):
        b = _binary(year_matrix(phone, base, country, 2020, six), thr)
        sch.append(schedules(b, [bp.SLOT_LABELS[s] for s in six], f"Aggarwal {country} 2020 (six windows)"))
    pd.concat(sch).to_csv(out / "aggarwal_fixed_schedules.csv", index=False)

    sc = []
    for country in ("Malawi", "Liberia"):
        sc.append(aggarwal_second_contact(phone, base, country, 2021, [1, 2, 3, 4], boot, thr))
        sc.append(aggarwal_second_contact(phone, base, country, 2020, six, boot, thr))
    pd.concat(sc).to_csv(out / "aggarwal_second_contact.csv", index=False)
    return {"july_june_selected": jj.candidate[sel]}
