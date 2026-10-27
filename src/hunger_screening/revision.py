"""Analyses added in the package revision of 27 October 2026 (see reports/ANALYSIS_HISTORY_AND_EVIDENCE_CLASSES.md).

1. window_comparisons   - every evaluated contact window in each Malawi horizon, with paired cluster-bootstrap
                          differences against the best observed window and against random timing. The best
                          observed window is reported as such, not as a demonstrated optimum.
2. season_groups        - EXPLORATORY, POST HOC: mean single-window missed share of September-February
                          windows minus March-August windows. Suggested during review after the window
                          results were known; reported only as a description.
3. second_contact_table - every executed second-contact comparison at matched re-contact budgets.
4. h2_h4_table          - the locked protocol's H2 (transfer) and H4 (rural vs urban) results, with eligibility.

All outputs are aggregates, written to data/public_aggregates/review/.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import build_panels as bp
from . import schedule_metrics as sm
from .config import Paths, load_config
from .extensions import CY_ORDER, _phone
from .hfps import load_investigation_config

SEP_FEB_SLOTS = {5, 6, 1}  # Sep-Oct, Nov-Dec, Jan-Feb


def _hhs_bin(phone, base, c, kind, yr, slots):
    sel = (phone["year"] == yr) if kind == "year" else (phone["cy"] == yr)
    sub = phone[(phone["country"] == c) & sel & phone["HHS"].notna()]
    w = sub.pivot_table(index="id", columns="slot", values="HHS", aggfunc="first").reindex(columns=slots)
    fr = base[base["country"] == c].set_index("id")[["village_id"]].join(w, how="left")
    b = fr.drop(columns="village_id")
    b = (b >= 2).astype(float).where(b.notna()).dropna()
    return b.to_numpy().astype(int), fr.loc[b.index, "village_id"].to_numpy()


def _hfps_bin(h, rounds, item, group=None):
    from . import hfps
    m = hfps.matrix(h, rounds, item).dropna()
    if group is not None:
        m = m[h.static.loc[m.index, "sample_type"] == group]
    return m.to_numpy().astype(int), h.static.loc[m.index, "district"].to_numpy()


def _compare(H, clusters, labels, boot, meta):
    pos = (H.max(axis=1) > 0).astype(float)
    rm, _ = sm.household_terms(H, m=1)
    stats = {"random": (rm, pos)}
    for j, lab in enumerate(labels):
        stats[lab] = (pos * (H[:, j] == 0), pos)
    reps, _ = sm.ratio_bootstrap(clusters, stats, boot["draws"], boot["seed"])
    miss = {lab: float(stats[lab][0].sum() / pos.sum()) for lab in labels}
    best = min(labels, key=lambda lab: (miss[lab], labels.index(lab)))
    rnd = float(rm.sum() / pos.sum())
    rows = []
    for lab in labels:
        d_best = reps[lab] - reps[best]
        d_rand = reps[lab] - reps["random"]
        rows.append({**meta, "window": lab, "is_best_observed": lab == best, "n_complete": len(H),
                     "n_reference_positive": int(pos.sum()), "missed": miss[lab],
                     "missed_ci_low": sm.interval(reps[lab], boot["level"])[0], "missed_ci_high": sm.interval(reps[lab], boot["level"])[1],
                     "random_missed": rnd, "diff_vs_random": miss[lab] - rnd,
                     "diff_vs_random_ci_low": sm.interval(d_rand, boot["level"])[0], "diff_vs_random_ci_high": sm.interval(d_rand, boot["level"])[1],
                     "diff_vs_best_observed": miss[lab] - miss[best],
                     "diff_vs_best_ci_low": sm.interval(d_best, boot["level"])[0] if lab != best else 0.0,
                     "diff_vs_best_ci_high": sm.interval(d_best, boot["level"])[1] if lab != best else 0.0,
                     "separable_from_best_at_95": bool(lab != best and sm.interval(d_best, boot["level"])[0] > 0)})
    return rows


def window_comparisons(paths: Paths, boot: dict) -> pd.DataFrame:
    cfg = load_config(paths.config)
    phone, base = _phone(paths, cfg)
    rows = []
    for c, kind, yr, slots, label in (("Malawi", "cy", 2020, CY_ORDER, "Jul 2020 - Jun 2021 (six windows)"),
                                      ("Malawi", "cy", 2019, CY_ORDER, "Jul 2019 - Jun 2020 (six windows)"),
                                      ("Malawi", "year", 2020, [1, 2, 3, 4, 5, 6], "calendar 2020 (six windows)"),
                                      ("Malawi", "year", 2021, [1, 2, 3, 4], "Jan - Aug 2021 (four windows)")):
        H, cl = _hhs_bin(phone, base, c, kind, yr, slots)
        rows += _compare(H, cl, [bp.SLOT_LABELS[s] for s in slots], boot,
                         {"dataset": "Aggarwal trial (HHS >= 2)", "horizon": label, "cluster_unit": "village"})
    from . import hfps
    hcfg = load_investigation_config(paths)["hfps"]
    if (paths.root / hcfg["extracted_dir"]).exists():
        h = hfps.load(hcfg, paths.root)
        for rounds, group, label in (([7, 8, 9, 11, 12], None, "2021 rounds 7/8/9/11/12"), ([7, 9, 11], None, "2021 rounds 7/9/11"),
                                     ([18, 19, 21], 2.0, "Jun 2023 / Dec 2023 / Apr 2024 (group B)")):
            H, cl = _hfps_bin(h, rounds, "s8q7", group)
            rows += _compare(H, cl, [h.labels[r] for r in rounds], boot,
                             {"dataset": "World Bank HFPS (FIES item: hungry but did not eat)", "horizon": label,
                              "cluster_unit": "district"})
    return pd.DataFrame(rows)


def season_groups(windows: pd.DataFrame, boot_note: str = "") -> pd.DataFrame:
    """Exploratory: mean missed share of Sep-Feb windows minus Mar-Aug windows (point estimates only)."""
    rows = []
    sepfeb_labels = {bp.SLOT_LABELS[s] for s in SEP_FEB_SLOTS}
    for (ds, hz), g in windows.groupby(["dataset", "horizon"], sort=False):
        if ds.startswith("Aggarwal"):
            grp = g.window.isin(sepfeb_labels)
        else:
            months = g.window.str.extract(r"R\d+ (\w{3})")[0]
            grp = months.isin(["Sep", "Oct", "Nov", "Dec", "Jan", "Feb"])
        a, b = g[grp], g[~grp]
        rows.append({"dataset": ds, "horizon": hz, "sep_feb_windows": ", ".join(a.window), "mar_aug_windows": ", ".join(b.window),
                     "mean_missed_sep_feb": a.missed.mean() if len(a) else np.nan,
                     "mean_missed_mar_aug": b.missed.mean() if len(b) else np.nan,
                     "difference": (a.missed.mean() - b.missed.mean()) if len(a) and len(b) else np.nan,
                     "balanced_design": len(a) == len(b),
                     "status": "exploratory post hoc description; not a test; window availability differs by horizon"})
    return pd.DataFrame(rows)


def second_contact_table(paths: Paths) -> pd.DataFrame:
    inv, mc = paths.public / "investigation", paths.public / "multicountry"
    rows = []
    mv = pd.read_csv(inv / "hfps_model_vs_rule.csv")
    for _, r in mv.iterrows():
        rows.append({"dataset": "World Bank Malawi HFPS 2021", "item": r["item"], "first_contact": "R7 (Jan 2021)", "later_contacts": "R9, R11",
                     "budget": f"{r.budget_definition} ({int(r.recontact_budget)})", "rule": r.rule,
                     "later_positives_per_100_recontacted": r.captured_per_100_recontacted, "ci": "", "evidence_class": "out-of-time model training (2020), not blind"})
    sc = pd.read_csv(inv / "hfps_second_contact.csv")
    for _, r in sc[sc.rule.str.startswith("poorest")].iterrows():
        rows.append({"dataset": "World Bank Malawi HFPS 2021", "item": r["item"], "first_contact": "R7 (Jan 2021)",
                     "later_contacts": r.analysis.split("later ")[-1], "budget": f"budget = all warning-sign negatives ({int(r.recontact_budget_households)})",
                     "rule": r.rule, "later_positives_per_100_recontacted": r.captured_per_100_recontacted, "ci": "",
                     "evidence_class": "exploratory"})
    ag = pd.read_csv(inv / "aggarwal_second_contact.csv")
    for (an, rule), g in ag.groupby(["analysis", "rule"], sort=False):
        r = g.iloc[0]
        ci = f"{r.warning_minus_random_per_100_ci_low:+.1f} to {r.warning_minus_random_per_100_ci_high:+.1f} (warning minus random)" if rule.startswith("warning") else ""
        rows.append({"dataset": "Aggarwal trial (HHS)", "item": "HHS >= 2; warning = HHS 1", "first_contact": an.split(":")[1].split(",")[0].strip(),
                     "later_contacts": an.split("later windows ")[-1], "budget": f"budget = all HHS-1 negatives ({int(r.recontact_budget_households)})",
                     "rule": rule, "later_positives_per_100_recontacted": r.captured_per_100_recontacted, "ci": ci, "evidence_class": "exploratory"})
    h3 = pd.read_csv(mc / "h3_second_contact.csv").dropna(subset=["difference"])
    for _, r in h3.iterrows():
        for rule, val in (("warning-sign rule", r.warning_per_100), ("random among negatives (exact expectation)", r.random_per_100)):
            rows.append({"dataset": f"Locked multi-country test: {r.country} {r.horizon_start_year}", "item": "FIES item 7", "first_contact": f"R{r.first_round}",
                         "later_contacts": "remaining horizon rounds", "budget": f"budget = all warning-sign negatives ({int(r.recontact_budget)})",
                         "rule": rule, "later_positives_per_100_recontacted": val,
                         "ci": f"{r.ci_low:+.1f} to {r.ci_high:+.1f} (warning minus random)" if rule.startswith("warning") else "",
                         "evidence_class": "protocol-locked (H3) primary" if r.analysis.startswith("primary") else "sensitivity (D2)"})
    return pd.DataFrame(rows)


def h2_h4_table(paths: Paths) -> pd.DataFrame:
    mc = paths.public / "multicountry"
    rows = []
    h2 = pd.read_csv(mc / "h2_transfer.csv")
    for _, r in h2.iterrows():
        rows.append({"hypothesis": "H2 data-driven transfer", "country": r.country, "horizons": f"{r.train_horizon}-{str(r.train_horizon + 1)[2:]} to {r.test_horizon}-{str(r.test_horizon + 1)[2:]}",
                     "eligible": bool(r.testable), "denominator": f"{int(r.n_test_reference_positive)} reference positives of {int(r.n_test_complete)} complete",
                     "estimand": "missed share, frozen round minus random round (pp)", "estimate_pp": 100 * r.frozen_minus_random,
                     "ci_low_pp": 100 * r.ci_low, "ci_high_pp": 100 * r.ci_high,
                     "direction": "frozen better" if r.frozen_minus_random < 0 else "frozen worse", "status": "prespecified (H2)",
                     "interpretation": "inconclusive (interval includes zero)" if r.ci_low < 0 < r.ci_high else "interval excludes zero",
                     "source": "data/public_aggregates/multicountry/h2_transfer.csv"})
    rows.append({"hypothesis": "H2 data-driven transfer", "country": "BFA, ETH, NGA, TZA", "horizons": "-", "eligible": False, "denominator": "-",
                 "estimand": "-", "estimate_pp": np.nan, "ci_low_pp": np.nan, "ci_high_pp": np.nan, "direction": "-", "status": "prespecified (H2)",
                 "interpretation": "untestable: fewer than two usable horizons in the same panel (BFA, ETH) or no usable horizon (NGA, TZA)",
                 "source": "data/public_aggregates/multicountry/horizons.csv"})
    rows.append({"hypothesis": "H2 pandemic-onset comparison", "country": "all", "horizons": "-", "eligible": False, "denominator": "-", "estimand": "-",
                 "estimate_pp": np.nan, "ci_low_pp": np.nan, "ci_high_pp": np.nan, "direction": "-", "status": "prespecified (H2, descriptive)",
                 "interpretation": "untestable: no testable pair had a pandemic-onset-flagged training horizon", "source": "h2_transfer.csv"})
    h1 = pd.read_csv(mc / "h1_calendar_rule.csv")
    for _, r in h1.iterrows():
        prim = r.analysis.startswith("primary")
        rows.append({"hypothesis": "H4 rural minus urban (rule minus random)", "country": r.country,
                     "horizons": f"{r.horizon_start_year}-{str(r.horizon_start_year + 1)[2:]}", "eligible": True,
                     "denominator": f"{int(r.n_reference_positive_rural)} rural / {int(r.n_reference_positive_urban)} urban reference positives",
                     "estimand": "difference in (rule minus random) missed share, rural minus urban (pp)",
                     "estimate_pp": 100 * r.rural_minus_urban, "ci_low_pp": 100 * r.rural_minus_urban_ci_low, "ci_high_pp": 100 * r.rural_minus_urban_ci_high,
                     "direction": "rule relatively better for rural" if r.rural_minus_urban < 0 else "rule relatively better for urban",
                     "status": "prespecified (H4, exploratory)" if prim else "sensitivity (D2)",
                     "interpretation": "inconclusive (interval includes zero)" if r.rural_minus_urban_ci_low < 0 < r.rural_minus_urban_ci_high else "interval excludes zero",
                     "source": "data/public_aggregates/multicountry/h1_calendar_rule.csv"})
    return pd.DataFrame(rows)


def run(paths: Paths | None = None) -> dict:
    paths = paths or Paths()
    boot = load_investigation_config(paths)["aggarwal_extensions"]["bootstrap"]
    out = paths.public / "review"
    out.mkdir(parents=True, exist_ok=True)
    w = window_comparisons(paths, boot)
    w.to_csv(out / "window_paired_comparisons.csv", index=False)
    season_groups(w).to_csv(out / "season_groups_exploratory.csv", index=False)
    second_contact_table(paths).to_csv(out / "second_contact_matched_budgets.csv", index=False)
    h2_h4_table(paths).to_csv(out / "h2_h4_results.csv", index=False)
    return {"written": ["window_paired_comparisons.csv", "season_groups_exploratory.csv", "second_contact_matched_budgets.csv", "h2_h4_results.csv"]}
