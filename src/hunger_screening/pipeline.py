"""End-to-end analysis pipeline. Deterministic given config/study.yaml and the source archive.

Household-level intermediate files go to data/interim (gitignored). Everything written to
data/public_aggregates, tables/ and reports/ is aggregate-only.
"""

from __future__ import annotations

import json
import logging
import time
from math import floor

import numpy as np
import pandas as pd
import yaml

from . import build_panels as bp
from . import cluster_bootstrap as cb
from . import optional_diagnostics as od
from . import schema_audit as sa
from . import timing_validation as tv
from .combinatorics import missed_fraction
from .config import Paths, config_hash, load_config
from .estimands import frontier, k_distribution
from .misclassification_bounds import label_error_bounds
from .missing_bounds import naive_imputations, sharp_missing_bounds
from .provenance import environment_record, utc_now, write_manifest
from .source_acquisition import acquire, save_record

log = logging.getLogger("hunger_screening")


def _setup_logging(paths: Paths) -> None:
    paths.logs.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(paths.logs / "pipeline.log", mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root = logging.getLogger("hunger_screening")
    root.handlers[:] = [handler, console]
    root.setLevel(logging.INFO)


def _f(x) -> float:
    return float(x) if x is not None else float("nan")


def run(paths: Paths | None = None, allow_download: bool = True) -> dict:
    paths = paths or Paths()
    paths.ensure()
    _setup_logging(paths)
    t0 = time.time()
    cfg = load_config(paths.config)
    pub = paths.public
    summary: dict = {"generated_utc": utc_now(), "config_sha256": config_hash(paths.config)}

    # ---------------- Phase 1: provenance ----------------
    rec = acquire(paths, cfg, allow_download=allow_download)
    save_record(rec, pub / "source_provenance.json")
    log.info("Source verified: %s bytes, sha256 %s", rec["bytes"], rec["sha256"])
    summary["source"] = {k: rec[k] for k in ("bytes", "sha256", "bytes_match", "sha256_match", "supplement_doi")}

    phone_path = paths.extracted / cfg["source"]["phone_file"]
    base_path = paths.extracted / cfg["source"]["baseline_file"]
    dd = pd.concat([sa.data_dictionary(phone_path), sa.data_dictionary(base_path)], ignore_index=True)
    dd.to_csv(pub / "data_dictionary.csv", index=False)

    phone_full = pd.read_stata(phone_path, convert_categoricals=False)
    base_full = pd.read_stata(base_path, convert_categoricals=False)
    checks = sa.integrity_checks(phone_full, base_full)
    checks.to_csv(pub / "integrity_checks.csv", index=False)
    sa.hhs_item_crosstab(phone_full).to_csv(pub / "hhs_item_crosstab.csv", index=False)
    sa.monthly_record_counts(phone_full).to_csv(pub / "monthly_record_counts.csv", index=False)
    log.info("Integrity checks: %d/%d pass", checks["pass"].sum(), len(checks))
    del phone_full, base_full

    # ---------------- Phase 2: panels ----------------
    phone_raw, frame = bp.load_sources(paths.extracted, cfg["source"]["phone_file"], cfg["source"]["baseline_file"])
    phone_valid = bp.assign_slots(bp.valid_hhs(phone_raw))
    phone, dinfo = bp.deduplicate(phone_valid)
    summary["dedup"] = {"household_slots_with_multiple": dinfo.household_slots_with_multiple,
                        "records_dropped": dinfo.records_dropped,
                        "binary_outcome_differs_by_threshold": dinfo.binary_outcome_differs}
    log.info("Dedup: %s", summary["dedup"])

    n = cfg["design"]["n_slots"]
    thr = cfg["outcome"]["primary_threshold"]
    ms = cfg["design"]["m_values"]
    year = cfg["design"]["main_year"]
    slots6 = list(range(1, n + 1))
    hhs20 = bp.slot_matrix(phone, frame, year, slots6)
    hhs21 = bp.slot_matrix(phone, frame, 2021, slots6)
    hhs20.to_csv(paths.interim / "hhs_slots_2020.csv")
    hhs21.to_csv(paths.interim / "hhs_slots_2021.csv")
    bin20 = bp.binarize(hhs20, thr)

    flow = bp.cohort_flow(phone_raw, phone_valid, phone, frame, bin20)
    flow.to_csv(pub / "cohort_flow.csv", index=False)

    obs = pd.concat([od.observation_pattern(hhs20), od.observation_pattern(hhs21)], ignore_index=True)
    obs.to_csv(pub / "observation_pattern.csv", index=False)
    pos_share = pd.concat([od.slot_positive_share(hhs20, thr), od.slot_positive_share(hhs21, thr)],
                          ignore_index=True)
    pos_share.to_csv(pub / "slot_positive_share.csv", index=False)
    od.observed_count_distribution(bin20).to_csv(pub / "observed_slot_count_distribution.csv", index=False)

    countries = cfg["design"]["countries"]

    # ---------------- Phase 3: exact estimand + bootstrap ----------------
    bcfg = cfg["bootstrap"]
    fr_rows, kd_rows, stab_rows = [], [], []
    for t in [thr] + cfg["outcome"]["secondary_thresholds"]:
        b = bp.binarize(hhs20, t)
        for c in countries:
            k = bp.complete_k(b.xs(c, level="country", drop_level=False))
            f = frontier(k.to_numpy(), n, ms)
            f.insert(0, "threshold", t)
            f.insert(0, "country", c)
            if t == thr:
                res = cb.village_bootstrap(k, n, ms, bcfg["draws"], bcfg["seed"])
                s = cb.summarize(res, f["missed_fraction"], bcfg["level"], bcfg["quantile_method"])
                f = f.merge(s[["m", "ci_low", "ci_high", "bootstrap_se", "zero_denominator_draws",
                               "villages_resampled", "draws", "seed", "interval"]], on="m")
                np.savetxt(paths.interim / f"bootstrap_replicates_{c}.csv", res.replicates, delimiter=",",
                           header=",".join(f"m{m}" for m in ms), comments="")
                # stability: more draws, alternative seeds, all-frame villages, jackknife
                big = cb.village_bootstrap(k, n, ms, bcfg["stability_draws"], bcfg["seed"] + 1)
                sb = cb.summarize(big, f["missed_fraction"], bcfg["level"], bcfg["quantile_method"])
                frame_vill = frame.loc[frame.country == c, "village_id"].unique()
                allv = cb.village_bootstrap(k, n, ms, bcfg["draws"], bcfg["seed"], all_villages=frame_vill)
                sa_ = cb.summarize(allv, f["missed_fraction"], bcfg["level"], bcfg["quantile_method"])
                jk = cb.cluster_jackknife_se(k, n, ms)
                for i, m in enumerate(ms):
                    for label, src in (("primary_2000_draws", s), (f"{bcfg['stability_draws']}_draws_seed+1", sb),
                                       ("2000_draws_all_frame_villages", sa_)):
                        stab_rows.append({"country": c, "m": m, "variant": label, "ci_low": src.ci_low[i],
                                          "ci_high": src.ci_high[i], "se": src.bootstrap_se[i],
                                          "villages": int(src.villages_resampled[i]),
                                          "zero_denominator_draws": int(src.zero_denominator_draws[i])})
                    stab_rows.append({"country": c, "m": m, "variant": "village_jackknife_se", "ci_low": np.nan,
                                      "ci_high": np.nan, "se": jk[i], "villages": int(s.villages_resampled[i]),
                                      "zero_denominator_draws": 0})
            fr_rows.append(f)
            kd = k_distribution(k.to_numpy(), n)
            kd.insert(0, "threshold", t)
            kd.insert(0, "country", c)
            kd_rows.append(kd)
    front = pd.concat(fr_rows, ignore_index=True)
    front.to_csv(pub / "frontier.csv", index=False)
    pd.concat(kd_rows, ignore_index=True).to_csv(pub / "k_distribution.csv", index=False)
    pd.DataFrame(stab_rows).to_csv(pub / "bootstrap_stability.csv", index=False)
    log.info("Frontier computed")

    # fixed schedules (secondary)
    fs = []
    for c in countries:
        bc = bin20.xs(c, level="country").dropna()
        t = od.fixed_schedule_table(bc, ms[:-1])
        t.insert(0, "country", c)
        fs.append(t)
    pd.concat(fs, ignore_index=True).to_csv(pub / "fixed_schedules.csv", index=False)

    # ---------------- Phase 4: bounds ----------------
    mb_rows, le_rows = [], []
    alphas = cfg["misclassification"]["alphas"]
    for c in countries:
        cnt = bp.observed_counts(bin20.xs(c, level="country"))
        k_arr, r_arr = cnt["k"].to_numpy(), cnt["r"].to_numpy()
        n_obs_total = int(cnt["n_obs"].sum())
        comp_mask = r_arr == 0
        for m in ms:
            tb = time.time()
            sb_ = sharp_missing_bounds(k_arr, r_arr, n, m)
            naive = naive_imputations(k_arr, r_arr, n, m)
            mb_rows.append({
                "country": c, "m": m, "frame_households": len(k_arr),
                "households_any_missing": int((r_arr > 0).sum()),
                "households_never_observed": int((r_arr == n).sum()),
                "observed_screens": n_obs_total,
                "lower": _f(sb_["lower"].value), "upper": _f(sb_["upper"].value),
                "lower_exact": str(sb_["lower"].value), "upper_exact": str(sb_["upper"].value),
                "lower_n_reference_positive": sb_["lower"].n_reference_positive,
                "upper_n_reference_positive": sb_["upper"].n_reference_positive,
                "all_missing_negative": _f(naive["all_missing_negative"]),
                "all_missing_positive": _f(naive["all_missing_positive"]),
                "complete_case_point": _f(missed_fraction(k_arr[comp_mask], n, m)),
                "seconds": time.time() - tb,
            })
            for scope, kk, rr, base in (("frame_missing_arbitrary", k_arr, r_arr, n_obs_total),
                                        ("complete_histories_only", k_arr[comp_mask], r_arr[comp_mask],
                                         int(comp_mask.sum()) * n)):
                for a in alphas:
                    B = floor(a * base + 1e-9)
                    tb = time.time()
                    lb = label_error_bounds(kk, rr, n, m, B)
                    le_rows.append({
                        "country": c, "scope": scope, "m": m, "alpha": a, "observed_screens_base": base,
                        "budget_flips": B,
                        "lower": _f(lb["lower"].value), "upper": _f(lb["upper"].value),
                        "lower_exact": str(lb["lower"].value), "upper_exact": str(lb["upper"].value),
                        "lower_n_reference_positive": lb["lower"].n_reference_positive,
                        "upper_n_reference_positive": lb["upper"].n_reference_positive,
                        "lower_budget_used": lb["lower"].budget_used, "upper_budget_used": lb["upper"].budget_used,
                        "lower_iterations": lb["lower"].dinkelbach_iterations,
                        "upper_iterations": lb["upper"].dinkelbach_iterations,
                        "lower_certificate_F": lb["lower"].certificate_F,
                        "upper_certificate_F": lb["upper"].certificate_F,
                        "zero_positive_world_feasible": lb["zero_positive_world_feasible"],
                        "seconds": time.time() - tb,
                    })
        log.info("Bounds computed for %s", c)
    mb = pd.DataFrame(mb_rows)
    le = pd.DataFrame(le_rows)
    # wall-clock solver times go to logs/ so that public outputs are byte-deterministic
    pd.concat([mb.assign(kind="missing_bounds"), le.assign(kind="label_error_bounds")])[
        ["kind", "country", "m", "alpha", "scope", "seconds"]].to_csv(paths.logs / "solver_runtimes.csv", index=False)
    mb = mb.drop(columns="seconds")
    le = le.drop(columns="seconds")
    mb.to_csv(pub / "missing_bounds.csv", index=False)
    le.to_csv(pub / "label_error_bounds.csv", index=False)

    # ---------------- Phase 5: timing ----------------
    tcfg = cfg["timing"]
    tslots = tcfg["slots"]
    tr = bp.binarize(bp.slot_matrix(phone, frame, tcfg["train_year"], tslots), thr)
    te = bp.binarize(bp.slot_matrix(phone, frame, tcfg["test_year"], tslots), thr)
    cand_rows, val_rows, tb_rows = [], [], []
    for c in countries:
        trc = tr.xs(c, level="country", drop_level=False)
        trc.attrs.update(tr.attrs)
        tec = te.xs(c, level="country", drop_level=False)
        tec.attrs.update(te.attrs)
        rule = tv.select_slot(trc, tcfg["train_year"], thr, tcfg["tie_break"])
        ct = tv.candidate_table(trc)
        ct.insert(0, "country", c)
        ct["year"] = tcfg["train_year"]
        ct["selected"] = ct["slot"] == rule.slot
        ct["random_one_slot"] = ct.attrs["random_one_slot"]
        # post hoc disclosure only: every candidate's 2021 performance
        ct21 = tv.candidate_table(tec)
        ct21.insert(0, "country", c)
        ct21["year"] = tcfg["test_year"]
        ct21["selected"] = ct21["slot"] == rule.slot
        ct21["random_one_slot"] = ct21.attrs["random_one_slot"]
        cand_rows += [ct, ct21]
        matched_ids = trc.dropna().index.intersection(tec.dropna().index)
        tr_m = tv.restrict(trc, matched_ids)
        te_m = tv.restrict(tec, matched_ids)
        for cohort, test_mat in (("2021 complete four-slot cohort", tec), ("Matched: complete in both years", te_m)):
            ev = tv.evaluate_rule(rule, test_mat)
            ev.update({"country": c, "cohort": cohort, "train_year": rule.train_year,
                       "train_missed": rule.train_missed, "train_n_reference_positive": rule.train_n_reference_positive,
                       "train_n_complete": len(trc.dropna())})
            bt = tv.bootstrap_timing(trc, test_mat, rule, tcfg["bootstrap_draws"], bcfg["seed"])
            ev.update({"frozen_ci_low": bt["test_frozen_ci"][0], "frozen_ci_high": bt["test_frozen_ci"][1],
                       "random_ci_low": bt["test_random_ci"][0], "random_ci_high": bt["test_random_ci"][1],
                       "diff_ci_low": bt["test_difference_ci"][0], "diff_ci_high": bt["test_difference_ci"][1],
                       "zero_denominator_draws": bt["test_zero_denominator_draws"]})
            val_rows.append(ev)
            if cohort.startswith("2021"):
                for s_, fq in bt["selection_frequency"].items():
                    tb_rows.append({"country": c, "slot": s_, "selection_frequency_2020_bootstrap": fq,
                                    "draws": bt["draws"]})
        # matched-cohort training performance (same households, 2020)
        evm = tv.evaluate_rule(rule, tr_m)
        evm.update({"country": c, "cohort": "Matched: 2020 performance of frozen slot"})
        val_rows.append(evm)
    pd.concat(cand_rows, ignore_index=True).to_csv(pub / "timing_candidates.csv", index=False)
    tval = pd.DataFrame(val_rows)
    tval.to_csv(pub / "timing_validation.csv", index=False)
    pd.DataFrame(tb_rows).to_csv(pub / "timing_selection_stability.csv", index=False)
    log.info("Timing assessment complete")

    # ---------------- secondary: attrition and IPW ----------------
    cov = od.prepare_covariates(frame)
    complete = bin20.notna().all(axis=1)
    od.attrition_balance(cov, complete).to_csv(pub / "attrition_balance.csv", index=False)
    od.ipw_frontier(cov, bin20, n, ms).to_csv(pub / "ipw_frontier.csv", index=False)

    # ---------------- reproduction comparison ----------------
    rep = reproduction_table(paths, flow, front, mb, le, tval, dinfo, thr)
    rep.to_csv(pub / "reproduction_comparison.csv", index=False)

    # ---------------- summary ----------------
    summary["counts"] = {c: {r.step: r.count for r in flow[flow.country == c].itertuples()} for c in countries}
    summary["frontier"] = {c: front[(front.country == c) & (front.threshold == thr)]
                           [["m", "missed_fraction", "ci_low", "ci_high", "n_reference_positive", "n_complete"]]
                           .to_dict(orient="records") for c in countries}
    summary["missing_bounds"] = {c: mb[mb.country == c][["m", "lower", "upper"]].to_dict(orient="records")
                                 for c in countries}
    summary["reproduction"] = {"n_checks": len(rep), "n_pass": int(rep["pass_with_tolerance"].sum())}
    summary["runtime_seconds"] = round(time.time() - t0, 1)
    (pub / "results_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    env = environment_record()
    env["config_sha256"] = summary["config_sha256"]
    (paths.reports / "execution_environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
    write_manifest(list(pub.glob("*")), paths.root, paths.root / "data" / "artifact_manifest.json",
                   {"config_sha256": summary["config_sha256"], "source_sha256": rec["sha256"]})
    log.info("Pipeline finished in %.1f s", time.time() - t0)
    return summary


def reproduction_table(paths, flow, front, mb, le, tval, dinfo, thr) -> pd.DataFrame:
    prev = yaml.safe_load((paths.root / "config" / "previous_findings.yaml").read_text(encoding="utf-8"))
    tol, itol = prev["tolerance_pp"], prev["interval_tolerance_pp"]
    rows = []

    def add(qty, country, p, newv, tolerance, script, unit="pct"):
        diff = None if newv is None or p is None else newv - p
        ok = diff is not None and abs(diff) <= tolerance + 1e-9
        rows.append({"quantity": qty, "country": country, "previous_reported": p,
                     "newly_computed": None if newv is None else round(newv, 4),
                     "difference": None if diff is None else round(diff, 4), "unit": unit,
                     "pass_with_tolerance": bool(ok), "tolerance": tolerance, "script": script,
                     "reason_if_discrepant": "" if ok else "see REPRODUCTION_AUDIT.md"})

    def cnt(c, step):
        return int(flow[(flow.country == c) & (flow.step == step)]["count"].iloc[0])

    for c in ("Malawi", "Liberia"):
        add("Baseline phone-frame households", c, prev["counts"]["frame_households"][c],
            cnt(c, "Baseline phone-frame households"), 0, "build_panels.cohort_flow", "households")
        add("Households with six 2020 screens", c, prev["counts"]["complete_2020"][c],
            cnt(c, "Households with all 6 valid 2020 screens"), 0, "build_panels.cohort_flow", "households")
        add("Complete histories reference-positive", c, prev["counts"]["reference_positive_2020"][c],
            cnt(c, "Complete households reference-positive (HHS>=2 in >=1 slot)"), 0,
            "build_panels.cohort_flow", "households")
        f = front[(front.country == c) & (front.threshold == thr)].set_index("m")
        for m, v in prev["main_missed_pct"][c].items():
            add(f"Missed, {m} retained screen(s)", c, v, 100 * f.loc[m, "missed_fraction"], tol, "estimands.frontier")
        for m, (lo, hi) in prev["bootstrap_ci_pct"][c].items():
            add(f"Bootstrap 95% lower, m={m}", c, lo, 100 * f.loc[m, "ci_low"], itol, "cluster_bootstrap")
            add(f"Bootstrap 95% upper, m={m}", c, hi, 100 * f.loc[m, "ci_high"], itol, "cluster_bootstrap")
        b = mb[(mb.country == c) & (mb.m == 1)].iloc[0]
        lo, hi = prev["missing_bounds_m1_pct"][c]
        add("Missing-history bound lower, m=1", c, lo, 100 * b.lower, tol, "missing_bounds")
        add("Missing-history bound upper, m=1", c, hi, 100 * b.upper, tol, "missing_bounds")
        e = le[(le.country == c) & (le.m == 1) & (le.alpha == 0.05) & (le.scope == "frame_missing_arbitrary")].iloc[0]
        lo, hi = prev["label_error_5pct_bounds_m1_pct"][c]
        add("Missing + 5% label-error bound lower, m=1", c, lo, 100 * e.lower, tol, "misclassification_bounds")
        add("Missing + 5% label-error bound upper, m=1", c, hi, 100 * e.upper, tol, "misclassification_bounds")
        T = prev["timing"]
        full = tval[(tval.country == c) & (tval.cohort == "2021 complete four-slot cohort")].iloc[0]
        mat = tval[(tval.country == c) & (tval.cohort == "Matched: complete in both years")].iloc[0]
        add("Timing: slot selected on 2020", c, T["selected_slot"][c], full.slot, 0, "timing_validation", "slot")
        add("Timing: 2020 missed, selected slot", c, T["train_missed_pct"][c], 100 * full.train_missed, tol,
            "timing_validation")
        add("Timing: 2021 missed, frozen slot", c, T["test_frozen_missed_pct"][c], 100 * full.missed_frozen, tol,
            "timing_validation")
        add("Timing: 2021 missed, random slot", c, T["test_random_missed_pct"][c],
            100 * full.missed_random_one_slot, tol, "timing_validation")
        add("Timing: households complete both years", c, T["matched_households"][c], mat.n_complete, 0,
            "timing_validation", "households")
        add("Timing matched: 2021 missed, frozen slot", c, T["matched_frozen_missed_pct"][c],
            100 * mat.missed_frozen, tol, "timing_validation")
        add("Timing matched: 2021 missed, random slot", c, T["matched_random_missed_pct"][c],
            100 * mat.missed_random_one_slot, tol, "timing_validation")
        if c == "Liberia":
            add("Timing matched: 2021 reference-positive", c, T["matched_reference_positive_liberia"],
                mat.n_reference_positive, 0, "timing_validation", "households")
    add("Household-slots with >1 record (2020-2021)", "Both", prev["counts"]["duplicate_household_slots"],
        dinfo.household_slots_with_multiple, 0, "build_panels.deduplicate", "household-slots")
    return pd.DataFrame(rows)
