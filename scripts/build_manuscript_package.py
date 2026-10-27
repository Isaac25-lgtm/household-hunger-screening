"""Build the manuscript materials package (figures, tables, results, methods, references, code).

1. Writes manuscript-ready tables for the investigation and review analyses to
   tables/investigation/ (CSV + Markdown), from data/public_aggregates only.
2. Assembles a zip of release-safe files (git-tracked or freshly generated aggregates;
   never data/raw, data/interim or logs) with a guide, 00_READ_ME_FIRST.md.

Usage: python scripts/build_manuscript_package.py [output_dir]
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "data" / "public_aggregates"
TAB = ROOT / "tables" / "investigation"


def pct(x):
    return f"{100 * x:.1f}%"


def pp(x):
    return f"{100 * x:+.1f}"


def ci(lo, hi):
    return f"{100 * lo:+.1f} to {100 * hi:+.1f}"


def save(df: pd.DataFrame, name: str, title: str, note: str) -> None:
    TAB.mkdir(parents=True, exist_ok=True)
    df.to_csv(TAB / f"{name}.csv", index=False)
    md = f"**{title}**\n\n" + df.to_markdown(index=False, disable_numparse=True) + f"\n\n*{note}*\n"
    (TAB / f"{name}.md").write_text(md, encoding="utf-8")


def build_tables() -> None:
    inv, mc, rv = PUB / "investigation", PUB / "multicountry", PUB / "review"
    # Main Table 3: Malawi timing evidence, by evidence class
    tv = pd.read_csv(PUB / "timing_validation.csv")
    tv = tv[(tv.country == "Malawi") & (tv.cohort == "2021 complete four-slot cohort")].iloc[0]
    jj = pd.read_csv(inv / "aggarwal_july_june_test.csv")
    jj = jj[jj.selected_on_train].iloc[0]
    cal = pd.read_csv(rv / "calendar_lean_season_sensitivity.csv")
    fp = pd.read_csv(rv / "frozen_best_pair.csv").iloc[0]
    rows = []
    c20 = cal[(cal.country == "Malawi") & (cal.horizon == "calendar 2020 (six windows)")].iloc[0]
    rows.append(["Exploratory, in-sample", "Calendar 2020", "6 windows", int(c20.n_reference_positive), "Jan-Feb",
                 pct(c20.window_missed), pct(c20.random_missed), pp(c20["diff"]), ci(c20.diff_ci_low, c20.diff_ci_high)])
    rows.append(["Out-of-time, not blind", "Chosen 2020, tested Jan-Aug 2021", "4 windows", int(tv.n_reference_positive), "Jan-Feb",
                 pct(tv.missed_frozen), pct(tv.missed_random_one_slot), pp(tv.missed_frozen - tv.missed_random_one_slot),
                 ci(tv.diff_ci_low, tv.diff_ci_high)])
    rows.append(["Out-of-time, not blind", "Chosen Jul 2019-Jun 2020, tested Jul 2020-Jun 2021", "6 windows",
                 int(jj.n_test_reference_positive), jj.candidate, pct(jj.test_missed), pct(jj.test_random_missed),
                 pp(jj.diff_vs_random), ci(jj.diff_ci_low, jj.diff_ci_high)])
    rows.append(["Out-of-time, not blind", "Best pair chosen Jul 2019-Jun 2020, tested Jul 2020-Jun 2021", "6 windows (2 contacts)",
                 int(fp.n_test_reference_positive), fp.selected_pair, pct(fp.test_missed_frozen_pair), pct(fp.test_missed_random_pair),
                 pp(fp["diff"]), ci(fp.diff_ci_low, fp.diff_ci_high)])
    dup = {("Malawi", "calendar 2020 (six windows)"), ("Malawi", "Jul 2020 - Jun 2021 (six windows)"),
           ("Malawi", "calendar 2021 (Jan-Aug, four windows)")}
    for _, r in cal.iterrows():
        if (r.country, r.horizon) in dup:
            continue  # calendar window = data-chosen window (Jan-Feb): identical to the rows above
        rows.append(["Calendar-based sensitivity, not blind", f"{r.country}: {r.horizon}", f"{r.reference_windows} windows",
                     int(r.n_reference_positive), r.calendar_window, pct(r.window_missed), pct(r.random_missed),
                     pp(r["diff"]), ci(r.diff_ci_low, r.diff_ci_high)])
    save(pd.DataFrame(rows, columns=["Evidence class", "Analysis", "Reference", "Reference-positive households", "Window(s)",
                                     "Missed", "Random missed", "Difference (pp)", "95% CI (pp)"]),
         "table3_timing_evidence_classes", "Table 3. Timing of a single contact (or pair) against random timing, by evidence class (HHS 2 or more)",
         "Trial data (Aggarwal et al. 2022). Calendar window from FEWS NET typical-year lean season (Malawi Dec-Feb, Liberia Jun-Aug). "
         "95% village-cluster bootstrap. Rows with different references are not directly comparable. None of these analyses is blind. "
         "In Malawi calendar 2020, Jan-Aug 2021 and Jul 2020-Jun 2021 the calendar window is the same Jan-Feb window chosen from the data, "
         "so those rows also serve as calendar-based results; only the additional calendar-based horizons are listed separately.")
    # Main Table 4: locked five-country test
    h1 = pd.read_csv(mc / "h1_calendar_rule.csv")
    h3 = pd.read_csv(mc / "h3_second_contact.csv").dropna(subset=["difference"])
    names = {"BFA": "Burkina Faso", "UGA": "Uganda", "ETH": "Ethiopia"}
    t4 = [[("Primary" if a.startswith("primary") else "Sensitivity (D2)"), "H1 calendar rule", f"{names[c]} {y}-{str(y + 1)[2:]}", rr,
           int(n), pct(m1), pct(m2), pp(d), ci(lo, hi)]
          for a, c, y, rr, n, m1, m2, d, lo, hi in zip(h1.analysis, h1.country, h1.horizon_start_year, h1.rule_round,
                                                        h1.n_reference_positive, h1.rule_missed, h1.random_missed, h1["diff"],
                                                        h1.diff_ci_low, h1.diff_ci_high)]
    t4 += [[("Primary" if r.analysis.startswith("primary") else "Sensitivity (D2)"), "H3 second-contact rule",
            f"{names[r.country]} {r.horizon_start_year}-{str(r.horizon_start_year + 1)[2:]}", f"first contact R{r.first_round}",
            int(r.recontact_budget), f"{r.warning_per_100:.1f} per 100", f"{r.random_per_100:.1f} per 100",
            f"{r.difference:+.1f}", f"{r.ci_low:+.1f} to {r.ci_high:+.1f}"] for _, r in h3.iterrows()]
    save(pd.DataFrame(t4, columns=["Analysis", "Hypothesis", "Horizon", "Contact chosen by rule", "Reference positives (H1) / re-contacted (H3)",
                                   "Rule result", "Random", "Difference", "95% CI"]),
         "table4_locked_multicountry_test", "Table 4. Locked five-country test (protocol committed before download)",
         "World Bank LSMS phone surveys; item 'hungry but did not eat' (FIES item 7, 30-day recall). H1 decision: contradicted; "
         "H3 decision: supported. H1 differences in percentage points of missed share; H3 in later positives per 100 re-contacted. "
         "Nigeria and Tanzania had no usable horizon; Ethiopia excluded from H1 by protocol.")
    # Supplementary tables
    b = pd.read_csv(rv / "missing_bounds_second_scope.csv")
    b["range"] = [f"{100 * lo:.1f} to {100 * hi:.1f}%" for lo, hi in zip(b.lower, b.upper)]
    save(b[["country", "scope", "households", "never_observed", "m", "range"]], "tableS5_bounds_second_scope",
         "Table S5. Missing-history identification ranges, all frame households vs households observed at least once (2020)",
         "Exact identification ranges, not confidence intervals.")
    s = pd.read_csv(rv / "single_window_positives.csv")
    save(s.round(3), "tableS6_single_window_positives", "Table S6. Single-window positives and the persistent-only reference",
         "Persistent-only reference: households positive in at least two of six 2020 windows.")
    save(pd.read_csv(rv / "random_error_simulation.csv").round(3), "tableS7_random_error_simulation",
         "Table S7. Malawi calendar-window advantage under hypothetical random answer error",
         "Flip rates are hypothetical, not estimated error rates. 1,000 simulations per rate.")
    save(pd.read_csv(rv / "hhs_scoring_check_records.csv"), "tableS8_hhs_scoring_check",
         "Table S8. HHS scoring check against item counts", "Consistent with standard FANTA scoring built from the 'no food' item.")
    save(pd.read_csv(rv / "recall_overlap_discordance.csv").round(4), "tableS9_recall_overlap_discordance",
         "Table S9. Answer discordance between World Bank Malawi rounds under 30 days apart",
         "Discordance mixes real change, recall differences and reporting error; it is not a misclassification rate.")
    hs = pd.read_csv(inv / "hfps_single_round.csv")
    save(hs[["cohort", "item", "schedule", "n_complete", "n_reference_positive", "missed_share", "missed_ci_district_low",
             "missed_ci_district_high", "diff_vs_random", "diff_ci_district_low", "diff_ci_district_high"]].round(3),
         "tableS10_worldbank_malawi_single_round", "Table S10. World Bank Malawi: single-round missed share against random",
         "District-cluster bootstrap (approximate; no PSU in public files).")
    tt = pd.read_csv(inv / "hfps_transfer_tests.csv")
    save(tt[tt.selected_on_train].round(3), "tableS11_worldbank_transfer_tests", "Table S11. World Bank Malawi transfer tests (selected rounds)",
         "Not blind: round-level rates had been seen.")
    save(pd.read_csv(inv / "hfps_model_vs_rule.csv").round(2), "tableS12_model_vs_rule", "Table S12. Second-contact targeting: model vs simple rules",
         "Logistic model trained on 2020 rounds only.")
    save(pd.read_csv(inv / "hfps_subgroups.csv").round(3), "tableS13_who_is_missed", "Table S13. Exploratory subgroup analysis (World Bank Malawi 2021)",
         "22 unadjusted comparisons; hypothesis-generating only.")
    save(pd.read_csv(mc / "horizons.csv"), "tableS14_multicountry_horizons", "Table S14. Five-country test: rounds, horizons and usability",
         "Usability rules fixed in the locked protocol.")


FIGURES_MAIN = [
    ("figures/manuscript/fig1_cohort_flow", "Figure1_cohort_flow"),
    ("figures/manuscript/fig2_frontier", "Figure2_screening_frontier"),
    ("figures/supplementary/fig3_intermittency", "Figure3_intermittency"),
    ("figures/investigation/figI1_timing_across_datasets", "Figure4_timing_two_Malawi_panels"),
    ("figures/investigation/figI6_multicountry_locked_test", "Figure5_locked_five_country_test"),
    ("figures/investigation/figI3_decision_robustness", "Figure6_decision_robustness"),
]
FIGURES_SUPP = [
    ("figures/manuscript/fig4_missing_bounds", "FigureS1_missing_bounds"),
    ("figures/manuscript/fig5_label_error", "FigureS2_label_error_sensitivity"),
    ("figures/manuscript/fig6_timing", "FigureS3_timing_2020_2021"),
    ("figures/supplementary/fig7_timing_matched", "FigureS4_timing_matched_households"),
    ("figures/investigation/figI2_transfer_tests", "FigureS5_transfer_tests"),
    ("figures/investigation/figI5_contact_yield", "FigureS6_contact_yield_second_contact"),
    ("figures/investigation/figI4_who_is_missed", "FigureS7_who_is_missed"),
    ("figures/supplementary/fig8_observation_pattern", "FigureS8_observation_pattern"),
    ("figures/supplementary/figS1_seasonality", "FigureS9_seasonality"),
    ("figures/supplementary/figS2_fixed_schedules", "FigureS10_fixed_schedules"),
    ("figures/supplementary/figS3_thresholds", "FigureS11_thresholds"),
    ("figures/supplementary/fig9_methods_schematic", "FigureS12_methods_schematic"),
]
TABLES_MAIN = [("tables/table1_cohort_flow", "Table1_cohort_flow"), ("tables/table2_main_frontier", "Table2_screening_frontier"),
               ("tables/investigation/table3_timing_evidence_classes", "Table3_timing_evidence_classes"),
               ("tables/investigation/table4_locked_multicountry_test", "Table4_locked_five_country_test")]
REPORTS = {
    "04_methods_results_reports": ["reports/ALL_FINDINGS.md", "reports/REVIEW_RESPONSE.md", "reports/FULL_SCIENTIFIC_ANALYSIS_REPORT.md",
                                   "reports/METHOD_SELECTION_AND_MODELS.md", "reports/DATA_QUALITY_AND_COHORT_FLOW.md",
                                   "reports/REPRODUCTION_AUDIT.md", "reports/VALIDATION_AND_TEST_RESULTS.md",
                                   "reports/LIMITATIONS_AND_THREATS.md", "reports/MANUSCRIPT_READINESS_VERDICT.md",
                                   "reports/NOVELTY_AND_CLOSEST_WORK.md", "reports/tables_figure_index.md"],
    "04_methods_results_reports/investigation": [f"reports/investigation/{n}" for n in (
        "README.md", "00_PROTOCOL_AND_EXPOSURE_LOG.md", "01_FULL_INVESTIGATION_REPORT.md", "02_DECISION_MEMO.md",
        "03_DATASET_INVENTORY_AND_ACCESS_LEDGER.md", "03_DATASET_INVENTORY_AND_ACCESS_LEDGER.csv", "04_CLOSEST_PRIOR_WORK.md",
        "05_NEGATIVE_FAILED_UNSTABLE_BLOCKED_TESTS.md", "06_MANUSCRIPT_OPTIONS.md", "07_REQUIRED_WORK_BEFORE_SUBMISSION.md",
        "08_LIMITATIONS_AND_UNRESOLVED_CLAIMS.md", "10_LOCKED_PROTOCOL_MULTICOUNTRY_HFPS.md", "11_MULTICOUNTRY_RESULTS.md")],
    "05_references_and_ledgers": ["reports/literature_ledger.csv", "reports/CLAIM_EVIDENCE_LEDGER.csv"],
}
CODE = ["src", "config", "tests", "scripts", "dashboard", "pyproject.toml", "requirements-lock.txt", "README.md", "CITATION.cff",
        "LICENSE", ".github/workflows/ci.yml", "docs/DEVELOPMENT_LOG.md"]


def tracked() -> set[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return set(out.splitlines())


def guide() -> str:
    return f"""# Manuscript materials package

