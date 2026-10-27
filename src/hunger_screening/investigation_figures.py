"""Investigation figures, drawn only from data/public_aggregates (aggregates, no microdata).

Same visual grammar as generate_figures: dot = point estimate; thin whisker = 95%
cluster-bootstrap interval; hatched bar = identification range (not a confidence
interval). Dataset colours: Aggarwal HHS panel = blue, World Bank HFPS = aqua (circle vs
square markers and direct labels carry identity too); Liberia keeps orange.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .generate_figures import GRID, INK, INK2, MUTED, _note, _pct, _save

AGG, WB, LIB = "#2a78d6", "#1baf7a", "#eb6834"


def _whisker(ax, x, y, lo, hi, color, marker="o", horizontal=False, ms=6):
    y, lo, hi = (np.atleast_1d(np.asarray(v, dtype=float)) for v in (y, lo, hi))
    err = np.vstack([y - lo, hi - y])
    if horizontal:
        ax.errorbar(y, x, xerr=err, fmt=marker, color=color, ms=ms, lw=1.2, capsize=0, mec="white", mew=1)
    else:
        ax.errorbar(x, y, yerr=err, fmt=marker, color=color, ms=ms, lw=1.2, capsize=0, mec="white", mew=1)


def fig_timing_across(pub: Path, out: Path, readme: Path):
    """Figure 4: every evaluated contact window, marked by separability from the best observed window."""
    w = pd.read_csv(pub / "review" / "window_paired_comparisons.csv")
    panels = [
        ("Aggarwal trial, HHS 2+, Jul 2020 - Jun 2021", "Aggarwal", "Jul 2020 - Jun 2021 (six windows)", AGG, "o"),
        ("Aggarwal trial, HHS 2+, Jul 2019 - Jun 2020", "Aggarwal", "Jul 2019 - Jun 2020 (six windows)", AGG, "o"),
        ("World Bank HFPS, FIES item 7, 2021", "World Bank", "2021 rounds 7/8/9/11/12", WB, "s"),
        ("World Bank, item 7, 2023-24 (B)", "World Bank", "Jun 2023 / Dec 2023 / Apr 2024 (group B)", WB, "s"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(11.6, 4.1), sharey=True, gridspec_kw={"width_ratios": [6, 6, 5, 3]})
    for ax, (title, ds, hz, col, mk) in zip(axes, panels):
        g = w[w.dataset.str.startswith(ds) & (w.horizon == hz)].reset_index(drop=True)
        x = np.arange(len(g))
        ax.axhline(g.random_missed.iloc[0], color=MUTED, lw=1.2, ls=(0, (4, 3)))
        for i, r in g.iterrows():
            filled = not r.separable_from_best_at_95
            ax.errorbar([i], [r.missed], yerr=[[r.missed - r.missed_ci_low], [r.missed_ci_high - r.missed]], fmt=mk,
                        color=col, mfc=col if filled else "white", mec=col, ms=7, lw=1.1, capsize=0, mew=1.4)
            if r.is_best_observed:
                ax.annotate("best observed", (i, r.missed_ci_high), xytext=(0, 4), textcoords="offset points",
                            ha="center", va="bottom", fontsize=6.8, color=INK2)
        labels = [lab.split(" ", 1)[1].replace(" 2021", "").replace(" 2023", " 23").replace(" 2024", " 24") if lab.startswith("R") else lab
                  for lab in g.window]
        ax.set_xticks(x, labels, fontsize=7.6)
        ax.set_xlim(-0.6, len(g) - 0.4)
        ax.set_title(title, loc="left", fontsize=8.4)
        ax.text(0.0, -0.19, f"{int(g.n_reference_positive.iloc[0])} reference positives", transform=ax.transAxes, fontsize=7.2, color=INK2)
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("Missed share of reference-positive households\n(single contact in that window)")
    _pct(axes[0])
    from matplotlib.lines import Line2D
    fig.legend([Line2D([], [], color=INK2, marker="o", ls="", mfc=INK2), Line2D([], [], color=INK2, marker="o", ls="", mfc="white"),
                Line2D([], [], color=MUTED, ls=(0, (4, 3)))],
               ["not separable from the best observed window (paired 95% CI includes 0)",
                "worse than the best observed window (paired 95% CI excludes 0)", "one contact at a random observed time"],
               loc="upper left", bbox_to_anchor=(0.01, 0.93), ncol=3, fontsize=7.4)
    fig.suptitle("Missed share by contact window in two Malawi panels", x=0.01, ha="left", fontsize=10.5, fontweight="bold")
    _note(fig, "Whiskers: 95% cluster-bootstrap intervals (villages for the trial; districts for the World Bank survey, an approximation). "
               "Blue circles: HHS 2 or more (trial); green squares: the FIES item 'hungry but did not eat' (World Bank). Different outcomes, "
               "not pooled. 'Best observed' is the lowest point estimate, not a demonstrated optimum. None of these comparisons is blind.", y=-0.05)
    fig.tight_layout(rect=(0, 0, 1, 0.87))
    return _save(fig, out / "investigation", "figI1_timing_across_datasets", readme)


def fig_transfer(pub: Path, out: Path, readme: Path):
    inv = pub / "investigation"
    base = pd.read_csv(pub / "timing_validation.csv")
    base = base[base.cohort == "2021 complete four-slot cohort"]
    jj = pd.read_csv(inv / "aggarwal_july_june_test.csv")
    t = pd.read_csv(inv / "hfps_transfer_tests.csv")
    t = t[(t.item == "s8q7") & t.selected_on_train & t.test_missed.notna()]
    from .build_panels import SLOT_LABELS
    rows = []
    for _, r in base.iterrows():
        rows.append((f"Aggarwal {r.country}: calendar 2020 → 2021", SLOT_LABELS[int(r.slot)], r.missed_frozen - r.missed_random_one_slot,
                     r.diff_ci_low, r.diff_ci_high, AGG if r.country == "Malawi" else LIB, "o"))
    j = jj[jj.selected_on_train].iloc[0]
    rows.append(("Aggarwal Malawi: Jul 2019–Jun 2020 → Jul 2020–Jun 2021", j.candidate, j.diff_vs_random, j.diff_ci_low, j.diff_ci_high, AGG, "o"))
    names = {"HFPS 2020 -> 2021 (reproduction)": "World Bank: 2020 rounds → 2021",
             "HFPS matched Jun/Dec/Apr, 2020-21 -> 2023-24, group B": "World Bank: Jun/Dec/Apr 2020–21 → 2023–24 (B)",
             "HFPS matched (train: group-B households only)": "  same, trained on group-B households only",
             "HFPS matched, training June = round 11 (pandemic-onset round excluded)": "  same, June 2020 round replaced by June 2021",
             "HFPS matched Jun/Feb-Mar, 2020-21 -> 2023-24, group A": "World Bank: Jun/Feb–Mar 2020–21 → 2023–24 (A)"}
    for _, r in t.iterrows():
        rows.append((names[r.test], r.candidate.replace("R1 ", ""), r.diff_vs_random, r.diff_ci_low, r.diff_ci_high, WB, "s"))
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    ax.axvline(0, color=INK2, lw=1)
    for i, (_lab, chosen, d, lo, hi, col, mk) in enumerate(rows):
        y = len(rows) - 1 - i
        _whisker(ax, [y], np.array([d]), np.array([lo]), np.array([hi]), col, mk, horizontal=True)
        ax.text(hi + 0.012, y, f"chose {chosen}", va="center", fontsize=7.6, color=INK2)
    ax.set_yticks(range(len(rows))[::-1], [r[0] for r in rows], fontsize=8)
    ax.set_xlim(-0.55, 0.32)
    _pct(ax, "x")
    ax.set_xlabel("Test-year missed share of the frozen choice minus a random observed contact\n(left of zero = frozen choice misses fewer)")
    fig.suptitle("Choosing the contact month from one earlier year worked when that year was typical,\n"
                 "and failed when the training data began at the pandemic onset", x=0.01, ha="left", fontsize=10.2,
                 fontweight="bold")
    _note(fig, "Each row selects one contact window on training data only, freezes it, and scores it on later data. World Bank "
               "rows: 'hungry but did not eat' item; their 2023–24 ranking was predictable from round-level rates seen during "
               "the audit, so these are not blind tests. The 2020 World Bank training data start at the pandemic onset (late May 2020).", y=-0.04)
    fig.tight_layout()
    return _save(fig, out / "investigation", "figI2_transfer_tests", readme)


def fig_robustness(pub: Path, out: Path, readme: Path):
    """Figure 6: missing-history identification, adversarial tipping points and random-error simulations."""
    inv = pub / "investigation"
    a = pd.read_csv(inv / "aggarwal_timing_robustness.csv")
    h = pd.read_csv(inv / "hfps_decision_robustness.csv")
    comps = [
        ("Trial, Malawi 2021\nJan-Feb vs random of 4", a[a.analysis.str.startswith("Aggarwal Malawi 2021")], AGG, "o"),
        ("Trial, Malawi Jul 2020-Jun 2021\nJan-Feb vs random of 6", a[a.analysis.str.startswith("Aggarwal Malawi Jul")], AGG, "o"),
        ("World Bank 2021, item 7\nJan round vs random of 3", h[h.analysis.str.startswith("2021 rounds 7/9/11") & (h["item"] == "s8q7")], WB, "s"),
        ("World Bank 2021, item 8\nJan round vs random of 3", h[h.analysis.str.startswith("2021 rounds 7/9/11") & (h["item"] == "s8q8")], WB, "s"),
    ]
    sim = pd.read_csv(pub / "review" / "random_error_simulation.csv")
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.4), gridspec_kw={"width_ratios": [5, 4, 4.6]})
    ax = axes[0]
    ax.axvline(0, color=INK2, lw=1)
    for i, (_lab, g, col, mk) in enumerate(comps):
        r = g[g.alpha == 0].iloc[0]
        y = len(comps) - 1 - i
        ax.barh(y, 100 * (r.upper - r.lower), left=100 * r.lower, height=0.5, color="white", edgecolor=col, hatch="////", lw=1.1)
        ax.plot(100 * r.complete_case_diff, y, mk, color=col, mec="white", ms=7)
        ok = r.upper < 0
        ax.text(100 * r.upper + 1, y, "excludes 0" if ok else "reaches 0", va="center", fontsize=7.4, color=INK if ok else LIB)
    ax.set_yticks(range(len(comps))[::-1], [c[0] for c in comps], fontsize=7.6)
    ax.set_xlim(-50, 18)
    ax.set_xlabel("Chosen minus random missed share (percentage points)")
    ax.set_title("A. Missing histories: exact identification range\n(no answer error; 3 of 4 exclude zero)", loc="left", fontsize=8.6)
    ax = axes[1]
    for i, (_lab, g, col, _mk) in enumerate(comps):
        r = g.iloc[0]
        y = len(comps) - 1 - i
        share = 100 * r.tipping_budget_share_of_observed_screens
        ax.barh(y, share, height=0.5, color=col, alpha=0.85)
        txt = (f"{int(r.tipping_budget_to_reach_zero)}/{int(r.observed_screens)} ({share:.1f}%)"
               if r.tipping_budget_to_reach_zero > 0 else "0 (missingness alone\nreaches zero)")
        ax.text(share + 0.05, y, txt, va="center", fontsize=7.2, color=INK2)
    ax.set_yticks(range(len(comps))[::-1], ["", "", "", ""])
    ax.set_xlim(0, 4.6)
    ax.set_xlabel("Smallest share of recorded answers whose\nadversarial flipping can erase the advantage (%)")
    ax.set_title("B. Worst-case (adversarial) answer error\n(tipping point; not an error-rate estimate)", loc="left", fontsize=8.6)
    ax = axes[2]
    ax.axhline(0, color=INK2, lw=1)
    obs = {"Malawi Jul 2020 - Jun 2021": float(comps[1][1][comps[1][1].alpha == 0].complete_case_diff.iloc[0]),
           "Malawi calendar 2021 (four windows)": float(comps[0][1][comps[0][1].alpha == 0].complete_case_diff.iloc[0])}
    for k, (hz, g) in enumerate(sim.groupby("horizon", sort=False)):
        xs = np.array([0.0] + list(100 * g.error_rate_per_answer)) + (k - 0.5) * 1.6
        ys = np.array([100 * obs[hz]] + list(100 * g.mean_diff))
        lo = np.array([100 * obs[hz]] + list(100 * g.p2_5))
        hi = np.array([100 * obs[hz]] + list(100 * g.p97_5))
        ax.errorbar(xs, ys, yerr=[ys - lo, hi - ys], fmt="o-" if k == 0 else "D-", color=AGG if k == 0 else "#0d366b", lw=1.1, ms=5,
                    capsize=0, label=("Trial, Jul 2020-Jun 2021 (6 windows)" if k == 0 else "Trial, Jan-Aug 2021 (4 windows)"))
    ax.set_xticks([0, 5, 10, 20], ["observed", "5%", "10%", "20%"])
    ax.set_xlabel("Hypothetical random flip rate per recorded answer")
    ax.set_ylabel("Jan-Feb minus random (pp)")
    ax.set_ylim(-50, 5)
    ax.legend(fontsize=7.2, loc="lower right")
    ax.set_title("C. Random answer error (simulation, 1,000 runs per\nrate; Jan-Feb stayed below random in at least 999)", loc="left", fontsize=8.6)
    fig.suptitle("Robustness of screening-timing comparisons to missing histories and hypothetical answer error", x=0.01, ha="left",
                 fontsize=10.4, fontweight="bold")
    _note(fig, "A: hatched bars are exact identification ranges over all completions of missing screens (not confidence intervals); dot = "
               "complete-case value. The World Bank item 8 comparison reaches zero. B: answers flipped in the most damaging possible way; a "
               "tipping point is not an estimate of real error. C: answers flipped at random at hypothetical rates; dots = mean, whiskers = "
               "2.5th to 97.5th percentiles of the simulated difference; trial (HHS) analyses only. No claim is made about which error "
               "mechanism operates.", y=-0.04)
    fig.tight_layout(rect=(0, 0, 1, 0.95), w_pad=3.0)
    return _save(fig, out / "investigation", "figI3_decision_robustness", readme)


def fig_subgroups(pub: Path, out: Path, readme: Path):
    g = pd.read_csv(pub / "investigation" / "hfps_subgroups.csv")
    g = g[(g["item"] == "s8q7") & g.n_complete.notna()]
    order = ["all", "Rural", "Urban"] + [f"wealth_quintile={q}" for q in range(1, 6)] + ["North", "Central", "Southern"]
    names = {"all": "All households", **{f"wealth_quintile={q}": f"Wealth quintile {q}" + (" (poorest)" if q == 1 else " (richest)" if q == 5 else "") for q in range(1, 6)}}
    g = g.set_index("group").loc[order]
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    ax.axvline(0, color=INK2, lw=1)
    ax.axvline(g.loc["all", "diff_vs_random"], color=MUTED, lw=1, ls=(0, (4, 3)))
    for i, (_grp, r) in enumerate(g.iterrows()):
        y = len(g) - 1 - i
        _whisker(ax, [y], np.array([r.diff_vs_random]), np.array([r.diff_ci_low]), np.array([r.diff_ci_high]), WB, "s",
                 horizontal=True)
        ax.text(0.05, y, f"{int(r.n_reference_positive)} ref.+ / {int(r.n_complete)}", va="center", fontsize=7.4, color=INK2)
    ax.set_yticks(range(len(g))[::-1], [names.get(x, x) for x in g.index], fontsize=8.2)
    ax.set_xlim(-0.3, 0.14)
    _pct(ax, "x")
    ax.set_xlabel("January 2021 contact minus random contact: missed share (left = January misses fewer)")
    fig.suptitle("Exploratory: the lean-season advantage is concentrated in poorer and rural households", x=0.01,
                 ha="left", fontsize=10.2, fontweight="bold")
    _note(fig, "World Bank HFPS, 'hungry but did not eat', households complete in rounds 7/9/11 (Jan, Apr, late May–Jun 2021). "
               "District-cluster bootstrap 95% intervals, unweighted, no multiplicity adjustment; 2019 wealth quintiles are national "
               "IHPS quintiles. Hypothesis-generating only.", y=-0.03)
    fig.tight_layout()
    return _save(fig, out / "investigation", "figI4_who_is_missed", readme)


def fig_yield(pub: Path, out: Path, readme: Path):
    inv = pub / "investigation"
    a = pd.read_csv(inv / "aggarwal_fixed_schedules.csv")
    a = a[a.cohort.str.startswith("Aggarwal Malawi")].set_index("schedule")
    h = pd.read_csv(inv / "hfps_fixed_schedules.csv")
    h = h[(h.cohort == "2021 rounds 7/9/11") & (h["item"] == "s8q7")].set_index("schedule")
    groups = [
        ("Aggarwal Malawi 2020\n(HHS ≥ 2, six windows)", AGG, "o",
         [("Random 1", a.loc["random 1 of 6"]), ("Jan–Feb", a.loc["Jan-Feb"]), ("Random 2", a.loc["random 2 of 6"]),
          ("Jan–Feb +\nMar–Apr", a.loc["Jan-Feb + Mar-Apr"])]),
        ("World Bank 2021\n('hungry', Jan/Apr/late May–Jun)", WB, "s",
         [("Random 1", h.loc["random 1 of 3"]), ("Jan", h.loc["R7 Jan 2021"]), ("Random 2", h.loc["random 2 of 3"]),
          ("Jan + Apr", h.loc["R7 Jan 2021 + R9 Apr 2021"])]),
    ]
    mv = pd.read_csv(inv / "hfps_model_vs_rule.csv")
    mv = mv[(mv["item"] == "s8q7") & (mv.budget_definition == "budget = half of them")]
    fig, axes = plt.subplots(1, 3, figsize=(10.6, 3.8), gridspec_kw={"width_ratios": [4, 4, 4.4]})
    for ax, (title, col, _mk, items) in zip(axes[:2], groups):
        x = np.arange(len(items))
        vals = [r.identified_per_100_households for _, r in items]
        ax.bar(x, vals, width=0.6, color=[GRID if lab.startswith("Random") else col for lab, _ in items], edgecolor="white")
        for xi, v in zip(x, vals):
            ax.text(xi, v + 1.5, f"{v:.0f}", ha="center", fontsize=8, color=INK)
        ax.set_xticks(x, [lab for lab, _ in items], fontsize=7.8)
        ax.set_ylim(0, 100)
        ax.set_title(title, loc="left", fontsize=8.8)
        ax.set_ylabel("Households identified per 100 enrolled")
    pick = {"random": "Random", "warning": "Any milder\n'yes'", "graded": "Count of\nmilder 'yes'", "logistic": "Logistic\nmodel"}
    rules = [(lab, float(mv[mv.rule.str.startswith(k)].captured_per_100_recontacted.iloc[0])) for k, lab in pick.items()]
    budget = int(mv.recontact_budget.iloc[0])
    x = np.arange(len(rules))
    axes[2].bar(x, [v for _, v in rules], width=0.6, color=[GRID, WB, WB, WB], edgecolor="white")
    for xi, (_, v) in zip(x, rules):
        axes[2].text(xi, v + 1.2, f"{v:.0f}", ha="center", fontsize=8, color=INK)
    axes[2].set_xticks(x, [r for r, _ in rules], fontsize=7.6)
    axes[2].set_ylim(0, 70)
    axes[2].set_title(f"Which January negatives to re-contact?\nLater positives per 100 re-contacted ({budget} re-contacted)",
                      loc="left", fontsize=8.8)
    fig.suptitle("A well-timed first contact does most of the work; a second contact adds less, and a simple rule targets it well",
                 x=0.01, ha="left", fontsize=10.2, fontweight="bold")
    _note(fig, "Retrospective, in-sample comparisons among complete households: identification is relative to the observed "
               "contacts, and no schedule is claimed optimal. Right panel: World Bank 2021, 'hungry but did not eat' negatives at "
               "the January round; the logistic model was trained on 2020 rounds only and matches the simple count rule.", y=-0.04)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return _save(fig, out / "investigation", "figI5_contact_yield", readme)


def fig_multicountry(pub: Path, out: Path, readme: Path):
    """Figure 5: protocol-locked multi-country tests; primary H1, primary H3, then sensitivity horizons."""
    mc = pub / "multicountry"
    h1 = pd.read_csv(mc / "h1_calendar_rule.csv")
    h3 = pd.read_csv(mc / "h3_second_contact.csv").dropna(subset=["difference"])
    names = {"BFA": "Burkina Faso", "UGA": "Uganda"}

    def lab(r):
        return f"{names[r.country]} {int(r.horizon_start_year)}-{str(int(r.horizon_start_year) + 1)[2:]}"

    fig = plt.figure(figsize=(12.6, 5.6))
    gs = fig.add_gridspec(2, 3, height_ratios=[2, 3], width_ratios=[1, 1, 1.15], hspace=1.2, wspace=1.05)
    axA, axB = fig.add_subplot(gs[:, 0]), fig.add_subplot(gs[:, 1])
    axC1, axC2 = fig.add_subplot(gs[0, 2]), fig.add_subplot(gs[1, 2])

    def forest(ax, df, x, lo, hi, scale, col, mk, xlabel, title, labeler=lab):
        ax.axvline(0, color=INK2, lw=1)
        for i, (_, r) in enumerate(df.iterrows()):
            y = len(df) - 1 - i
            _whisker(ax, [y], np.array([scale * r[x]]), np.array([scale * r[lo]]), np.array([scale * r[hi]]), col, mk, horizontal=True)
            ax.annotate(f"{scale * r[x]:+.1f} ({scale * r[lo]:+.1f} to {scale * r[hi]:+.1f})", (scale * r[x], y), xytext=(0, 7),
                        textcoords="offset points", ha="center", fontsize=6.8, color=INK2)
        ax.set_yticks(range(len(df))[::-1], [labeler(r) for _, r in df.iterrows()], fontsize=7.6)
        ax.set_ylim(-0.6, len(df) - 0.1)
        ax.set_xlabel(xlabel, fontsize=7.8)
        ax.set_title(title, loc="left", fontsize=8.6)

    p1 = h1[h1.analysis.str.startswith("primary")]
    p3 = h3[h3.analysis.str.startswith("primary")]
    s1 = h1[~h1.analysis.str.startswith("primary")]
    s3 = h3[~h3.analysis.str.startswith("primary")]
    forest(axA, p1, "diff", "diff_ci_low", "diff_ci_high", 100, LIB, "o",
           "Calendar-rule minus random missed share\n(percentage points; left = rule better)", "A. H1 calendar rule, primary\n(2 eligible horizons)")
    axA.set_xlim(-12, 22)
    forest(axB, p3, "difference", "ci_low", "ci_high", 1, LIB, "o",
           "Warning-sign minus random: later positives per\n100 re-contacted households (right = rule better)",
           "B. H3 second-contact rule, primary\n(3 eligible horizons)")
    axB.set_xlim(-4, 12)
    forest(axC1, s1, "diff", "diff_ci_low", "diff_ci_high", 100, MUTED, "D", "percentage points",
           "C. Sensitivity only (deviation D2, split-\nsample group panels): H1",
           labeler=lambda r: f"{lab(r)}, rule {r.rule_round.split(' ')[0]}")
    axC1.set_xlim(-45, 25)
    forest(axC2, s3, "difference", "ci_low", "ci_high", 1, MUTED, "D", "per 100 re-contacted households", "H3 (sensitivity only)",
           labeler=lambda r: f"{lab(r)}, {int(r.recontact_budget)} re-contacted")
    axC2.set_xlim(-5, 10)
    fig.suptitle("Protocol-locked multi-country screening tests", x=0.01, ha="left", fontsize=10.5, fontweight="bold")
    _note(fig, "Five countries assessed (Burkina Faso, Ethiopia, Nigeria, Tanzania, Uganda); two had eligible primary H1 horizons. Ethiopia was "
               "excluded from H1 by protocol (no single national lean season); Nigeria and Tanzania had no usable horizon. Protocol locked before "
               "access to household- and item-level outcomes, with prior exposure to some published aggregate charts. Under its prespecified rule "
               "H1 was contradicted (Uganda individually inconclusive); H3 was supported directionally (Uganda 2022-23 interval includes zero). "
               "Whiskers: 95% cluster-bootstrap intervals. Item: 'hungry but did not eat' (FIES item 7).", y=0.0)
    fig.subplots_adjust(left=0.12, right=0.98, top=0.84, bottom=0.22)
    return _save(fig, out / "investigation", "figI6_multicountry_locked_test", readme)


def render_investigation(pub: Path, figures: Path) -> list[Path]:
    readme = figures / "README"
    paths = []
    for f in (fig_timing_across, fig_transfer, fig_robustness, fig_subgroups, fig_yield):
        paths += f(pub, figures, readme)
    if (pub / "multicountry" / "h1_calendar_rule.csv").exists():
        paths += fig_multicountry(pub, figures, readme)
    return paths
