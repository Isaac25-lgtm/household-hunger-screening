"""Manuscript-facing tables, built only from data/public_aggregates.

Rounding convention (applies to every manuscript-facing number):
  * proportions are shown as percentages with one decimal place, computed from the stored unrounded value;
  * differences are computed from unrounded components and then rounded (never the difference of rounded values);
  * confidence-interval limits are rounded from their own unrounded values;
  * rates per 100 re-contacted households use one decimal place;
  * observed counts are integers; expected (fractional) counts keep one decimal place and are labelled "expected".
Rounding uses Python string formatting of the stored double to one decimal place.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def p1(x) -> str:
    return "" if pd.isna(x) else f"{100 * x:.1f}%"


def d1(x, scale=100.0) -> str:
    return "" if pd.isna(x) else f"{scale * x:+.1f}"


def ci1(lo, hi, scale=100.0) -> str:
    return "" if pd.isna(lo) else f"{scale * lo:+.1f} to {scale * hi:+.1f}"


def save(df: pd.DataFrame, out: Path, name: str, title: str, note: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    df = df.astype(object).where(df.notna(), "")
    df.to_csv(out / f"{name}.csv", index=False)
    md = f"**{title}**\n\n" + df.to_markdown(index=False, disable_numparse=True) + f"\n\n*{note}*\n"
    (out / f"{name}.md").write_text(md, encoding="utf-8")


def table2(pub: Path) -> pd.DataFrame:
    f = pd.read_csv(pub / "frontier.csv")
    f = f[f.threshold == 2]
    mb = pd.read_csv(pub / "missing_bounds.csv")
    sc = pd.read_csv(pub / "review" / "missing_bounds_second_scope.csv")
    rows = []
    for c in ("Malawi", "Liberia"):
        for m in (1, 2, 3):
            r = f[(f.country == c) & (f.m == m)].iloc[0]
            rows.append({"Panel": "A. Complete observed 2020 histories (sampling uncertainty)", "Country": c, "Screens retained of 6": m,
                         "Households": int(r.n_complete), "Reference-positive households": int(r.n_reference_positive),
                         "Missed share or range": p1(r.missed_fraction),
                         "Uncertainty": f"95% village bootstrap CI {100 * r.ci_low:.1f} to {100 * r.ci_high:.1f}%",
                         "Expected households missed": f"{r.expected_missed_households:.1f} (expected)"})
    for c in ("Malawi", "Liberia"):
        for m in (1, 2, 3):
            r = mb[(mb.country == c) & (mb.m == m)].iloc[0]
            s = sc[(sc.country == c) & (sc.m == m) & sc.scope.str.startswith("households with")].iloc[0]
            rows.append({"Panel": "B. Full baseline frame, missing interviews unrestricted (identification, not a CI)", "Country": c,
                         "Screens retained of 6": m, "Households": int(r.frame_households),
                         "Reference-positive households": f"{int(r.lower_n_reference_positive)} to {int(r.upper_n_reference_positive)} (depends on completion)",
                         "Missed share or range": f"{100 * r.lower:.1f} to {100 * r.upper:.1f}%",
                         "Uncertainty": f"identification range; {int(r.households_never_observed)} never observed; excluding them: "
                                        f"{100 * s.lower:.1f} to {100 * s.upper:.1f}% ({int(s.households)} households)",
                         "Expected households missed": ""})
    return pd.DataFrame(rows)


def table3(pub: Path) -> pd.DataFrame:
    inv, rv = pub / "investigation", pub / "review"
    w = pd.read_csv(rv / "window_paired_comparisons.csv")
    fp = pd.read_csv(rv / "frozen_best_pair.csv").iloc[0]
    cal = pd.read_csv(rv / "calendar_lean_season_sensitivity.csv")
    tt = pd.read_csv(inv / "hfps_transfer_tests.csv")
    rows = []
    A = "A. Aggarwal trial, Malawi: Household Hunger Scale (HHS 2 or more)"
    B = "B. World Bank HFPS, Malawi: single FIES item 'hungry but did not eat' (not the HHS)"

    def wrow(panel, period, hz, window, cls, note):
        r = w[(w.horizon == hz) & (w.window == window)].iloc[0]
        return {"Panel": panel, "Analysis period": period, "Reference": hz.split("(")[-1].rstrip(")") if "(" in hz else hz,
                "Complete households": int(r.n_complete), "Reference-positive households": int(r.n_reference_positive),
                "Contact window": window, "Window missed": p1(r.missed), "Random missed": p1(r.random_missed),
                "Difference (pp)": d1(r.diff_vs_random), "95% CI (pp)": ci1(r.diff_vs_random_ci_low, r.diff_vs_random_ci_high),
                "Evidence class": cls, "Note": note}

    lead = w[w.horizon == "Jul 2020 - Jun 2021 (six windows)"]
    best = lead[lead.is_best_observed].iloc[0]
    tied = " and ".join(lead[~lead.is_best_observed & ~lead.separable_from_best_at_95].window)
    rows.append(wrow(A, "Jul 2020 - Jun 2021 (lead result)", "Jul 2020 - Jun 2021 (six windows)", "Jan-Feb", "Out-of-time (chosen on Jul 2019 - Jun 2020), not blind",
                     f"Best observed window here is {best.window} ({p1(best.missed)}); {tied} not separable from it (Table S17)"))
    r21 = wrow(A, "Jan - Aug 2021 (restricted)", "Jan - Aug 2021 (four windows)", "Jan-Feb", "Out-of-time (chosen on 2020), not blind",
               "Four-window reference: not comparable with the six-window rows")
    tv = pd.read_csv(pub / "timing_validation.csv")
    tv = tv[(tv.country == "Malawi") & (tv.cohort == "2021 complete four-slot cohort")].iloc[0]
    r21["95% CI (pp)"] = ci1(tv.diff_ci_low, tv.diff_ci_high)  # canonical: primary pipeline (see NUMERICAL_RECONCILIATION)
    rows.append(r21)
    rows.append(wrow(A, "Jul 2019 - Jun 2020", "Jul 2019 - Jun 2020 (six windows)", "Jan-Feb", "Exploratory, in-sample (training year)", "Jan-Feb separable from every other window"))
    rows.append(wrow(A, "Calendar 2020", "calendar 2020 (six windows)", "Jan-Feb", "Exploratory, in-sample", "Original exploratory finding"))
    rows.append({"Panel": A, "Analysis period": "Jul 2020 - Jun 2021, two contacts", "Reference": "six windows",
                 "Complete households": int(fp.n_test_complete), "Reference-positive households": int(fp.n_test_reference_positive),
                 "Contact window": fp.selected_pair, "Window missed": p1(fp.test_missed_frozen_pair), "Random missed": p1(fp.test_missed_random_pair) + " (random pair)",
                 "Difference (pp)": d1(fp["diff"]), "95% CI (pp)": ci1(fp.diff_ci_low, fp.diff_ci_high),
                 "Evidence class": "Out-of-time (pair chosen on Jul 2019 - Jun 2020), not blind", "Note": "The in-sample 2020 best pair (Jan-Feb + Mar-Apr) is not used"})
    for _, r in cal[cal.country == "Liberia"].iterrows():
        rows.append({"Panel": "A2. Aggarwal trial, Liberia (secondary)", "Analysis period": r.horizon.split(" (")[0],
                     "Reference": {4: "four windows", 6: "six windows"}[int(r.reference_windows)],
                     "Complete households": int(r.n_complete), "Reference-positive households": int(r.n_reference_positive),
                     "Contact window": r.calendar_window, "Window missed": p1(r.window_missed), "Random missed": p1(r.random_missed),
                     "Difference (pp)": d1(r["diff"]), "95% CI (pp)": ci1(r.diff_ci_low, r.diff_ci_high),
                     "Evidence class": "Calendar-based sensitivity (FEWS NET lean season Jun-Aug), not blind", "Note": "Does not beat random"})
    rows.append(wrow(B, "2021 (Jan, Apr, late May-Jun rounds)", "2021 rounds 7/9/11", "R7 Jan 2021", "Exploratory, in-sample", "January round best of three"))
    rows.append(wrow(B, "2021 (five rounds)", "2021 rounds 7/8/9/11/12", "R8 Mar 2021", "Exploratory, in-sample", "Best observed round is late Feb - mid Mar"))
    r7 = w[(w.horizon == "2021 rounds 7/8/9/11/12") & (w.window == "R7 Jan 2021")].iloc[0]
    rows.append(wrow(B, "2021 (five rounds)", "2021 rounds 7/8/9/11/12", "R7 Jan 2021", "Exploratory, in-sample",
                     f"Worse than the best observed round ({d1(r7.diff_vs_best_observed)} pp, Table S17)"))
    names = {"HFPS 2020 -> 2021 (reproduction)": ("2020 rounds -> 2021", "Out-of-time (chosen on 2020), not blind"),
             "HFPS matched Jun/Dec/Apr, 2020-21 -> 2023-24, group B": ("Jun/Dec/Apr 2020-21 -> 2023-24, group B", "Out-of-time, calendar-matched, not blind"),
             "HFPS matched, training June = round 11 (pandemic-onset round excluded)": ("Same, June 2020 round replaced by June 2021", "Out-of-time, calendar-matched, not blind"),
             "HFPS matched Jun/Feb-Mar, 2020-21 -> 2023-24, group A": ("Jun/Feb-Mar 2020-21 -> 2023-24, group A", "Out-of-time, calendar-matched, not blind")}
    t = tt[(tt["item"] == "s8q7") & tt.selected_on_train & tt.test_missed.notna()]
    for _, r in t.iterrows():
        if r.test not in names:
            continue
        period, cls = names[r.test]
        rows.append({"Panel": B, "Analysis period": period, "Reference": "test-year rounds",
                     "Complete households": int(r.n_test_complete), "Reference-positive households": int(r.n_test_reference_positive),
                     "Contact window": f"{r.candidate} (chosen in training)", "Window missed": p1(r.test_missed), "Random missed": p1(r.test_random_missed),
                     "Difference (pp)": d1(r.diff_vs_random), "95% CI (pp)": ci1(r.diff_ci_low, r.diff_ci_high), "Evidence class": cls,
                     "Note": "Failed transfer" if r.diff_vs_random > 0 else "Transfer held"})
    return pd.DataFrame(rows)


def table4(pub: Path) -> pd.DataFrame:
    mc = pub / "multicountry"
    h1 = pd.read_csv(mc / "h1_calendar_rule.csv")
    h3 = pd.read_csv(mc / "h3_second_contact.csv")
    names = {"BFA": "Burkina Faso", "UGA": "Uganda", "ETH": "Ethiopia"}
    rows = []

    def yr(y):
        return f"{int(y)}-{str(int(y) + 1)[2:]}"

    for prim in (True, False):
        for _, r in h1[h1.analysis.str.startswith("primary") == prim].iterrows():
            rows.append({"Status": "Primary (prespecified)" if prim else "Sensitivity (deviation D2)", "Hypothesis": "H1 calendar rule",
                         "Country and horizon": f"{names[r.country]} {yr(r.horizon_start_year)}", "Contact chosen": r.rule_round,
                         "Denominator": f"{int(r.n_reference_positive)} reference positives", "Rule": p1(r.rule_missed) + " missed",
                         "Random": p1(r.random_missed) + " missed", "Difference": d1(r["diff"]) + " pp",
                         "95% CI": ci1(r.diff_ci_low, r.diff_ci_high) + " pp",
                         "Reading": ("rule worse than random" if r.diff_ci_low > 0 else "inconclusive" if r.diff_ci_low < 0 < r.diff_ci_high else "rule better than random")})
        for _, r in h3[(h3.analysis.str.startswith("primary") == prim)].iterrows():
            if pd.isna(r.difference):
                rows.append({"Status": "Primary (prespecified)", "Hypothesis": "H3 second-contact rule", "Country and horizon": f"{names[r.country]} {yr(r.horizon_start_year)}",
                             "Contact chosen": f"first contact R{r.first_round}", "Denominator": "-", "Rule": "-", "Random": "-", "Difference": "-", "95% CI": "-",
                             "Reading": "untestable: first round asked only FIES items 6 to 8"})
                continue
            rows.append({"Status": "Primary (prespecified)" if prim else "Sensitivity (deviation D2)", "Hypothesis": "H3 second-contact rule",
                         "Country and horizon": f"{names[r.country]} {yr(r.horizon_start_year)}", "Contact chosen": f"first contact R{r.first_round}",
                         "Denominator": f"{int(r.recontact_budget)} re-contacted", "Rule": f"{r.warning_per_100:.1f} per 100",
                         "Random": f"{r.random_per_100:.1f} per 100", "Difference": f"{r.difference:+.1f} per 100",
                         "95% CI": f"{r.ci_low:+.1f} to {r.ci_high:+.1f} per 100",
                         "Reading": "rule better than random" if r.ci_low > 0 else "inconclusive"})
    for c, hyp, why in (("Ethiopia", "H1", "excluded from H1 by protocol (no single national lean season); H3 untestable (row above)"),
                        ("Nigeria (both panels)", "H1 and H3", "no usable horizon (at most two food-security rounds per year)"),
                        ("Tanzania", "H1 and H3", "no usable horizon (subsample module; round 9 file truncated in the official release)")):
        rows.append({"Status": "Not eligible", "Hypothesis": hyp, "Country and horizon": c, "Contact chosen": "-", "Denominator": "-",
                     "Rule": "-", "Random": "-", "Difference": "-", "95% CI": "-", "Reading": why})
    out = pd.DataFrame(rows)
    d2 = out.Status.str.startswith("Sensitivity")
    key = out.Hypothesis + out["Country and horizon"]
    for k in key[d2].unique():
        idx = out.index[d2 & (key == k)]
        if len(idx) > 1:
            for j, i in enumerate(idx, 1):
                out.loc[i, "Country and horizon"] += f" (sample group {j})"
    return out


def build(pub: Path, out_main: Path, out_supp: Path) -> list[str]:
    made = []
    save(table2(pub), out_main, "table2_frequency_frontier_and_identification",
         "Table 2. Households missed when screens are retained at random: complete-history estimates (A) and full-frame identification ranges (B)",
         "Aggarwal trial, 2020, six two-month windows, HHS 2 or more. Panel A: exact estimate for households observed in all six windows, with 95% "
         "village-cluster bootstrap CIs (sampling uncertainty). Panel B: sharp range over every completion of missing interviews for all baseline-frame "
         "households (identification uncertainty, not a confidence interval). The two panels refer to different populations.")
    made.append("table2_frequency_frontier_and_identification")
    save(table3(pub), out_main, "table3_timing_two_malawi_panels",
         "Table 3. Single-contact timing against random timing in two Malawi panels, by evidence class",
         "Panel A uses the Household Hunger Scale; panel B uses one FIES item. The outcomes are different and are not pooled. Rows with different "
         "reference periods are not directly comparable. 95% cluster-bootstrap CIs (villages in A, districts in B; B is approximate). No row is blind.")
    made.append("table3_timing_two_malawi_panels")
    save(table4(pub), out_main, "table4_protocol_locked_multicountry_tests",
         "Table 4. Protocol-locked multi-country tests: five countries assessed, two with eligible primary calendar-test (H1) horizons",
         "Protocol committed before access to household- and item-level outcomes, with prior exposure to some published aggregate charts. Item: "
         "'hungry but did not eat' (FIES item 7). H1 decision under the prespecified rule: contradicted (two eligible horizons; Uganda individually "
         "inconclusive). H3 decision: supported directionally (3 of 3 primary horizons positive; one interval includes zero). D2 rows are sensitivity "
         "analyses only. H2 and H4: Table S15.")
    made.append("table4_protocol_locked_multicountry_tests")
    rv = pub / "review"
    h = pd.read_csv(rv / "h2_h4_results.csv")
    for col in ("estimate_pp", "ci_low_pp", "ci_high_pp"):
        h[col] = h[col].map(lambda v: "" if pd.isna(v) else f"{v:+.1f}")
    save(h, out_supp, "tableS15_h2_h4_prespecified_results", "Table S15. Prespecified hypotheses H2 (transfer) and H4 (rural vs urban), including untestable comparisons",
         "Percentage points. H4 was prespecified as exploratory. Source files listed per row.")
    made.append("tableS15_h2_h4_prespecified_results")
    s = pd.read_csv(rv / "second_contact_matched_budgets.csv")
    s["later_positives_per_100_recontacted"] = s.later_positives_per_100_recontacted.map(lambda v: f"{v:.1f}")
    save(s, out_supp, "tableS16_second_contact_matched_budgets", "Table S16. Every executed second-contact comparison, at matched re-contact budgets",
         "Yield per 100 re-contacted households is a contact-efficiency measure, not a monetary cost. Random rows are exact expectations.")
    made.append("tableS16_second_contact_matched_budgets")
    w = pd.read_csv(rv / "window_paired_comparisons.csv")
    wt = w[["dataset", "horizon", "window", "is_best_observed", "n_reference_positive"]].copy()
    wt["missed"] = w.missed.map(p1)
    wt["diff_vs_random_pp"] = w.diff_vs_random.map(d1)
    wt["ci_vs_random_pp"] = [ci1(a, b) for a, b in zip(w.diff_vs_random_ci_low, w.diff_vs_random_ci_high)]
    wt["diff_vs_best_observed_pp"] = w.diff_vs_best_observed.map(d1)
    wt["paired_ci_vs_best_pp"] = [ci1(a, b) if not best else "" for a, b, best in zip(w.diff_vs_best_ci_low, w.diff_vs_best_ci_high, w.is_best_observed)]
    wt["separable_from_best_at_95"] = w.separable_from_best_at_95
    save(wt, out_supp, "tableS17_window_paired_comparisons", "Table S17. Every evaluated contact window, with paired comparisons against the best observed window",
         "Paired cluster bootstrap. 'Best observed' is the lowest point estimate, not a demonstrated optimum. For Jan - Aug 2021 the "
         "interval against random comes from a separate bootstrap run and differs from the canonical Table 3 interval by up to 0.4 pp.")
    made.append("tableS17_window_paired_comparisons")
    g = pd.read_csv(rv / "season_groups_exploratory.csv")
    for col in ("mean_missed_sep_feb", "mean_missed_mar_aug"):
        g[col] = g[col].map(p1)
    g["difference"] = g["difference"].map(d1)
    save(g, out_supp, "tableS18_season_groups_exploratory", "Table S18. EXPLORATORY, POST HOC: September-February vs March-August windows",
         "Suggested during review after the window results were known. A description, not a test; window availability is unbalanced in most horizons.")
    made.append("tableS18_season_groups_exploratory")
    return made


def supplementary(pub: Path, out: Path) -> list[str]:
    """Supplementary tables S5 to S14, formatted with the same rounding convention."""
    inv, mc, rv = pub / "investigation", pub / "multicountry", pub / "review"
    made = []

    def put(df, name, title, note):
        save(df, out, name, title, note)
        made.append(name)

    def rng(lo, hi):
        return [f"{100 * a:.1f} to {100 * c:.1f}%" for a, c in zip(lo, hi)]

    def cis(lo, hi):
        return [ci1(a, c) for a, c in zip(lo, hi)]

    b = pd.read_csv(rv / "missing_bounds_second_scope.csv")
    put(pd.DataFrame({"Country": b.country, "Scope": b.scope, "Households": b.households.astype(int),
                      "Never observed": b.never_observed.astype(int), "Screens retained of 6": b.m.astype(int),
                      "Identification range": rng(b.lower, b.upper)}),
        "tableS5_bounds_second_scope",
        "Table S5. Missing-history identification ranges, all frame households vs households observed at least once (2020)",
        "Exact identification ranges, not confidence intervals.")
    s = pd.read_csv(rv / "single_window_positives.csv")
    put(pd.DataFrame({"Country": s.country, "Reference": s.reference, "Complete households": s.n_complete,
                      "Reference positive": s.reference_positive, "Positive in one window only": s.positive_in_one_window,
                      "Single-window positives scoring exactly 2": s.single_positive_with_score_exactly_2,
                      "Random missed, 1 screen": s.random_missed_m1.map(p1), "Random missed, 2 screens": s.random_missed_m2.map(p1),
                      "Random missed, 3 screens": s.random_missed_m3.map(p1), "Calendar window": s.calendar_window,
                      "Calendar window missed": s.calendar_window_missed.map(p1),
                      "Difference vs random (pp)": s.calendar_diff_vs_random.map(d1), "95% CI (pp)": cis(s.diff_ci_low, s.diff_ci_high)}),
        "tableS6_single_window_positives",
        "Table S6. Single-window positives and the persistent-only reference (calendar 2020, six windows)",
        "Persistent-only reference: households positive in at least two of six 2020 windows. Count columns refer to all reference "
        "positives. 95% village bootstrap.")
    e = pd.read_csv(rv / "random_error_simulation.csv")
    put(pd.DataFrame({"Horizon": e.horizon, "Window": e.calendar_window,
                      "Hypothetical flip rate per answer": e.error_rate_per_answer.map(lambda v: f"{100 * v:.0f}%"),
                      "Simulations": e.simulations.astype(int), "Mean difference vs random (pp)": e.mean_diff.map(d1),
                      "2.5th to 97.5th simulation percentile (pp)": cis(e.p2_5, e.p97_5),
                      "Simulations with difference 0 or more": (e.share_sims_diff_ge_0 * e.simulations).round().astype(int)}),
        "tableS7_random_error_simulation", "Table S7. Malawi calendar-window advantage under hypothetical random answer error",
        "Flip rates are hypothetical, not estimated error rates. Percentiles describe simulation spread, not sampling uncertainty.")
    put(pd.read_csv(rv / "hhs_scoring_check_records.csv"), "tableS8_hhs_scoring_check", "Table S8. HHS scoring check against item counts",
        "Consistent with standard FANTA scoring built from the 'no food' item. Counts are records (household-rounds).")
    r = pd.read_csv(rv / "recall_overlap_discordance.csv")
    put(pd.DataFrame({"Item": r["item"].map({"s8q7": "FIES 7: hungry but did not eat", "s8q8": "FIES 8: whole day without eating"}),
                      "Household pairs under 30 days apart": r.pairs_under_30_days.astype(int), "Discordance": r.discordance.map(p1),
                      "Yes then no": r.yes_then_no.astype(int), "No then yes": r.no_then_yes.astype(int)}),
        "tableS9_recall_overlap_discordance",
        "Table S9. Answer discordance between World Bank Malawi rounds 11 and 12 under 30 days apart",
        "Discordance mixes real change, recall differences and reporting error; it is not a misclassification rate.")
    h = pd.read_csv(inv / "hfps_single_round.csv")
    put(pd.DataFrame({"Cohort": h.cohort, "Item": h["item"], "Round": h.schedule, "Complete households": h.n_complete.astype(int),
                      "Reference positive": h.n_reference_positive.astype(int), "Missed households": [f"{v:.1f} (expected)" if str(sc).startswith("random") else f"{round(v):d}"
                                            for v, sc in zip(h.n_missed, h.schedule)],
                      "Missed": h.missed_share.map(p1), "95% CI": rng(h.missed_ci_district_low, h.missed_ci_district_high),
                      "Difference vs random (pp)": h.diff_vs_random.map(d1),
                      "95% CI (pp)": cis(h.diff_ci_district_low, h.diff_ci_district_high)}),
        "tableS10_worldbank_malawi_single_round", "Table S10. World Bank Malawi: single-round missed share against random",
        "District-cluster bootstrap (approximate; no PSU in public files). FIES items are not the HHS.")
    t = pd.read_csv(inv / "hfps_transfer_tests.csv")
    t = t[t.selected_on_train & t.test_missed.notna()]
    put(pd.DataFrame({"Test": t.test, "Item": t["item"], "Chosen in training": t.candidate, "Training missed": t.train_missed.map(p1),
                      "Test round": t.test_round.astype(int), "Test complete": t.n_test_complete.astype(int),
                      "Test reference positive": t.n_test_reference_positive.astype(int), "Test missed": t.test_missed.map(p1),
                      "Random missed": t.test_random_missed.map(p1), "Difference (pp)": t.diff_vs_random.map(d1),
                      "95% CI (pp)": cis(t.diff_ci_low, t.diff_ci_high)}),
        "tableS11_worldbank_transfer_tests",
        "Table S11. World Bank Malawi transfer tests (round selected in training, evaluated in test)",
        "Not blind: round-level rates had been seen. Positive differences are failed transfers.")
    m = pd.read_csv(inv / "hfps_model_vs_rule.csv")
    put(pd.DataFrame({"Item": m["item"], "Training": m.train_problem, "Test": m.test_problem, "Test negatives": m.n_test_negatives.astype(int),
                      "Budget": m.budget_definition, "Re-contacted": m.recontact_budget.astype(int), "Rule": m.rule,
                      "Later positives captured (expected)": m.expected_captured.map(lambda v: f"{v:.1f}"),
                      "Per 100 re-contacted": m.captured_per_100_recontacted.map(lambda v: f"{v:.1f}")}),
        "tableS12_model_vs_rule", "Table S12. Second-contact targeting: logistic model vs simple rules at matched budgets",
        "Logistic model trained on 2020 rounds only. Ties are split, so captured counts are expectations. "
        "Not a cost-effectiveness measure.")
    g = pd.read_csv(inv / "hfps_subgroups.csv")
    g[["fixed_round", "small_cell_flag"]] = g[["fixed_round", "small_cell_flag"]].astype(object).where(g[["fixed_round", "small_cell_flag"]].notna(), "")
    put(pd.DataFrame({"Item": g["item"], "Group": g.group, "Complete": g.n_complete.map(lambda v: "" if pd.isna(v) else f"{int(v)}"),
                      "Reference positive": g.n_reference_positive.map(lambda v: "" if pd.isna(v) else f"{int(v)}"), "Round": g.fixed_round,
                      "Round missed": g.fixed_missed.map(p1), "Random missed": g.random_missed.map(p1),
                      "Difference (pp)": g.diff_vs_random.map(d1), "95% CI (pp)": cis(g.diff_ci_low, g.diff_ci_high),
                      "Small cell": g.small_cell_flag}),
        "tableS13_who_is_missed", "Table S13. Exploratory subgroup analysis (World Bank Malawi 2021, rounds 7/9/11)",
        "Unadjusted comparisons; hypothesis-generating only. District-cluster bootstrap.")
    hz = pd.read_csv(mc / "horizons.csv")
    hz["complete_households"] = hz.complete_households.astype(int)
    put(hz, "tableS14_multicountry_horizons",
        "Table S14. Protocol-locked multi-country investigation: rounds, horizons and usability",
        "Usability rules fixed in the locked protocol. complete_households = 0 where split-sample designs leave no household "
        "interviewed in every round.")
    return made


def count_columns_are_integers(df: pd.DataFrame, cols: list[str]) -> bool:
    for c in cols:
        if c not in df:
            continue
        v = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(v) and not np.all(np.equal(np.mod(v, 1), 0)):
            return False
        if df[c].astype(str).str.contains(r"^\d+\.0$").any():
            return False
    return True