*Omoding Isaac (MSc Data Science and Analytics; Ministry of Health, Uganda). Built {date.today():%d %B %Y} from the repository
https://github.com/Isaac25-lgtm/household-hunger-screening (branch `main`). Aggregate results only: no microdata, household
identifiers or credentials are included.*

## Working title

When to ask about hunger: seasonal timing helps in Malawi but does not transfer as a calendar rule, while a simple
second-contact rule does.

## Folder map

| Folder | Contents |
|---|---|
| `01_figures/main` | Proposed main figures 1 to 6 (PNG 300 dpi, PDF, SVG) |
| `01_figures/supplementary` | Supplementary figures S1 to S12 |
| `02_tables/main` | Proposed main tables 1 to 4 (CSV and Markdown) |
| `02_tables/supplementary` | Supplementary tables (trial-data S1 to S4, investigation and review S5 to S14, plus bounds and timing tables) |
| `03_results_data` | Every aggregate result file behind the figures and tables (trial data, `investigation/`, `multicountry/`, `review/`) |
| `04_methods_results_reports` | Findings summary, review response, full analysis report, methods and model choices, data quality, reproduction and validation audits, limitations, novelty, and the investigation reports (including the locked protocol and its results) |
| `05_references_and_ledgers` | Literature ledger, claim-evidence ledger, `DATA_CITATIONS.md` |
| `06_code_snapshot` | Analysis code, configuration (including the locked protocol parameters), tests and scripts, to cite or deposit |

