"""Household hunger screening: research dashboard (aggregate data only).

Run locally:  streamlit run dashboard/app.py
Every number shown is read from dashboard/data/*.csv, which the analysis pipeline copies from
data/public_aggregates/. No household-level data are loaded or bundled.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FIGS = HERE.parent / "figures"
REPO = "https://github.com/Isaac25-lgtm/household-hunger-screening"
DOI = "https://doi.org/10.1371/journal.pone.0271488"
COL = {"Malawi": "#2a78d6", "Liberia": "#eb6834"}
BAND = {"Malawi": "rgba(42,120,214,0.12)", "Liberia": "rgba(235,104,52,0.12)"}
GREY = "#8a8984"
SLOT = {1: "Jan–Feb", 2: "Mar–Apr", 3: "May–Jun", 4: "Jul–Aug", 5: "Sep–Oct", 6: "Nov–Dec"}
COUNTRIES = ["Malawi", "Liberia"]

st.set_page_config(page_title="Household Hunger Screening", page_icon="🌾", layout="wide")

st.markdown(
    """
<style>
.block-container {max-width: 1180px; padding-top: 2.2rem;}
h1, h2, h3 {letter-spacing: -0.01em;}
.kpi {border: 1px solid rgba(128,128,128,0.25); border-radius: 10px; padding: 14px 16px; height: 100%;}
.kpi .v {font-size: 1.9rem; font-weight: 650; line-height: 1.1;}
.kpi .l {font-size: 0.86rem; opacity: 0.8;}
.kpi .s {font-size: 0.78rem; opacity: 0.7; margin-top: 4px;}
.swatch {display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:6px;}
.caveat {border-left: 4px solid #8a8984; padding: 8px 14px; background: rgba(138,137,132,0.08);
         border-radius: 4px; font-size: 0.92rem;}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def _read_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def load(name: str) -> pd.DataFrame:
    p = DATA / name
    return _read_csv(str(p)) if p.exists() else pd.DataFrame()


@st.cache_data
def summary() -> dict:
    p = DATA / "results_summary.json"
    return json.loads(p.read_text()) if p.exists() else {}


def git_hash() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=HERE, capture_output=True,
                              text=True, timeout=5).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def pct(x: float, d: int = 1) -> str:
    return "–" if pd.isna(x) else f"{100 * x:.{d}f}%"


def base_layout(fig: go.Figure, ytitle: str = "", xtitle: str = "", height: int = 420) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=30, b=10), hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0), font=dict(size=13),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_yaxes(title=ytitle, gridcolor="rgba(128,128,128,0.18)", zeroline=False)
    fig.update_xaxes(title=xtitle, gridcolor="rgba(128,128,128,0.10)", zeroline=False)
    return fig


def empty_guard(df: pd.DataFrame, what: str) -> bool:
    if df.empty:
        st.warning(f"{what} not available. Run `python -m hunger_screening.cli all` to regenerate aggregates.")
        return True
    return False


