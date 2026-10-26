"""Manuscript-ready tables (CSV + Markdown) from data/public_aggregates."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .build_panels import SLOT_LABELS


def _pct(x, d=1):
    return "" if pd.isna(x) else f"{100 * x:.{d}f}%"


def _md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines) + "\n"


def _write(df: pd.DataFrame, out: Path, name: str, title: str, note: str) -> None:
    df.to_csv(out / f"{name}.csv", index=False)
    (out / f"{name}.md").write_text(f"**{title}**\n\n{_md(df)}\n*{note}*\n", encoding="utf-8")


def build_tables(pub: Path, out: Path) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    made = []

    flow = pd.read_csv(pub / "cohort_flow.csv")
    t1 = flow.pivot_table(index=["order", "step", "unit"], columns="country", values="count").reset_index()
    t1 = t1[["step", "unit", "Malawi", "Liberia"]].rename(columns={"step": "Step", "unit": "Unit"})
    _write(t1, out, "table1_cohort_flow", "Table 1. Cohort construction (aggregate counts)",
           "Baseline phone frame = control households selected for the household phone survey. One "
           "household-slot had two records; the earliest dated record was kept (outcome-blind).")
    made.append("table1_cohort_flow")

    f = pd.read_csv(pub / "frontier.csv")
    f = f[f.threshold == 2]
    rows = []
    for c in ("Malawi", "Liberia"):
        g = f[f.country == c]
        for _, r in g.iterrows():
            rows.append({"Country": c, "Screens retained (m)": int(r.m),
                         "Complete households": int(r.n_complete),
                         "Reference-positive": int(r.n_reference_positive),
                         "Missed (exact)": _pct(r.missed_fraction),
                         "95% village bootstrap": f"{_pct(r.ci_low)} – {_pct(r.ci_high)}",
                         "Expected households missed": f"{r.expected_missed_households:.1f}"})
    _write(pd.DataFrame(rows), out, "table2_main_frontier",
           "Table 2. Expected share of reference-positive households missed by m uniformly random screens of six",
           "Complete 2020 histories; reference-positive = HHS >= 2 in at least one of six two-month windows. "
           "Bootstrap: villages resampled with replacement within country, 2,000 draws, percentile intervals. "
           "Not prevalence, not annual incidence, not causal.")
    made.append("table2_main_frontier")

    mb = pd.read_csv(pub / "missing_bounds.csv")
    le = pd.read_csv(pub / "label_error_bounds.csv")
    le = le[le.scope == "frame_missing_arbitrary"]
    rows = []
    for c in ("Malawi", "Liberia"):
        for m in (1, 2, 3):
            b = mb[(mb.country == c) & (mb.m == m)].iloc[0]
            row = {"Country": c, "m": m, "Complete-history estimate": _pct(b.complete_case_point),
                   "Sharp bounds (missing arbitrary)": f"{_pct(b.lower)} – {_pct(b.upper)}",
                   "All missing negative": _pct(b.all_missing_negative),
                   "All missing positive": _pct(b.all_missing_positive)}
            for a in (0.01, 0.05, 0.10):
                e = le[(le.country == c) & (le.m == m) & (abs(le.alpha - a) < 1e-9)].iloc[0]
                row[f"+ {a:.0%} label budget"] = f"{_pct(e.lower)} – {_pct(e.upper)} ({int(e.budget_flips)} flips)"
            rows.append(row)
    _write(pd.DataFrame(rows), out, "table3_identification_bounds",
           "Table 3. Identification ranges over the full baseline phone frame (not confidence intervals)",
           "Frame: Malawi 297, Liberia 206 households. Missing 2020 windows may take any value; label budgets "
           "allow up to the stated share of observed binary screens per country to be misclassified (shared "
           "budget; hypothetical). Single imputations are shown to demonstrate they are not the sharp endpoints.")
    made.append("table3_identification_bounds")

    tc = pd.read_csv(pub / "timing_candidates.csv")
    tv = pd.read_csv(pub / "timing_validation.csv")
    rows = []
    for c in ("Malawi", "Liberia"):
        for y in (2020, 2021):
            g = tc[(tc.country == c) & (tc.year == y)]
            row = {"Country": c, "Year": y, "Complete (4 windows)": int(g.n_complete.iloc[0]),
                   "Reference-positive": int(g.n_reference_positive.iloc[0])}
            for _, r in g.iterrows():
                row[SLOT_LABELS[int(r.slot)]] = _pct(r.missed_fraction) + (" *" if r.selected else "")
            row["Random window"] = _pct(g.random_one_slot.iloc[0])
            rows.append(row)
    t4 = pd.DataFrame(rows)
    _write(t4, out, "table4_timing_candidates",
           "Table 4. Missed share for each single fixed window, 2020 (selection) and 2021 (frozen evaluation)",
           "* = window selected on 2020 data only (ties -> earlier window). 2021 values for non-selected windows "
           "are post hoc disclosure. Cohorts differ by year.")
    made.append("table4_timing_candidates")

    rows = []
    for _, r in tv.iterrows():
        if r.cohort == "Matched: 2020 performance of frozen slot":
            continue
        rows.append({"Country": r.country, "Cohort (2021)": r.cohort, "Frozen window": SLOT_LABELS[int(r.slot)],
                     "Complete": int(r.n_complete), "Reference-positive": int(r.n_reference_positive),
                     "Missed, frozen window": f"{_pct(r.missed_frozen)} ({_pct(r.frozen_ci_low)} – {_pct(r.frozen_ci_high)})",
                     "Missed, random window": f"{_pct(r.missed_random_one_slot)} ({_pct(r.random_ci_low)} – {_pct(r.random_ci_high)})",
                     "Difference (95% bootstrap)": f"{100 * (r.missed_frozen - r.missed_random_one_slot):.1f} pp "
                                                   f"({100 * r.diff_ci_low:.1f} to {100 * r.diff_ci_high:.1f})"})
    _write(pd.DataFrame(rows), out, "table5_timing_validation",
           "Table 5. Out-of-year evaluation of the 2020-selected window",
           "Brackets: 95% village-cluster percentile bootstrap (2,000 draws) holding the frozen window fixed. "
           "Liberia estimates rest on 22 and 13 reference-positive households.")
    made.append("table5_timing_validation")

    ab = pd.read_csv(pub / "attrition_balance.csv")
    ab = ab.assign(**{"Complete mean": ab.mean_complete.round(3), "Incomplete mean": ab.mean_incomplete.round(3),
                      "Difference (cluster SE)": [f"{d:.3f} ({s:.3f})" for d, s in zip(ab.difference, ab.cluster_se)],
                      "n complete / incomplete": [f"{a} / {b}" for a, b in zip(ab.n_complete, ab.n_incomplete)]})
    t6 = ab[["country", "covariate", "Complete mean", "Incomplete mean", "Difference (cluster SE)",
             "n complete / incomplete"]].rename(columns={"country": "Country", "covariate": "Baseline covariate"})
    _write(t6, out, "tableS1_attrition_balance",
           "Table S1. Baseline characteristics of complete versus incomplete 2020 histories",
           "Descriptive; differences from OLS on a completeness indicator with CR1 village-clustered SEs. Seven "
           "covariates x two countries: expect ~1 nominal |z|>2 by chance; not causal predictors.")
    made.append("tableS1_attrition_balance")

    ip = pd.read_csv(pub / "ipw_frontier.csv")
    mbm = mb.set_index(["country", "m"])
    rows = []
    for _, r in ip[ip.m <= 3].iterrows():
        b = mbm.loc[(r.country, r.m)]
        rows.append({"Country": r.country, "m": int(r.m), "Complete-case": _pct(b.complete_case_point),
                     "IPW (MAR given baseline)": _pct(r.ipw_missed_fraction),
                     "Sharp bounds": f"{_pct(b.lower)} – {_pct(b.upper)}",
                     "Max weight": f"{r.max_weight:.1f}", "Effective n (positives)": f"{r.effective_n_positive:.0f}"})
    _write(pd.DataFrame(rows), out, "tableS2_ipw_vs_bounds",
           "Table S2. Assumption-dependent IPW estimate versus assumption-free bounds",
           "IPW assumes completeness is independent of 2020 hunger history given seven baseline covariates; "
           "this is untestable here. Shown only as a secondary sensitivity point.")
    made.append("tableS2_ipw_vs_bounds")

    st = pd.read_csv(pub / "bootstrap_stability.csv")
    st = st[st.m <= 3].copy()
    st["interval"] = [("" if pd.isna(lo) else f"{_pct(lo, 2)} – {_pct(hi, 2)}") for lo, hi in zip(st.ci_low, st.ci_high)]
    st["SE"] = st.se.map(lambda s: f"{100 * s:.2f} pp")
    _write(st[["country", "m", "variant", "interval", "SE", "villages"]], out, "tableS3_bootstrap_stability",
           "Table S3. Monte Carlo and resampling-unit stability of the village bootstrap",
           "Primary: 2,000 draws over villages with >=1 complete household. Variants: 20,000 draws (different "
           "seed); all frame villages as units; delete-one-village jackknife SE.")
    made.append("tableS3_bootstrap_stability")

    rep = pd.read_csv(pub / "reproduction_comparison.csv")
    _write(rep, out, "tableS4_reproduction", "Table S4. Earlier exploratory values versus independent recomputation",
           "Tolerance: 0.05 pp for point estimates and bounds (reported to one decimal); 0.6 pp for bootstrap "
           "endpoints (Monte Carlo + implementation differences); exact for counts.")
    made.append("tableS4_reproduction")
    return made