## Proposed manuscript structure and where each part comes from

| Section | Source in this package |
|---|---|
| Introduction and prior work | `04.../investigation/04_CLOSEST_PRIOR_WORK.md`; `05.../literature_ledger.csv` |
| Data | `04.../DATA_QUALITY_AND_COHORT_FLOW.md`; `04.../investigation/03_DATASET_INVENTORY_AND_ACCESS_LEDGER.md`; Table 1; Figure 1 |
| Measurement (HHS, FIES items) | `04.../REVIEW_RESPONSE.md` section 1; Table S8 |
| Methods (estimand, bootstrap, exact bounds, frozen and calendar tests, locked protocol) | `04.../METHOD_SELECTION_AND_MODELS.md`; `04.../investigation/01_FULL_INVESTIGATION_REPORT.md` section 7; `04.../investigation/10_LOCKED_PROTOCOL_MULTICOUNTRY_HFPS.md`; Figure S12 |
| Results 1: frequency and intermittency | Table 2; Figures 2 and 3; Figure S1 |
| Results 2: timing in Malawi (by evidence class) | Table 3; Figure 4; Figures S3 to S5 |
| Results 3: locked five-country test | Table 4; Figure 5; `04.../investigation/11_MULTICOUNTRY_RESULTS.md` |
| Results 4: second contact | Table 4 (H3); Figure S6; Table S12 |
| Robustness | Figure 6; Tables S5 to S7, S9; Figure S2 |
| Limitations | `04.../LIMITATIONS_AND_THREATS.md`; `04.../investigation/08_LIMITATIONS_AND_UNRESOLVED_CLAIMS.md` |
| Data availability, code availability, AI-use statement | `05.../DATA_CITATIONS.md`; `06_code_snapshot/README.md` |