def kpi(value: str, label: str, sub: str, country: str | None = None) -> None:
    sw = f"<span class='swatch' style='background:{COL[country]}'></span>" if country else ""
    st.markdown(f"<div class='kpi'><div class='l'>{sw}{label}</div><div class='v'>{value}</div>"
                f"<div class='s'>{sub}</div></div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ pages
def page_overview() -> None:
    st.title("Missed household hunger under infrequent screening")
    st.markdown("**Independent reanalysis of rural control households in Malawi and Liberia, 2020–2021** · "
                "research status: *reanalysis complete; manuscript in development (not peer reviewed)*")
    st.markdown(
        "If a programme screens a fixed cohort of households for moderate/severe hunger "
        "(Household Hunger Scale, HHS ≥ 2) but conducts fewer of its scheduled 30-day-recall interviews, "
        "how many households that *would* have screened positive at least once does it miss?"
    )
    f = load("frontier.csv")
    if empty_guard(f, "Frontier results"):
        return
    f = f[f.threshold == 2]
    mb = load("missing_bounds.csv")
    cols = st.columns(4)
    for i, c in enumerate(COUNTRIES):
        r = f[(f.country == c) & (f.m == 1)].iloc[0]
        b = mb[(mb.country == c) & (mb.m == 1)].iloc[0]
        with cols[2 * i]:
            kpi(pct(r.missed_fraction), f"{c}: missed with 1 of 6 screens",
                f"95% village bootstrap {pct(r.ci_low)}–{pct(r.ci_high)} · {int(r.n_reference_positive)} "
                f"reference-positive of {int(r.n_complete)} complete", c)
        with cols[2 * i + 1]:
            kpi(f"{pct(b.lower)}–{pct(b.upper)}", f"{c}: identification range, 1 screen",
                f"no-assumption bounds over all {int(b.frame_households)} frame households "
                "(not a confidence interval)", c)
    st.write("")
    st.markdown(
        "<div class='caveat'><b>What these results do not show.</b> They are not national or annual hunger "
        "prevalence, not an undercount of official statistics or IPC phases, and not the causal effect of "
        "interviewing less often. Six screens cover six ~30-day recall windows, not the whole year. The sample "
        "is the control arm of a cash-transfer study and is not nationally representative.</div>",
        unsafe_allow_html=True,
    )
    st.subheader("Key takeaways")
    tv = load("timing_validation.csv")
    mw = tv[(tv.country == "Malawi") & (tv.cohort == "2021 complete four-slot cohort")]
    mw_line = (f"a single **Jan–Feb** screen chosen on 2020 data missed {pct(mw.missed_frozen.iloc[0])} of "
               f"reference-positive households in 2021, against {pct(mw.missed_random_one_slot.iloc[0])} for a "
               "random window") if not mw.empty else ""
    st.markdown(
        f"""
- **Sparse random screening misses many intermittently hungry households.** With 1, 2 or 3 of six windows
  retained, Malawi misses {pct(f[(f.country=='Malawi')&(f.m==1)].missed_fraction.item())},
  {pct(f[(f.country=='Malawi')&(f.m==2)].missed_fraction.item())} and
  {pct(f[(f.country=='Malawi')&(f.m==3)].missed_fraction.item())}; Liberia
  {pct(f[(f.country=='Liberia')&(f.m==1)].missed_fraction.item())},
  {pct(f[(f.country=='Liberia')&(f.m==2)].missed_fraction.item())} and
  {pct(f[(f.country=='Liberia')&(f.m==3)].missed_fraction.item())}.
- **Timing matters as much as frequency where hunger is seasonal.** In Malawi {mw_line}. In Liberia the
  2020-selected window did not clearly beat a random window in 2021 (very few reference-positive households).
- **Missing follow-up limits what can be said, especially in Liberia** (only 67 of 206 frame households have
  all six 2020 screens), so the Liberia identification range is wide.
"""
    )
    st.caption(f"Source data: Aggarwal et al. (2022) PLOS ONE, [{DOI}]({DOI}), S1 Data (CC BY 4.0). "
               f"Code: [{REPO}]({REPO}) · version {git_hash()}")


def page_cohort() -> None:
    st.header("Cohort and data audit")
    flow = load("cohort_flow.csv")
    if empty_guard(flow, "Cohort flow"):
        return
    t = flow.pivot_table(index=["order", "step"], columns="country", values="count").reset_index()
    st.dataframe(t[["step", "Malawi", "Liberia"]].rename(columns={"step": "Step"}), hide_index=True,
                 use_container_width=True)
    st.subheader("Follow-up by designated window")
    ob = load("observation_pattern.csv")
    ob = ob[ob.observed > 0]
    ob["window"] = ob.slot_label + " " + ob.year.astype(str)
    fig = go.Figure()
    for c in COUNTRIES:
        g = ob[ob.country == c]
        fig.add_trace(go.Scatter(x=g.window, y=g.observed_share, mode="lines+markers", name=c,
                                 line=dict(color=COL[c], width=2), marker=dict(size=9),
                                 customdata=g[["observed", "frame_households"]],
                                 hovertemplate="%{x}<br>%{y:.0%} observed (%{customdata[0]} of %{customdata[1]})"
                                               "<extra>" + c + "</extra>"))
    fig.update_yaxes(tickformat=".0%", range=[0, 1.02])
    st.plotly_chart(base_layout(fig, "Frame households with a valid screen"), use_container_width=True)
    st.caption("Malawi's phone survey ended in Aug 2021, Liberia's in Oct 2021 (windows with no fieldwork omitted).")
    st.subheader("Integrity checks")
    ch = load("integrity_checks.csv")
    st.dataframe(ch, hide_index=True, use_container_width=True)
    st.caption("HHS item consistency: the score is bounded by the three occurrence items (yes-count ≤ HHS ≤ 2×yes-count) "
               "for every record, consistent with FANTA frequency coding. Frequency items are not in the public file, "
               "so the source-provided score is used.")


def page_frontier() -> None:
    st.header("How many households does sparser screening miss?")
    f = load("frontier.csv")
    if empty_guard(f, "Frontier results"):
        return
    thr = st.radio("Reference definition", [2, 1, 4], horizontal=True,
                   format_func=lambda t: {2: "HHS ≥ 2 (primary)", 1: "HHS ≥ 1 (any hunger)", 4: "HHS ≥ 4 (severe; sparse)"}[t])
    g = f[f.threshold == thr]
    fig = go.Figure()
    for c in COUNTRIES:
        d = g[g.country == c].sort_values("m")
        if thr == 2:
            fig.add_trace(go.Scatter(x=list(d.m) + list(d.m[::-1]), y=list(d.ci_high) + list(d.ci_low[::-1]),
                                     fill="toself", fillcolor=BAND[c], line=dict(width=0), hoverinfo="skip",
                                     showlegend=False))
        cd = d[["n_reference_positive", "n_complete"]].copy()
        cd["ci"] = [f"{pct(a)}–{pct(b)}" if thr == 2 else "n/a (secondary)" for a, b in
                    zip(d.get("ci_low", d.m), d.get("ci_high", d.m))]
        fig.add_trace(go.Scatter(x=d.m, y=d.missed_fraction, mode="lines+markers", name=c,
                                 line=dict(color=COL[c], width=2), marker=dict(size=10),
                                 customdata=cd.to_numpy(),
                                 hovertemplate="m = %{x} screens<br>missed %{y:.1%}<br>95% bootstrap %{customdata[2]}"
                                               "<br>%{customdata[0]} reference-positive of %{customdata[1]}<extra>"
                                               + c + "</extra>"))
    fig.update_yaxes(tickformat=".0%", range=[0, 0.9])
    fig.update_xaxes(dtick=1)
    st.plotly_chart(base_layout(fig, "Reference-positive households missed",
                                "Screens retained out of six 2020 windows (uniformly random)"), use_container_width=True)
    st.caption("Exact expected values. Shaded bands (primary threshold only): 95% village-cluster percentile bootstrap, "
               "2,000 draws, conditional on complete histories.")
    show = g[["country", "m", "n_complete", "n_reference_positive", "missed_fraction", "expected_missed_households"]].copy()
    if thr == 2:
        show["95% bootstrap"] = [f"{pct(a)}–{pct(b)}" for a, b in zip(g.ci_low, g.ci_high)]
    show["missed_fraction"] = show.missed_fraction.map(pct)
    st.dataframe(show, hide_index=True, use_container_width=True)
    if thr == 4:
        st.info("Severe hunger is near-degenerate here: every severe-reference household was severe in exactly one window, "
                "so the curve equals (6 − m)/6 and carries little information.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("How intermittent is hunger?")
        kd = load("k_distribution.csv")
        kd = kd[kd.threshold == thr]
        fig = go.Figure()
        for c in COUNTRIES:
            d = kd[kd.country == c]
            fig.add_trace(go.Bar(x=d.k_positive_windows, y=d.households / d.households.sum(), name=c,
                                 marker_color=COL[c], customdata=d.households,
                                 hovertemplate="%{x} positive windows<br>%{y:.0%} (%{customdata} households)<extra>"
                                               + c + "</extra>"))
        fig.update_layout(barmode="group", bargap=0.35)
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(base_layout(fig, "Share of complete households", "Positive windows (of 6)", 340),
                        use_container_width=True)
    with c2:
        st.subheader("Which windows are kept matters")
        fs = load("fixed_schedules.csv")
        mm = st.select_slider("Windows kept", [1, 2, 3], value=1, key="fsm")
        d = fs[fs.m == mm].sort_values("missed_fraction")
        fig = go.Figure()
        for c in COUNTRIES:
            e = d[d.country == c]
            fig.add_trace(go.Scatter(x=e.missed_fraction, y=e.schedule, mode="markers", name=c,
                                     marker=dict(color=COL[c], size=10),
                                     hovertemplate="%{y}<br>missed %{x:.1%}<extra>" + c + "</extra>"))
        fig.update_xaxes(tickformat=".0%", range=[0, 1])
        st.plotly_chart(base_layout(fig, "", "Missed (2020, in-sample)", 340), use_container_width=True)
        st.caption("Every fixed schedule, 2020 complete histories (primary threshold). Picking the best post hoc "
                   "is optimistic; see the Timing page for an out-of-year check.")


def page_bounds() -> None:
    st.header("Missing screens: identification ranges")
    st.markdown("<div class='caveat'><b>IDENTIFICATION BOUNDS — NOT CONFIDENCE INTERVALS.</b> These ranges contain every "
                "value of the estimand compatible with the observed data when each missing 2020 window could be "
                "positive or negative. They do not shrink with more bootstrap draws and say nothing about sampling "
                "variability.</div>", unsafe_allow_html=True)
    mb = load("missing_bounds.csv")
    f = load("frontier.csv")
    if empty_guard(mb, "Bounds"):
        return
    f = f[f.threshold == 2]
    fig = go.Figure()
    for c in COUNTRIES:
        d = mb[(mb.country == c) & (mb.m <= 5)]
        p = f[(f.country == c) & (f.m <= 5)]
        fig.add_trace(go.Bar(x=d.upper - d.lower, base=d.lower, y=[f"{c} · m={m}" for m in d.m], orientation="h",
                             marker=dict(color=BAND[c].replace("0.12", "0.35"), pattern_shape="/", line=dict(width=0)),
                             name=f"{c}: identification range",
                             customdata=d[["lower", "upper", "households_any_missing", "frame_households"]],
                             hovertemplate="range %{customdata[0]:.1%}–%{customdata[1]:.1%}<br>%{customdata[2]} of "
                                           "%{customdata[3]} households with a missing window<extra></extra>"))
        fig.add_trace(go.Scatter(x=p.missed_fraction, y=[f"{c} · m={m}" for m in p.m], mode="markers",
                                 marker=dict(color=COL[c], size=10, line=dict(color="white", width=2)),
                                 error_x=dict(type="data", symmetric=False, array=p.ci_high - p.missed_fraction,
                                              arrayminus=p.missed_fraction - p.ci_low, color="#555", thickness=1.2),
                                 name=f"{c}: complete-history estimate ± 95% bootstrap",
                                 hovertemplate="complete-history %{x:.1%}<extra></extra>"))
    fig.update_xaxes(tickformat=".0%", range=[0, 1])
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(base_layout(fig, "", "Reference-positive households missed", 520), use_container_width=True)
    show = mb[["country", "m", "frame_households", "households_any_missing", "households_never_observed", "lower",
               "upper", "all_missing_negative", "all_missing_positive", "complete_case_point"]].copy()
    for c in ["lower", "upper", "all_missing_negative", "all_missing_positive", "complete_case_point"]:
        show[c] = show[c].map(pct)
    st.dataframe(show, hide_index=True, use_container_width=True)
    st.caption("Filling every missing window with 'negative' or 'positive' gives values strictly inside the sharp range: "
               "because the reference-positive denominator changes with the completion, single imputations are not the "
               "endpoints. Bounds are computed exactly (rational arithmetic) and verified against brute-force enumeration.")


def page_label_error() -> None:
    st.header("Hypothetical label-error sensitivity")
    st.markdown("<div class='caveat'>The slider sets a <b>hypothetical</b> budget: the share of observed binary screens "
                "(HHS ≥ 2 vs &lt; 2) in each country that could be misclassified, shared across all households. It is "
                "<b>not</b> an estimated error rate — no validation data on HHS misclassification exist in this source.</div>",
                unsafe_allow_html=True)
    le = load("label_error_bounds.csv")
    if empty_guard(le, "Label-error bounds"):
        return
    c1, c2 = st.columns(2)
    scope = c1.radio("Population", ["frame_missing_arbitrary", "complete_histories_only"], horizontal=True,
                     format_func=lambda s: {"frame_missing_arbitrary": "Whole frame (missing windows arbitrary)",
                                            "complete_histories_only": "Complete histories only"}[s])
    m = c2.select_slider("Screens retained (m)", [1, 2, 3, 4, 5], value=1)
    d = le[(le.scope == scope) & (le.m == m)].sort_values("alpha")
    fig = go.Figure()
    for i, c in enumerate(COUNTRIES):
        e = d[d.country == c]
        fig.add_trace(go.Bar(x=[f"{a:.0%}" for a in e.alpha], y=e.upper - e.lower, base=e.lower, name=c,
                             marker=dict(color=COL[c], opacity=0.45, pattern_shape="/"), offsetgroup=i,
                             customdata=e[["lower", "upper", "budget_flips"]],
                             hovertemplate="budget %{x} (%{customdata[2]} flips)<br>range %{customdata[0]:.1%}–"
                                           "%{customdata[1]:.1%}<extra>" + c + "</extra>"))
    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    st.plotly_chart(base_layout(fig, "Reference-positive households missed", "Hypothetical flip budget"),
                    use_container_width=True)
    st.caption("Exact optimum via Dinkelbach iteration over an exact budgeted dynamic programme; every run terminated with "
               "the optimality certificate F(λ*) = 0. Ranges nest as the budget grows, and 0% equals the missing-data bounds.")


def page_timing() -> None:
    st.header("Calendar timing: choose on 2020, test frozen on 2021")
    tc = load("timing_candidates.csv")
    tv = load("timing_validation.csv")
    ss = load("timing_selection_stability.csv")
    if empty_guard(tc, "Timing results"):
        return
    country = st.radio("Country", COUNTRIES, horizontal=True)
    d = tc[tc.country == country]
    fig = go.Figure()
    for y, op in ((2020, 1.0), (2021, 0.45)):
        e = d[d.year == y].sort_values("slot")
        fig.add_trace(go.Bar(x=[SLOT[s] for s in e.slot], y=e.missed_fraction, name=f"{y}" + (" (selection)" if y == 2020 else " (frozen test)"),
                             marker=dict(color=COL[country], opacity=op, pattern_shape="" if y == 2020 else "."),
                             customdata=e[["n_missed", "n_reference_positive", "selected"]],
                             hovertemplate="%{x} " + str(y) + "<br>missed %{y:.1%} (%{customdata[0]} of %{customdata[1]})"
                                           "<br>selected on 2020: %{customdata[2]}<extra></extra>"))
        fig.add_hline(y=e.random_one_slot.iloc[0], line=dict(color=GREY, width=1, dash="solid" if y == 2020 else "dot"),
                      annotation_text=f"random window {y}", annotation_position="top left")
    fig.update_layout(barmode="group", bargap=0.35)
    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    st.plotly_chart(base_layout(fig, "Reference-positive households missed by one fixed window"), use_container_width=True)
    sel = d[(d.year == 2020) & d.selected].slot.iloc[0]
    st.markdown(f"**Selected on 2020 only:** {SLOT[int(sel)]} (ties → earlier window). The 2021 bars for other windows "
                "are post hoc disclosure, not a re-selection.")
    v = tv[(tv.country == country) & (tv.cohort != "Matched: 2020 performance of frozen slot")].copy()
    v["frozen"] = [f"{pct(a)} ({pct(lo)}–{pct(hi)})" for a, lo, hi in zip(v.missed_frozen, v.frozen_ci_low, v.frozen_ci_high)]
    v["random"] = [f"{pct(a)} ({pct(lo)}–{pct(hi)})" for a, lo, hi in
                   zip(v.missed_random_one_slot, v.random_ci_low, v.random_ci_high)]
    v["difference (pp)"] = [f"{100 * (a - b):.1f} ({100 * lo:.1f} to {100 * hi:.1f})" for a, b, lo, hi in
                            zip(v.missed_frozen, v.missed_random_one_slot, v.diff_ci_low, v.diff_ci_high)]
    st.dataframe(v[["cohort", "n_complete", "n_reference_positive", "frozen", "random", "difference (pp)"]],
                 hide_index=True, use_container_width=True)
    if country == "Liberia":
        st.warning("Liberia 2021 estimates rest on 22 (full cohort) and 13 (matched) reference-positive households; "
                   "the 2020 choice itself was unstable under resampling. Treat as uninformative about timing.")
    s = ss[ss.country == country]
    st.caption("Share of 2,000 village-bootstrap re-runs of the 2020 selection won by each window: " +
               ", ".join(f"{SLOT[int(r.slot)]} {r.selection_frequency_2020_bootstrap:.0%}" for r in s.itertuples()))
    st.caption("Two adjacent pandemic-era years cannot establish a stable seasonal optimum; this is not a causal estimate "
               "of moving a survey calendar.")


def page_methods() -> None:
    st.header("Methods and formulas")
    st.markdown("**Primary estimand.** For complete household *i* with *K* positive windows among *n* = 6, and *m* windows "
                "retained uniformly at random without replacement:")
    st.latex(r"p_{\text{miss}}(K;n,m)=\frac{\binom{n-K}{m}}{\binom{n}{m}},\qquad "
             r"M_m=\frac{\sum_i \mathbf 1[K_i>0]\,p_{\text{miss}}(K_i;n,m)}{\sum_i \mathbf 1[K_i>0]}")
    st.markdown("Exact design arithmetic (hypergeometric zero-success probability), verified against enumeration of "
                "every subset. Households never positive are outside the denominator.")
    st.markdown("**Clustered sampling variability.** Villages resampled with replacement within country (2,000 draws, "
                "seed 20261026), percentile intervals; stability checked with 20,000 draws, all-frame villages and a "
                "delete-one-village jackknife.")
    st.markdown("**Sharp missing-history bounds.** Each frame household's completed count can be any "
                "K ∈ {k, …, k + r}. Because M_m is a mean over the *included* set, the optimum gives each included "
                "household its extreme value and adds optional households (k = 0, r > 0) as a sorted prefix; all "
                "prefixes are evaluated exactly.")
    st.markdown("**Label-error budget.** Minimum observed flips to reach K:")
    st.latex(r"\text{cost}(K)=\max(0,\;k-K,\;K-k-r)")
    st.markdown("subject to one shared budget B = ⌊α · observed screens⌋ per country. The ratio is optimised by "
                "Dinkelbach's method with each parametric subproblem solved exactly as a budgeted multiple-choice "
                "knapsack (integer DP). Termination certifies optimality.")
    st.markdown("**Timing.** The single best of four common windows (Jan–Aug) is chosen on 2020 complete histories only "
                "(ties → earlier), frozen, and evaluated in 2021 and in households complete in both years.")
    st.markdown("**Why no machine learning.** The target is an exact design quantity of observed histories, not a future "
                "label; a predictive model would add assumptions and no information about this estimand. A prospective "
                "next-window prediction task was considered and rejected (few clusters and events, especially in Liberia, "
                "and no programme decision rule to evaluate against).")


def page_limits() -> None:
    st.header("Limitations and closest prior work")
    st.markdown(
        """
**Main threats to validity**
- *Retrospective thinning*: removing recorded interviews is not the same as conducting fewer interviews (recall,
  panel conditioning and attrition could differ in a real sparse design).
- *Observation windows*: each screen recalls ~30 days; months between windows are unobserved.
- *Selection*: complete histories are a selected subset (Liberia 33% of frame); the bounds show how much this matters.
- *Measurement*: HHS is self-reported; the label-error analysis is hypothetical, not estimated.
- *Seasonality and period*: 2020–2021 overlaps COVID-19 disruptions; Malawi's lean season dominates its timing result.
- *Generalisability*: control households of a cash-transfer study in selected rural areas; not national samples.

**Closest prior work (verified bibliographic records)**
- Zhu, Gupta, Doan & Michuda (2026), *Food Security* 18(5):1509–1524 — single-round surveys misclassify 15–48% of
  households against a weekly-diary annual benchmark (India). Same core message; different data, indicators,
  benchmark and methods.
- Na et al. (2017), *BMC Public Health* 17:260 — monthly HFI in Zambia; within-household variance exceeds between.
- Livings et al. (2023), *Am J Prev Med* 65(4):657–666 — past-year questions under-report food insecurity reported weekly.
- Aggarwal et al. (2022), *PLOS ONE* 17(8):e0271488 — the source study (mean outcomes during COVID-19).

This work's increment is an explicit household-ascertainment estimand for HHS screening, the interview-count
frontier, sharp missing-history and label-error identification ranges, and a frozen out-of-year timing test.
None of these methods is new in itself.
"""
    )


def page_downloads() -> None:
    st.header("Downloads and reproducibility")
    st.markdown("All files below are aggregate outputs. No household or village identifiers are included.")
    files = sorted(DATA.glob("*.csv"))
    cols = st.columns(3)
    for i, p in enumerate(files):
        with cols[i % 3]:
            st.download_button(p.name, p.read_bytes(), file_name=p.name, mime="text/csv", key=f"d{i}")
    figs = sorted((FIGS / "manuscript").glob("*.pdf")) if (FIGS / "manuscript").exists() else []
    if figs:
        st.subheader("Manuscript figures (PDF)")
        cols = st.columns(3)
        for i, p in enumerate(figs):
            with cols[i % 3]:
                st.download_button(p.name, p.read_bytes(), file_name=p.name, mime="application/pdf", key=f"f{i}")
    s = summary()
    st.subheader("Provenance")
    st.code(f"Source supplement: 10.1371/journal.pone.0271488.s021\nSHA-256: {s.get('source', {}).get('sha256', 'n/a')}\n"
            f"Config SHA-256: {s.get('config_sha256', 'n/a')}\nCode version: {git_hash()}", language="text")
    st.markdown(f"Reproduce: clone [{REPO}]({REPO}), then `scripts/run_all.ps1` (Windows) or "
                "`python -m hunger_screening.cli all` — the source archive is downloaded from PLOS and hash-verified.")


PAGES = {
    "Overview": page_overview,
    "Cohort & data audit": page_cohort,
    "Screening frontier": page_frontier,
    "Missing-data bounds": page_bounds,
    "Label-error sensitivity": page_label_error,
    "Calendar timing": page_timing,
    "Methods & formulas": page_methods,
    "Limitations & literature": page_limits,
    "Downloads": page_downloads,
}

with st.sidebar:
    st.markdown("### Household hunger screening")
    choice = st.radio("Section", list(PAGES), label_visibility="collapsed")
    st.markdown("---")
    st.caption("Malawi <span class='swatch' style='background:#2a78d6'></span> · Liberia "
               "<span class='swatch' style='background:#eb6834'></span>", unsafe_allow_html=True)
    st.caption("Aggregate results only. Not peer reviewed.")

PAGES[choice]()
