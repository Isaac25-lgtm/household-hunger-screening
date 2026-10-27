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
    inv = pub / "investigation"
    jj = pd.read_csv(inv / "aggarwal_july_june_test.csv")
    s = pd.read_csv(inv / "hfps_single_round.csv")
    s = s[(s.cohort == "2021 rounds 7/8/9/11/12") & (s.item == "s8q7")]
    t = pd.read_csv(inv / "hfps_transfer_tests.csv")
    t = t[(t.test.str.startswith("HFPS matched Jun/Dec/Apr")) & (t.item == "s8q7")]
    panels = [
        ("Aggarwal Malawi · HHS ≥ 2\nJul 2020–Jun 2021, two-month windows", AGG, "o",
         list(jj.candidate), jj.test_missed.to_numpy(), jj.test_missed_ci_low.to_numpy(), jj.test_missed_ci_high.to_numpy(),
         jj.test_random_missed.iloc[0], int(jj.n_test_reference_positive.iloc[0])),
        ("World Bank HFPS · 'hungry, did not eat'\n2021 monthly rounds", WB, "s",
         [x.split(" ", 1)[1].replace(" 2021", "") for x in s[~s.schedule.str.startswith("random")].schedule],
         *[s[~s.schedule.str.startswith("random")][c].to_numpy() for c in ("missed_share", "missed_ci_district_low", "missed_ci_district_high")],
         float(s[s.schedule.str.startswith("random")].missed_share.iloc[0]), int(s.n_reference_positive.iloc[0])),
        ("World Bank HFPS · same item\n2023–24, group B", WB, "s",
         ["Jun 2023", "Dec 2023", "Apr 2024"], t.test_missed.to_numpy(), t.test_missed_ci_low.to_numpy(),
         t.test_missed_ci_high.to_numpy(), float(t.test_random_missed.iloc[0]), int(t.n_test_reference_positive.iloc[0])),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.9), sharey=True, gridspec_kw={"width_ratios": [6, 5, 3]})
    for ax, (title, col, mk, labels, y, lo, hi, rnd, npos) in zip(axes, panels):
        x = np.arange(len(labels))
        ax.axhline(rnd, color=MUTED, lw=1.2, ls=(0, (4, 3)))
        _whisker(ax, x, y, lo, hi, col, mk)
        ax.set_xticks(x, labels, rotation=0, fontsize=8)
        ax.set_title(title, loc="left", fontsize=9)
        ax.text(0.0, -0.2, f"{npos} reference-positive households", transform=ax.transAxes, fontsize=7.4, color=INK2)
        ax.set_xlim(-0.6, len(labels) - 0.4)
    axes[0].set_ylabel("Missed: share of households positive at ≥1\nobserved contact that this one contact misses")
    axes[0].set_ylim(0, 1)
    _pct(axes[0])
    from matplotlib.lines import Line2D
    fig.legend([Line2D([], [], color=AGG, marker="o", ls=""), Line2D([], [], color=WB, marker="s", ls=""),
                Line2D([], [], color=MUTED, ls=(0, (4, 3)), lw=1.2)],
               ["Aggarwal et al. HHS panel (rural trial controls)", "World Bank HFPS (national phone panel)",
                "one contact at a random observed time (benchmark)"],
               loc="upper left", bbox_to_anchor=(0.01, 0.94), ncol=3, fontsize=7.8)
    fig.suptitle("A single lean-season contact misses fewer households than a random or post-harvest contact, in two Malawi panels",
                 x=0.01, ha="left", fontsize=10.5, fontweight="bold")
    _note(fig, "Dots: missed share in households observed at every contact of the horizon; whiskers: 95% cluster-bootstrap "
               "intervals (villages for Aggarwal; districts for the World Bank panel, a coarse approximation). The two "
               "datasets use different questions (HHS ≥ 2 vs one FIES item, both 30-day recall) and are not pooled.", y=-0.06)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
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
    inv = pub / "investigation"
    a = pd.read_csv(inv / "aggarwal_timing_robustness.csv")
    h = pd.read_csv(inv / "hfps_decision_robustness.csv")
    series = [
        ("Aggarwal Malawi 2021\nJan–Feb vs random of 4", a[a.analysis.str.startswith("Aggarwal Malawi 2021")], AGG),
        ("Aggarwal Malawi Jul 2020–Jun 2021\nJan–Feb vs random of 6", a[a.analysis.str.startswith("Aggarwal Malawi Jul")], AGG),
        ("World Bank 2021, 'hungry'\nJan round vs random of 3",
         h[(h.analysis.str.startswith("2021 rounds 7/9/11")) & (h.item == "s8q7")], WB),
        ("World Bank 2021, 'whole day'\nJan round vs random of 3",
         h[(h.analysis.str.startswith("2021 rounds 7/9/11")) & (h.item == "s8q8")], WB),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(10.6, 3.8), sharey=True)
    for ax, (title, g, col) in zip(axes, series):
        g = g.sort_values("alpha")
        x = np.arange(len(g))
        ax.axhline(0, color=INK2, lw=1)
        ax.bar(x, g.upper - g.lower, bottom=g.lower, width=0.55, color="white", edgecolor=col, hatch="////", lw=1.1)
        ax.plot(x, g.complete_case_diff, "o" if col == AGG else "s", color=col, ms=5, mec="white")
        ax.set_xticks(x, [f"{a:.0%}" for a in g.alpha])
        tip = g.tipping_budget_to_reach_zero.iloc[0]
        share = g.tipping_budget_share_of_observed_screens.iloc[0]
        ax.set_title(title, loc="left", fontsize=8.2)
        ax.text(0.02, 0.97, f"{int(tip)} flips ({share:.1%} of\n{int(g.observed_screens.iloc[0])} answers) can\nerase the advantage"
                if tip > 0 else "reaches zero with\nmissing screens alone", transform=ax.transAxes, fontsize=7.2, color=INK2,
                va="top")
        ax.set_xlabel("Hypothetical share of recorded\nanswers allowed to be wrong")
    axes[0].set_ylabel("Missed share: chosen contact minus random\n(range over all allowed worlds)")
    _pct(axes[0])
    axes[0].set_ylim(-0.8, 0.8)
    fig.suptitle("Timing advantages survive any pattern of missing interviews but not small amounts of worst-case answer error",
                 x=0.01, ha="left", fontsize=10.2, fontweight="bold")
    _note(fig, "Hatched bars: exact identification ranges (not confidence intervals) over every completion of missing screens, plus "
               "a shared budget of flipped recorded answers chosen adversarially; dot = complete-case value. Solver validated by brute force.", y=-0.04)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
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


def render_investigation(pub: Path, figures: Path) -> list[Path]:
    readme = figures / "README"
    paths = []
    for f in (fig_timing_across, fig_transfer, fig_robustness, fig_subgroups, fig_yield):
        paths += f(pub, figures, readme)
    return paths