## Rules to keep when writing

- Keep the three uncertainty objects separate:
  - bootstrap confidence intervals;
  - identification ranges, which are not confidence intervals;
  - hypothetical answer-error envelopes.
- The 21.6% (four windows, January to August 2021, 102 reference positives) and 38.3% (six windows, July 2020 to June 2021,
  133 reference positives) results use different references. Do not compare them directly.
- Label every timing result by evidence class (Table 3). Only the five-country test is prespecified and blind.
- Report discordance between overlapping recall periods as discordance, not as an error rate.
- Do not claim:
  - national or annual prevalence, or IPC phases;
  - causal effects of interviewing less;
  - cost-effectiveness;
  - an optimal schedule;
  - that the World Bank items are the HHS;
  - being first.

## Still to do before submission

1. Confirm the HHS phone questionnaire and scoring with the source authors.
2. Add the co-researchers (also in `CITATION.cff`).
3. Statistical review of the exact-bound solvers and bootstrap choices.
4. Institutional ethics determination.
5. Use each catalog's exact citation text for the World Bank datasets.
"""


def data_citations() -> str:
    src = (ROOT / "reports" / "investigation" / "README.md").read_text(encoding="utf-8")
    part = src[src.index("## Data sources and citations"):]
    return "# Data citations\n\n" + part.split("\n", 1)[1]


def main() -> int:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads"
    build_tables()
    t = tracked()
    name = f"household_hunger_manuscript_package_{date.today():%Y-%m-%d}"
    stage = ROOT / "build" / name
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    def put(src: Path, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    for group, sub in ((FIGURES_MAIN, "main"), (FIGURES_SUPP, "supplementary")):
        for src, new in group:
            for ext in (".png", ".pdf", ".svg"):
                p = ROOT / (src + ext)
                if p.exists():
                    put(p, stage / "01_figures" / sub / (new + ext))
    for src, new in TABLES_MAIN:
        for ext in (".csv", ".md"):
            put(ROOT / (src + ext), stage / "02_tables" / "main" / (new + ext))
    main_tabs = {Path(s).name for s, _ in TABLES_MAIN}
    for p in sorted((ROOT / "tables").rglob("*")):
        if p.is_file() and p.stem not in main_tabs:
            put(p, stage / "02_tables" / "supplementary" / p.name)
    for p in sorted(PUB.rglob("*")):
        if p.is_file() and p.suffix in {".csv", ".json"}:
            put(p, stage / "03_results_data" / p.relative_to(PUB))
    for folder, files in REPORTS.items():
        for f in files:
            if (ROOT / f).exists():
                put(ROOT / f, stage / folder / Path(f).name)
    (stage / "05_references_and_ledgers" / "DATA_CITATIONS.md").write_text(data_citations(), encoding="utf-8")
    for item in CODE:
        p = ROOT / item
        files = [p] if p.is_file() else [q for q in p.rglob("*") if q.is_file()]
        for q in files:
            rel = q.relative_to(ROOT).as_posix()
            if rel in t and "__pycache__" not in rel:
                put(q, stage / "06_code_snapshot" / rel)
    (stage / "00_READ_ME_FIRST.md").write_text(guide(), encoding="utf-8")

    # safety: refuse anything private
    bad = [p for p in stage.rglob("*") if p.is_file() and (p.suffix.lower() in {".dta", ".zip", ".sav", ".parquet", ".pkl", ".env"}
                                                          or "raw" in p.relative_to(stage).parts or "interim" in p.relative_to(stage).parts)]
    if bad:
        raise SystemExit(f"refusing to package private files: {bad[:5]}")
    for p in stage.rglob("*.csv"):
        cols = {c.strip().lower() for c in pd.read_csv(p, nrows=0).columns}
        if cols & {"id", "hh", "hhid", "y4_hhid", "household_id", "village_id", "ea_id"}:
            raise SystemExit(f"identifier column in {p}")

    out_dir.mkdir(parents=True, exist_ok=True)
    zpath = out_dir / f"{name}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(stage.rglob("*")):
            if p.is_file():
                z.write(p, Path(name) / p.relative_to(stage))
    n = sum(1 for p in stage.rglob("*") if p.is_file())
    print(f"{zpath} ({n} files, {zpath.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
