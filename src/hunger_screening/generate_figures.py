"""Publication figures, drawn only from data/public_aggregates/*.csv.

Visual grammar used throughout (kept identical in every figure so the three kinds of
uncertainty are never confused):
  * dot             = point estimate on complete histories
  * thin whisker    = 95% village-cluster bootstrap interval (sampling variability)
  * hatched bar     = identification range (no-assumption bounds; NOT a confidence interval)
Colours: Malawi = blue, Liberia = orange (validated CVD-safe pair); neutral grey for benchmarks.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Patch  # noqa: E402

from .build_panels import SLOT_LABELS  # noqa: E402

COL = {"Malawi": "#2a78d6", "Liberia": "#eb6834"}
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#ffffff"
COUNTRIES = ["Malawi", "Liberia"]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9.5, "axes.titlesize": 10.5, "axes.titleweight": "bold",
    "axes.labelsize": 9.5, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "legend.frameon": False, "svg.fonttype": "none",
    "hatch.linewidth": 0.8,
})


def _save(fig, outdir: Path, name: str, readme_dir: Path | None = None) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext, kw in (("png", {"dpi": 300}), ("svg", {}), ("pdf", {})):
        p = outdir / f"{name}.{ext}"
        fig.savefig(p, bbox_inches="tight", **kw)
        paths.append(p)
    if readme_dir is not None:
        readme_dir.mkdir(parents=True, exist_ok=True)
        p = readme_dir / f"{name}.png"
        fig.savefig(p, dpi=130, bbox_inches="tight")
        paths.append(p)
    plt.close(fig)
    return paths


def _pct(ax, axis="y"):
    fmt = matplotlib.ticker.PercentFormatter(1.0, decimals=0)
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def _note(fig, text, y=-0.02):
    fig.text(0.01, y, text, ha="left", va="top", fontsize=7.6, color=INK2, wrap=True)


# ---------------------------------------------------------------- Fig 1: flow
def fig_cohort_flow(pub: Path, out: Path, readme: Path):
    flow = pd.read_csv(pub / "cohort_flow.csv")
    steps = [
        ("Baseline phone-frame households", "Baseline phone frame\n(control households)"),
        ("Households with >=1 phone record", "≥1 phone interview\n(any month, 2019–2021)"),
        ("Households with >=1 valid 2020 screen", "≥1 valid 2020 screen"),
        ("Households with all 6 valid 2020 screens", "All six 2020 windows\nobserved (complete)"),
        ("Complete households reference-positive (HHS>=2 in >=1 slot)", "Reference-positive\n(HHS ≥ 2 in ≥ 1 window)"),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.set_axis_off()
    ax.set_xlim(0, 10)
    ax.set_ylim(0.5, len(steps) + 0.75)
    for i, (key, label) in enumerate(steps):
        y = len(steps) - i
        ax.add_patch(FancyBboxPatch((3.05, y - 0.36), 3.9, 0.72, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc="#f4f3f0", ec=GRID, lw=1))
        ax.text(5.0, y, label, ha="center", va="center", fontsize=8.8, color=INK)
        for c, x in (("Malawi", 1.5), ("Liberia", 8.5)):
            v = int(flow[(flow.country == c) & (flow.step == key)]["count"].iloc[0])
            top = int(flow[(flow.country == c) & (flow.step == steps[0][0])]["count"].iloc[0])
            ax.add_patch(FancyBboxPatch((x - 1.1, y - 0.36), 2.2, 0.72,
                                        boxstyle="round,pad=0.02,rounding_size=0.12", fc=SURF, ec=COL[c], lw=1.6))
            sub = f"{v / top:.0%} of frame" if i > 0 else "households"
            ax.text(x, y + 0.1, f"{v}", ha="center", va="center", fontsize=11, fontweight="bold", color=INK)
            ax.text(x, y - 0.19, sub, ha="center", va="center", fontsize=7.4, color=INK2)
        if i < len(steps) - 1:
            for x in (1.5, 8.5):
                ax.annotate("", xy=(x, y - 0.62), xytext=(x, y - 0.38),
                            arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1))
    for c, x in (("Malawi", 1.5), ("Liberia", 8.5)):
        ax.text(x + 0.12, len(steps) + 0.55, c, ha="center", va="center", fontsize=10.5, fontweight="bold",
                color=INK)
        ax.plot([x - 0.72, x - 0.55], [len(steps) + 0.55] * 2, color=COL[c], lw=5, solid_capstyle="round")
    vm = flow[(flow.country == "Malawi") & (flow.step.str.startswith("Villages with"))]["count"].item()
    vl = flow[(flow.country == "Liberia") & (flow.step.str.startswith("Villages with"))]["count"].item()
    _note(fig, f"Complete-history villages: Malawi {vm}, Liberia {vl}. Windows are two-month designated slots "
               "(Jan–Feb … Nov–Dec 2020); each screen recalls ~30 days. Source: Aggarwal et al. (2022) S1 Data, "
               "control households only. Counts are aggregates.", y=0.04)
    return _save(fig, out, "fig1_cohort_flow", readme)


# ---------------------------------------------------------------- Fig 2: frontier
def fig_frontier(pub: Path, out: Path, readme: Path):
    f = pd.read_csv(pub / "frontier.csv")
    f = f[f.threshold == 2]
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for c, dx in (("Malawi", -0.06), ("Liberia", 0.06)):
        g = f[f.country == c].sort_values("m")
        x = g.m + dx
        ax.fill_between(g.m, g.ci_low, g.ci_high, color=COL[c], alpha=0.10, lw=0)
        ax.plot(g.m, g.missed_fraction, color=COL[c], lw=2, solid_capstyle="round")
        ax.errorbar(x, g.missed_fraction, yerr=[g.missed_fraction - g.ci_low, g.ci_high - g.missed_fraction],
                    fmt="none", ecolor=COL[c], elinewidth=1.1, capsize=2.5)
        ax.scatter(g.m, g.missed_fraction, s=34, color=COL[c], edgecolor=SURF, linewidth=1.5, zorder=3,
                   label=f"{c} (n = {g.n_complete.iloc[0]} complete; {g.n_reference_positive.iloc[0]} reference-positive)")
        for m in (1, 2, 3):
            v = g[g.m == m].missed_fraction.item()
            ax.annotate(f"{v:.1%}", (m, v), xytext=(9, 3) if c == "Liberia" else (-12, -14),
                        textcoords="offset points", fontsize=8, color=INK2,
                        ha="left" if c == "Liberia" else "right")
    ax.set_xticks(range(1, 7))
    ax.set_xticklabels([f"{m}" for m in range(1, 7)])
    ax.set_xlabel("Screens retained out of six 2020 windows (chosen uniformly at random)")
    ax.set_ylabel("Reference-positive households missed")
    ax.set_ylim(0, 0.82)
    _pct(ax)
    ax.set_title("Fewer screens, more households missed", loc="left")
    ax.legend(loc="upper right", fontsize=8)
    _note(fig, "Exact expected share of reference-positive households (HHS ≥ 2 in ≥ 1 of six observed 30-day recall "
               "windows) with no positive retained screen. Lines/dots: exact values; whiskers and bands: 95% village-"
               "cluster percentile bootstrap (2,000 draws), conditional on complete histories. Not a prevalence, not "
               "annual incidence, not a causal effect of interviewing less often.")
    return _save(fig, out, "fig2_frontier", readme)


# ---------------------------------------------------------------- Fig 3: intermittency
def fig_k_distribution(pub: Path, out: Path, readme: Path):
    kd = pd.read_csv(pub / "k_distribution.csv")
    kd = kd[kd.threshold == 2]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2), sharey=False)
    for ax, c in zip(axes, COUNTRIES):
        g = kd[kd.country == c]
        tot = g.households.sum()
        pos = g[g.k_positive_windows > 0].households.sum()
        colors = [MUTED if k == 0 else COL[c] for k in g.k_positive_windows]
        ax.bar(g.k_positive_windows, g.households / tot, width=0.62, color=colors, edgecolor=SURF, linewidth=2)
        for k, h in zip(g.k_positive_windows, g.households):
            ax.text(k, h / tot + 0.008, f"{h}", ha="center", va="bottom", fontsize=7.6, color=INK2)
        ax.set_xticks(range(7))
        ax.set_ylim(0, (g.households / tot).max() * 1.18)
        ax.set_xlabel("Windows with HHS ≥ 2 (of 6)")
        ax.set_title(f"{c}: {pos} of {tot} reference-positive", loc="left", fontsize=9.5)
        _pct(ax)
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Share of complete households")
    _note(fig, "Complete 2020 histories. Bar labels are household counts. Grey bar: never positive (excluded from "
               "the ascertainment denominator). Most reference-positive households are positive in only one to three "
               "of six windows, which is why sparse screening misses them.", y=-0.06)
    fig.subplots_adjust(wspace=0.3)
    return _save(fig, out, "fig3_intermittency", readme)


# ---------------------------------------------------------------- Fig 4: missing bounds
def fig_missing_bounds(pub: Path, out: Path, readme: Path):
    mb = pd.read_csv(pub / "missing_bounds.csv")
    fr = pd.read_csv(pub / "frontier.csv")
    fr = fr[fr.threshold == 2]
    fig, ax = plt.subplots(figsize=(6.8, 3.9))
    ylabels, yticks = [], []
    y = 0
    for m in (1, 2, 3):
        for c in COUNTRIES:
            b = mb[(mb.country == c) & (mb.m == m)].iloc[0]
            p = fr[(fr.country == c) & (fr.m == m)].iloc[0]
            ax.barh(y, b.upper - b.lower, left=b.lower, height=0.5, color=COL[c], alpha=0.18,
                    hatch="///", edgecolor=COL[c], linewidth=0)
            ax.plot([p.ci_low, p.ci_high], [y, y], color=INK, lw=1.1)
            ax.scatter([p.missed_fraction], [y], s=34, color=COL[c], edgecolor=SURF, linewidth=1.5, zorder=3)
            ax.text(b.upper + 0.012, y, f"{b.lower:.1%}–{b.upper:.1%}", va="center", fontsize=7.8, color=INK2)
            ylabels.append(f"{c}, {m} screen{'s' if m > 1 else ''}")
            yticks.append(y)
            y += 1
        y += 0.6
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.0)
    _pct(ax, "x")
    ax.set_xlabel("Reference-positive households missed")
    ax.set_title("Missing screens: what the frame data can and cannot pin down", loc="left")
    handles = [Patch(facecolor="#d9d8d4", hatch="///", edgecolor=MUTED,
                     label="Identification bounds — NOT confidence intervals"),
               plt.Line2D([], [], color=INK, lw=1.1, marker="o", markerfacecolor=MUTED, markeredgecolor=SURF,
                          label="Complete-history estimate with 95% village bootstrap")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.45, -0.16), ncol=2, fontsize=7.6)
    nm = mb[mb.country == "Malawi"].iloc[0]
    nl = mb[mb.country == "Liberia"].iloc[0]
    _note(fig, y=-0.09, text=f"Sharp no-assumption bounds over the whole baseline phone frame (Malawi {nm.frame_households}, "
               f"{nm.households_any_missing} with ≥1 missing 2020 window; Liberia {nl.frame_households}, "
               f"{nl.households_any_missing} with ≥1 missing). Each missing window may be positive or negative; "
               "the reference-positive denominator changes with the completion. Exact rational optimisation.")
    return _save(fig, out, "fig4_missing_bounds", readme)


# ---------------------------------------------------------------- Fig 5: label error
def fig_label_error(pub: Path, out: Path, readme: Path):
    le = pd.read_csv(pub / "label_error_bounds.csv")
    le = le[(le.scope == "frame_missing_arbitrary")]
    fig, axes = plt.subplots(1, 3, figsize=(8.2, 3.4), sharey=True)
    alphas = sorted(le.alpha.unique())
    for ax, m in zip(axes, (1, 2, 3)):
        for c, dx in (("Malawi", -0.17), ("Liberia", 0.17)):
            g = le[(le.country == c) & (le.m == m)].sort_values("alpha")
            xs = np.arange(len(alphas)) + dx
            ax.bar(xs, g.upper - g.lower, bottom=g.lower, width=0.3, color=COL[c], alpha=0.22, hatch="///",
                   edgecolor=COL[c], linewidth=0, label=c)
        ax.set_xticks(range(len(alphas)))
        ax.set_xticklabels([f"{a:.0%}" for a in alphas])
        ax.set_title(f"{m} screen{'s' if m > 1 else ''} retained", loc="left", fontsize=9.5)
        ax.set_xlabel("Hypothetical flip budget")
        ax.grid(axis="x", visible=False)
        _pct(ax)
    axes[0].set_ylabel("Reference-positive households missed")
    axes[0].set_ylim(0, 1)
    axes[2].legend(loc="upper right", fontsize=8)
    _note(fig, "Identification ranges (not confidence intervals) when missing windows are unrestricted AND up to the "
               "stated share of observed binary screens in each country may be misclassified (one shared budget per "
               "country). Budgets are hypothetical sensitivity settings, not measured error rates. 0% equals Fig. 4. "
               "Exact Dinkelbach + dynamic-programming optimisation; optimality certified (F(λ*) = 0).", y=-0.05)
    return _save(fig, out, "fig5_label_error", readme)


# ---------------------------------------------------------------- Fig 6: timing
def fig_timing(pub: Path, out: Path, readme: Path):
    ct = pd.read_csv(pub / "timing_candidates.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.6), sharey=True)
    for ax, c in zip(axes, COUNTRIES):
        g20 = ct[(ct.country == c) & (ct.year == 2020)].sort_values("slot")
        g21 = ct[(ct.country == c) & (ct.year == 2021)].sort_values("slot")
        x = np.arange(4)
        ax.bar(x - 0.17, g20.missed_fraction, width=0.3, color=COL[c], edgecolor=SURF, linewidth=2,
               label="2020 (selection year)")
        ax.bar(x + 0.17, g21.missed_fraction, width=0.3, color=COL[c], alpha=0.35, edgecolor=SURF, linewidth=2,
               hatch="....", label="2021 (frozen evaluation)")
        r20, r21 = g20.random_one_slot.iloc[0], g21.random_one_slot.iloc[0]
        ax.axhline(r20, color=INK2, lw=1, label="Random single window, 2020")
        ax.axhline(r21, color=MUTED, lw=1, ls=(0, (1, 2)), label="Random single window, 2021")
        sel = int(g20[g20.selected].slot.iloc[0]) - 1
        ax.annotate("selected\non 2020", (sel - 0.17, g20.missed_fraction.iloc[sel]), xytext=(0, 14),
                    textcoords="offset points", ha="center", fontsize=7.4, color=INK,
                    arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
        ax.set_xticks(x)
        ax.set_xticklabels([SLOT_LABELS[s] for s in g20.slot])
        ax.set_title(f"{c}: n+ = {g20.n_reference_positive.iloc[0]} (2020), {g21.n_reference_positive.iloc[0]} (2021)",
                     loc="left", fontsize=9.5)
        ax.grid(axis="x", visible=False)
        _pct(ax)
    axes[0].set_ylabel("Reference-positive households missed\nby a single fixed window")
    axes[0].set_ylim(0, 1.05)
    h, lab = axes[1].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=4, fontsize=7.4, bbox_to_anchor=(0.5, -0.04))
    fig.subplots_adjust(bottom=0.2)
    _note(fig, "Four windows observed in both years (Jan–Aug). Reference: HHS ≥ 2 in ≥ 1 of the four windows among "
               "households complete in that year (cohorts differ between years). The slot is chosen on 2020 only "
               "(ties → earlier slot) and frozen; 2021 bars for non-selected slots are post hoc disclosure, not "
               "re-selection. Two adjacent pandemic-era years cannot establish stable seasonal optimality.", y=-0.07)
    return _save(fig, out, "fig6_timing", readme)


# ---------------------------------------------------------------- Fig 7: matched timing
def fig_timing_matched(pub: Path, out: Path, readme: Path):
    tv = pd.read_csv(pub / "timing_validation.csv")
    tv = tv[tv.cohort != "Matched: 2020 performance of frozen slot"]
    fig, ax = plt.subplots(figsize=(6.8, 3.4))
    rows = []
    for c in COUNTRIES:
        for coh in ("2021 complete four-slot cohort", "Matched: complete in both years"):
            rows.append(tv[(tv.country == c) & (tv.cohort == coh)].iloc[0])
    for i, r in enumerate(rows):
        c = r.country
        ax.plot([r.frozen_ci_low, r.frozen_ci_high], [i - 0.12] * 2, color=COL[c], lw=1.2)
        ax.scatter([r.missed_frozen], [i - 0.12], s=40, color=COL[c], edgecolor=SURF, linewidth=1.5, zorder=3)
        ax.plot([r.random_ci_low, r.random_ci_high], [i + 0.12] * 2, color=MUTED, lw=1.2)
        ax.scatter([r.missed_random_one_slot], [i + 0.12], s=40, marker="D", color=MUTED, edgecolor=SURF,
                   linewidth=1.5, zorder=3)
        warn = "  ⚠ small n" if r.n_reference_positive < 30 else ""
        ax.text(1.01, i, f"n+ = {int(r.n_reference_positive)} of {int(r.n_complete)}{warn}", va="center",
                fontsize=7.8, color=INK2, transform=ax.get_yaxis_transform())
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{r.country}: {'2021 cohort' if r.cohort.startswith('2021') else 'matched both years'}"
                        for r in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    _pct(ax, "x")
    ax.set_xlabel("Reference-positive households missed in 2021")
    ax.set_title("Frozen 2020 window vs random window, evaluated in 2021", loc="left")
    handles = [plt.Line2D([], [], color=INK2, marker="o", lw=1.2, label="Frozen 2020-selected window (95% village bootstrap)"),
               plt.Line2D([], [], color=MUTED, marker="D", lw=1.2, label="Random single window (95% village bootstrap)")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.45, -0.2), ncol=2, fontsize=7.6)
    _note(fig, y=-0.17, text="Matched = households complete in the four Jan–Aug windows in both 2020 and 2021. Liberia matched "
               "estimates rest on very few reference-positive households and are not informative about timing.")
    return _save(fig, out, "fig7_timing_matched", readme)


# ---------------------------------------------------------------- Fig 8: observation heatmap
def fig_observation(pub: Path, out: Path, readme: Path):
    ob = pd.read_csv(pub / "observation_pattern.csv")
    ob = ob[~((ob.year == 2021) & (ob.observed == 0))]
    fig, axes = plt.subplots(2, 1, figsize=(7.0, 3.3))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "blue", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
    for ax, c in zip(axes, COUNTRIES):
        g = ob[ob.country == c]
        cols = [(y, s) for y in (2020, 2021) for s in range(1, 7) if ((g.year == y) & (g.slot == s)).any()]
        vals = np.array([[g[(g.year == y) & (g.slot == s)].observed_share.item() for y, s in cols]])
        ax.imshow(vals, cmap=cmap, vmin=0.3, vmax=1.0, aspect="auto")
        for j, v in enumerate(vals[0]):
            ax.text(j, 0, f"{v:.0%}", ha="center", va="center", fontsize=7.6, color="white" if v > 0.7 else INK)
        ax.set_xticks(range(len(cols)))
        ax.set_xticklabels([f"{SLOT_LABELS[s]}\n{y}" for y, s in cols], fontsize=6.8)
        ax.set_yticks([0])
        ax.set_yticklabels([f"{c}\n(n = {g.frame_households.iloc[0]})"])
        ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
    axes[0].set_title("Share of baseline phone-frame households with a valid screen, by window", loc="left")
    fig.tight_layout()
    _note(fig, "Aggregate observation rates. Malawi's phone survey ended in Aug 2021; Liberia's in Oct 2021. "
               "Liberia's lower and declining follow-up drives its wide identification bounds.", y=0.0)
    return _save(fig, out, "fig8_observation_pattern", readme)


# ---------------------------------------------------------------- Fig 9: methods schematic
def fig_methods(out: Path, readme: Path):
    fig, ax = plt.subplots(figsize=(8.2, 3.5))
    ax.set_axis_off()
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4.4)
    boxes = [
        (0.2, "Complete histories", "Exact hypergeometric\nmiss probability\nC(6−K, m) / C(6, m)",
         "Point estimate +\nvillage bootstrap CI"),
        (3.15, "Missing windows", "Sharp bounds over\nall completions\n(exact prefix search)",
         "Identification range\n(no assumptions)"),
        (6.1, "Label error", "Shared flip budget\nDinkelbach + exact\nknapsack DP",
         "Wider range per\nhypothetical budget"),
        (9.05, "Calendar timing", "Select window on 2020,\nfreeze, evaluate 2021\n(+ matched cohort)",
         "Out-of-year check\n(not causal)"),
    ]
    for x, head, mid, foot in boxes:
        ax.add_patch(FancyBboxPatch((x, 0.35), 2.75, 3.7, boxstyle="round,pad=0.02,rounding_size=0.15",
                                    fc="#f6f5f2", ec=GRID, lw=1))
        ax.text(x + 1.375, 3.65, head, ha="center", va="center", fontsize=9.6, fontweight="bold", color=INK)
        ax.text(x + 1.375, 2.4, mid, ha="center", va="center", fontsize=8.2, color=INK2, linespacing=1.4)
        ax.add_patch(FancyBboxPatch((x + 0.2, 0.55), 2.35, 0.85, boxstyle="round,pad=0.02,rounding_size=0.1",
                                    fc=SURF, ec=MUTED, lw=0.9))
        ax.text(x + 1.375, 0.97, foot, ha="center", va="center", fontsize=7.8, color=INK, linespacing=1.3)
    for x in (2.95, 5.9, 8.85):
        ax.annotate("", xy=(x + 0.2, 2.4), xytext=(x, 2.4), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1))
    ax.text(0.2, 4.3, "Four distinct questions, four distinct uncertainty objects", fontsize=10.5,
            fontweight="bold", color=INK, va="center")
    return _save(fig, out, "fig9_methods_schematic", readme)


# ---------------------------------------------------------------- Supplementary
def fig_seasonality(pub: Path, out: Path):
    ps = pd.read_csv(pub / "slot_positive_share.csv").dropna(subset=["positive_share"])
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0), sharey=True)
    for ax, c in zip(axes, COUNTRIES):
        for y, style in ((2020, "-"), (2021, (0, (2, 2)))):
            g = ps[(ps.country == c) & (ps.year == y)].sort_values("slot")
            ax.plot(g.slot, g.positive_share, color=COL[c], lw=2, ls=style, label=str(y))
            ax.scatter(g.slot, g.positive_share, s=28, color=COL[c], edgecolor=SURF, linewidth=1.5, zorder=3)
        ax.set_xticks(range(1, 7))
        ax.set_xticklabels([SLOT_LABELS[s] for s in range(1, 7)], fontsize=7.4)
        ax.set_title(c, loc="left")
        _pct(ax)
        ax.legend(fontsize=7.6)
    axes[0].set_ylabel("Observed screens with HHS ≥ 2")
    _note(fig, "Descriptive share among observed designated screens (denominators differ by window; not prevalence "
               "estimates). Malawi shows a strong lean-season (Jan–Feb) peak; Liberia is flatter.")
    return _save(fig, out, "figS1_seasonality")


def fig_fixed_schedules(pub: Path, out: Path):
    fs = pd.read_csv(pub / "fixed_schedules.csv")
    fr = pd.read_csv(pub / "frontier.csv")
    fr = fr[fr.threshold == 2]
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    for c, dx in (("Malawi", -0.12), ("Liberia", 0.12)):
        for m in (1, 2, 3):
            g = fs[(fs.country == c) & (fs.m == m)]
            jitter = np.linspace(-0.05, 0.05, len(g))
            ax.scatter(m + dx + jitter, g.missed_fraction, s=14, color=COL[c], alpha=0.55, edgecolor="none")
            rnd = fr[(fr.country == c) & (fr.m == m)].missed_fraction.item()
            ax.plot([m + dx - 0.09, m + dx + 0.09], [rnd, rnd], color=INK, lw=2)
        ax.scatter([], [], s=14, color=COL[c], label=f"{c}: each fixed schedule")
    ax.plot([], [], color=INK, lw=2, label="Uniform random schedule (mean of fixed)")
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(["1 window", "2 windows", "3 windows"])
    ax.set_ylabel("Reference-positive households missed")
    _pct(ax)
    ax.set_ylim(0, 1)
    ax.legend(fontsize=7.6, loc="upper right")
    ax.set_title("Which windows are kept matters as much as how many", loc="left")
    _note(fig, "All C(6, m) fixed 2020 schedules among complete histories (in-sample, 2020 only; choosing the best "
               "fixed schedule post hoc is optimistic). The random-schedule estimand is the average over fixed schedules.")
    return _save(fig, out, "figS2_fixed_schedules")


def fig_thresholds(pub: Path, out: Path):
    f = pd.read_csv(pub / "frontier.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0), sharey=True)
    styles = {1: (0, (1, 2)), 2: "-", 4: (0, (4, 2))}
    for ax, c in zip(axes, COUNTRIES):
        for t in (1, 2, 4):
            g = f[(f.country == c) & (f.threshold == t)].sort_values("m")
            ax.plot(g.m, g.missed_fraction, color=COL[c] if t == 2 else INK2, lw=2, ls=styles[t],
                    label=f"HHS ≥ {t} (n+ = {g.n_reference_positive.iloc[0]})")
        ax.set_title(c, loc="left")
        ax.set_xlabel("Screens retained (of 6)")
        _pct(ax)
        ax.legend(fontsize=7.4)
    axes[0].set_ylabel("Reference-positive households missed")
    _note(fig, "Secondary thresholds. HHS ≥ 4 (severe) is near-degenerate: every severe-reference household had "
               "exactly one severe window, so the curve equals (6 − m)/6.")
    return _save(fig, out, "figS3_thresholds")


def render_all(pub: Path, figures: Path) -> list[Path]:
    man, sup, rd = figures / "manuscript", figures / "supplementary", figures / "README"
    paths = []
    paths += fig_cohort_flow(pub, man, rd)
    paths += fig_frontier(pub, man, rd)
    paths += fig_k_distribution(pub, sup, rd)
    paths += fig_missing_bounds(pub, man, rd)
    paths += fig_label_error(pub, man, rd)
    paths += fig_timing(pub, man, rd)
    paths += fig_timing_matched(pub, sup, rd)
    paths += fig_observation(pub, sup, rd)
    paths += fig_methods(sup, rd)
    paths += fig_seasonality(pub, sup)
    paths += fig_fixed_schedules(pub, sup)
    paths += fig_thresholds(pub, sup)
    return paths
