"""Build the revised manuscript materials package (figures, tables, results, reports, ledgers, code, quality control).

1. Regenerates the manuscript tables (tables/manuscript/) and supplementary tables S5 to S18 (tables/investigation/)
   from data/public_aggregates only, and removes superseded table files.
2. Stages release-safe files (git-tracked or freshly generated aggregates; never data/raw, data/interim or logs)
   with new descriptive names, a guide (00_READ_ME_FIRST.md) and a quality-control folder (07_quality_control/).
3. Runs the package checks (hunger_screening.package_qc), writes MANIFEST.sha256 and a deterministic ZIP
   (sorted entries, fixed timestamps and permissions), so two builds from the same commit are byte-identical.

Usage: python scripts/build_manuscript_package.py [output_dir] [--evidence build/release_evidence.json]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hunger_screening import manuscript_tables, package_qc  # noqa: E402

PUB = ROOT / "data" / "public_aggregates"
TAB_MAIN = ROOT / "tables" / "manuscript"
TAB_SUPP = ROOT / "tables" / "investigation"
RELEASE = "revised-2026-10-27"
RELEASE_DATE = "27 October 2026"
NAME = "household_hunger_manuscript_package_REVISED_2026-10-27"
ZIP_TIME = (2026, 10, 27, 0, 0, 0)
TITLE = ("Missed Household Hunger Under Infrequent Screening: Timing, Uncertainty, and Evidence from African "
         "Longitudinal Surveys")
PREVIOUS = ROOT / "docs" / "previous_package_2026-10-27_manifest.txt"
SUPERSEDED = ["tables/investigation/table3_timing_evidence_classes", "tables/investigation/table4_locked_multicountry_test"]

FIGURES_MAIN = [
    ("figures/manuscript/fig1_cohort_flow", "Figure1_cohort_flow"),
    ("figures/manuscript/fig2_frontier", "Figure2_screening_frontier"),
    ("figures/supplementary/fig3_intermittency", "Figure3_intermittency"),
    ("figures/investigation/figI1_timing_across_datasets", "Figure4_missed_share_by_window_two_Malawi_panels"),
    ("figures/investigation/figI6_multicountry_locked_test", "Figure5_protocol_locked_multicountry_tests"),
    ("figures/investigation/figI3_decision_robustness", "Figure6_robustness_missing_histories_answer_error"),
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
TABLES_MAIN = [
    ("tables/table1_cohort_flow", "Table1_cohort_flow"),
    ("tables/manuscript/table2_frequency_frontier_and_identification", "Table2_frequency_frontier_and_identification"),
    ("tables/manuscript/table3_timing_two_malawi_panels", "Table3_timing_two_Malawi_panels"),
    ("tables/manuscript/table4_protocol_locked_multicountry_tests", "Table4_protocol_locked_multicountry_tests"),
]
# Trial tables kept as supplementary under new numbers (old numbering clashed with the main tables).
TABLES_TRIAL_SUPP = [
    ("tables/tableS1_attrition_balance", "TableS1_attrition_balance", None),
    ("tables/tableS2_ipw_vs_bounds", "TableS2_ipw_vs_bounds", None),
    ("tables/tableS3_bootstrap_stability", "TableS3_bootstrap_stability", None),
    ("tables/tableS4_reproduction", "TableS4_reproduction", None),
    ("tables/table2_main_frontier", "TableS19_frontier_complete_histories", "Table S19."),
    ("tables/table3_identification_bounds", "TableS20_identification_ranges_with_label_error", "Table S20."),
    ("tables/table4_timing_candidates", "TableS21_single_window_candidates_2020_2021", "Table S21."),
    ("tables/table5_timing_validation", "TableS22_out_of_year_validation_2021", "Table S22."),
]
REPORTS = {
    "04_methods_results_reports": [
        "reports/ALL_FINDINGS.md", "reports/ANALYSIS_HISTORY_AND_EVIDENCE_CLASSES.md", "reports/MANUSCRIPT_OUTLINE_FOOD_SECURITY.md",
        "reports/REVIEW_RESPONSE.md", "reports/FULL_SCIENTIFIC_ANALYSIS_REPORT.md", "reports/METHOD_SELECTION_AND_MODELS.md",
        "reports/DATA_QUALITY_AND_COHORT_FLOW.md", "reports/REPRODUCTION_AUDIT.md", "reports/VALIDATION_AND_TEST_RESULTS.md",
        "reports/LIMITATIONS_AND_THREATS.md", "reports/MANUSCRIPT_READINESS_VERDICT.md", "reports/NOVELTY_AND_CLOSEST_WORK.md",
        "reports/tables_figure_index.md"],
    "04_methods_results_reports/investigation": [f"reports/investigation/{n}" for n in (
        "README.md", "00_PROTOCOL_AND_EXPOSURE_LOG.md", "01_FULL_INVESTIGATION_REPORT.md", "02_DECISION_MEMO.md",
        "03_DATASET_INVENTORY_AND_ACCESS_LEDGER.md", "03_DATASET_INVENTORY_AND_ACCESS_LEDGER.csv", "04_CLOSEST_PRIOR_WORK.md",
        "05_NEGATIVE_FAILED_UNSTABLE_BLOCKED_TESTS.md", "06_MANUSCRIPT_OPTIONS.md", "07_REQUIRED_WORK_BEFORE_SUBMISSION.md",
        "08_LIMITATIONS_AND_UNRESOLVED_CLAIMS.md", "10_LOCKED_PROTOCOL_MULTICOUNTRY_HFPS.md", "11_MULTICOUNTRY_RESULTS.md")],
    "05_references_and_ledgers": ["reports/literature_ledger.csv", "reports/CLAIM_EVIDENCE_LEDGER.csv"],
}
CODE = ["src", "config", "tests", "scripts", "dashboard", "docs", "pyproject.toml", "requirements-lock.txt", "README.md",
        "CITATION.cff", "LICENSE", ".github/workflows/ci.yml"]

SOURCES = {  # package stem -> (generating code, aggregate inputs)
    "Figure1_cohort_flow": ("generate_figures.py", "cohort_flow.csv"),
    "Figure2_screening_frontier": ("generate_figures.py", "frontier.csv; missing_bounds.csv"),
    "Figure3_intermittency": ("generate_figures.py", "k_distribution.csv"),
    "Figure4_missed_share_by_window_two_Malawi_panels": ("investigation_figures.fig_timing_across", "review/window_paired_comparisons.csv"),
    "Figure5_protocol_locked_multicountry_tests": ("investigation_figures.fig_multicountry",
                                                   "multicountry/h1_calendar_rule.csv; multicountry/h3_second_contact.csv"),
    "Figure6_robustness_missing_histories_answer_error": (
        "investigation_figures.fig_robustness",
        "investigation/aggarwal_timing_robustness.csv; investigation/hfps_decision_robustness.csv; review/random_error_simulation.csv"),
    "Table1_cohort_flow": ("generate_tables.py", "cohort_flow.csv"),
    "Table2_frequency_frontier_and_identification": ("manuscript_tables.table2",
                                                     "frontier.csv; missing_bounds.csv; review/missing_bounds_second_scope.csv"),
    "Table3_timing_two_Malawi_panels": ("manuscript_tables.table3",
                                        "review/window_paired_comparisons.csv; timing_validation.csv; review/frozen_best_pair.csv; "
                                        "review/calendar_lean_season_sensitivity.csv; investigation/hfps_transfer_tests.csv"),
    "Table4_protocol_locked_multicountry_tests": ("manuscript_tables.table4", "multicountry/h1_calendar_rule.csv; multicountry/h3_second_contact.csv"),
}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def build_tables() -> None:
    manuscript_tables.build(PUB, TAB_MAIN, TAB_SUPP)
    manuscript_tables.supplementary(PUB, TAB_SUPP)
    for stem in SUPERSEDED:
        for ext in (".csv", ".md"):
            (ROOT / (stem + ext)).unlink(missing_ok=True)


# ------------------------------------------------------------------ documents
def mapping_rows(new_files: list[str]) -> pd.DataFrame:
    """Old-to-new path mapping, using the recorded manifest of the previous package."""
    old = {}
    for line in PREVIOUS.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            h, rel = line.split("  ", 1)
            old[rel] = h
    ren = {}
    old_main_fig = {"Figure4_timing_two_Malawi_panels": "Figure4_missed_share_by_window_two_Malawi_panels",
                    "Figure5_locked_five_country_test": "Figure5_protocol_locked_multicountry_tests",
                    "Figure6_decision_robustness": "Figure6_robustness_missing_histories_answer_error"}
    for o, n in old_main_fig.items():
        for e in (".png", ".pdf", ".svg"):
            ren[f"01_figures/main/{o}{e}"] = f"01_figures/main/{n}{e}"
    tab = {"02_tables/main/Table2_screening_frontier": "02_tables/main/Table2_frequency_frontier_and_identification",
           "02_tables/main/Table3_timing_evidence_classes": "02_tables/main/Table3_timing_two_Malawi_panels",
           "02_tables/main/Table4_locked_five_country_test": "02_tables/main/Table4_protocol_locked_multicountry_tests"}
    for s, n, _ in TABLES_TRIAL_SUPP:
        tab[f"02_tables/supplementary/{Path(s).name}"] = f"02_tables/supplementary/{n}"
    for s in ("S5_bounds_second_scope", "S6_single_window_positives", "S7_random_error_simulation", "S8_hhs_scoring_check",
              "S9_recall_overlap_discordance", "S10_worldbank_malawi_single_round", "S11_worldbank_transfer_tests", "S12_model_vs_rule",
              "S13_who_is_missed", "S14_multicountry_horizons"):
        tab[f"02_tables/supplementary/table{s}"] = f"02_tables/supplementary/Table{s}"
    for o, n in tab.items():
        for e in (".csv", ".md"):
            ren[o + e] = n + e
    new_set = set(new_files)
    rows = []
    for rel in sorted(old):
        new = ren.get(rel, rel)
        if new in new_set:
            change = "renamed" if new != rel else "same path"
            rows.append({"old_path": rel, "new_path": new, "change": change})
        else:
            rows.append({"old_path": rel, "new_path": "", "change": "removed"})
    mapped = {r["new_path"] for r in rows}
    for rel in sorted(new_set - mapped):
        rows.append({"old_path": "", "new_path": rel, "change": "added"})
    return pd.DataFrame(rows), old


def doc_changelog(m: pd.DataFrame, old: dict, stage: Path) -> str:
    def content(r):
        if r.change in ("same path", "renamed"):
            return "unchanged" if package_qc.sha256(stage / r.new_path) == old[r.old_path] else "revised"
        return ""
    m = m.copy()
    m["content"] = [content(r) for r in m.itertuples()]
    counts = m.groupby(["change", "content"]).size().reset_index(name="files")
    renamed = m[m.change == "renamed"]
    rn = "\n".join(f"| `{a}` | `{b}` | {c} |" for a, b, c in zip(renamed.old_path, renamed.new_path, renamed.content))
    added = m[(m.change == "added") & ~m.new_path.str.startswith(("06_code_snapshot/", "03_results_data/"))]
    removed = m[m.change == "removed"]
    return f"""# Changelog from the previous package

Previous package: `household_hunger_manuscript_package_2026-10-27.zip` (264 files; its file hashes are recorded in
`06_code_snapshot/docs/previous_package_2026-10-27_manifest.txt`). This package: `{NAME}.zip`.
The full old-to-new mapping, with content status for every file, is `old_to_new_filename_mapping.csv`.

## Scientific and editorial corrections

1. **Figure 6 redesigned.**
   - Panel A shows missing-history identification ranges; three of four comparisons exclude zero, and the World Bank item 8 range reaches zero.
   - Panel B shows adversarial tipping points.
   - Panel C shows the random-error simulations.
   - New title: "Robustness of screening-timing comparisons to missing histories and hypothetical answer error". The phrase "survive any pattern" was removed everywhere.
2. **Figure 4 reinterpreted.**
   - It shows every contact window, the best observed window, and paired comparisons against it.
   - No month is presented as uniquely best.
   - The July 2020 to June 2021 six-window result leads; the January to August 2021 four-window result is kept separate.
3. **"Five-country test" relabelled.** It is now the "protocol-locked multi-country investigation: five countries assessed, two with eligible primary calendar-test horizons". It is described as protocol-locked, not fully blind.
4. **Figure 5 redesigned.**
   - Panel A: H1 primary, in percentage points.
   - Panel B: H3 primary, per 100 re-contacted households.
   - Panel C: D2 sensitivity only.
5. **One rounding convention for every number** (`NUMERICAL_RECONCILIATION.md`). H3 values were corrected to 7.7, 10.4, +6.4 and 36.1.
6. **One canonical interval for the January to August 2021 Malawi contrast:** −46.9 to −29.2, from the primary pipeline. The separate bootstrap rerun is documented.
7. **New supplementary tables.**
   - Table S15: H2 and H4, including the untestable comparisons.
   - Table S16: second-contact comparisons at matched budgets.
   - Table S17: paired window comparisons.
   - Table S18: the exploratory September to February grouping.
8. **Table 1** shows integer counts.
9. **Table 2** has two panels: A, complete histories with bootstrap CIs; B, full-frame identification ranges labelled "not a CI".
10. **Table 3** now has a World Bank Malawi panel, leads with July 2020 to June 2021, includes the failed transfers, and separates the HHS from the FIES item.
11. **Table 4** has explicit eligibility rows and labels the sample-group panels.
12. **Trial tables renumbered** S19 to S22, because the old numbers 2 to 5 clashed with the main tables.
13. **Superseded tables removed:** the old Table 3 "timing evidence classes" and Table 4 "locked five-country test".
14. **Reports corrected.**
    - Model history (`METHOD_SELECTION_AND_MODELS.md` section 8) resolves the "no model fitted" inconsistency.
    - New `ANALYSIS_HISTORY_AND_EVIDENCE_CLASSES.md`.
    - New `MANUSCRIPT_OUTLINE_FOOD_SECURITY.md`.
    - Consolidated limitations.
    - Prior-work table: a FEWS NET row added, and how fully each paper was read.
15. **Ledgers.**
    - Claim-evidence ledger: 17 new claims, including the negative findings; new evidence-class and reference-period columns.
    - Literature ledger: the main finding for Aggarwal et al. 2022 corrected to "no evidence of declines in food security", and seven sources added.
16. **New title:** "{TITLE}".
17. **New quality control.** `07_quality_control/`, `MANIFEST.sha256`, and a deterministic ZIP build.

## File counts by change type

{counts.to_markdown(index=False)}

## Renamed files

| Old path | New path | Content |
|---|---|---|
{rn}

## Removed files

{chr(10).join(f"- `{p}`" for p in removed.old_path) or "- none"}

## Added files (outside the code snapshot and results data)

{chr(10).join(f"- `{p}`" for p in added.new_path)}
"""


def doc_reconciliation(cv: pd.DataFrame, stage: Path) -> str:
    docs = {p.relative_to(stage).as_posix(): package_qc._norm(p.read_text(encoding="utf-8")) for p in stage.rglob("*.md")
            if not p.relative_to(stage).as_posix().startswith(("06_code_snapshot/src", "06_code_snapshot/tests", "07_quality_control"))}
    rows = []
    for r in cv.itertuples():
        token = r.display.split(" (")[0].split(";")[0]
        n = sum(token in t for t in docs.values())
        rows.append(f"| {r.quantity} | `{r.display}` | {r.evidence_class} | `{r.source_file}` | {n} |")
    return f"""# Numerical reconciliation

## Rounding convention (applied to every manuscript-facing number)

- **Proportions** are shown as percentages with one decimal place, computed from the stored unrounded value.
- **Differences** are computed from the unrounded components, then rounded. They are never the difference of two rounded values, so a displayed difference can differ by 0.1 from the difference of the displayed components.
- **Confidence-interval limits** are rounded from their own unrounded values.
- **Rates per 100 re-contacted households** use one decimal place.
- **Counts.** Observed counts are integers. Expected (fractional) counts keep one decimal place and are labelled "expected".
- **Signs.** Differences carry an explicit sign in tables. Documents use the Unicode minus "−", which the checker treats as "-".

## Canonical values

Each value is computed by `hunger_screening.package_qc.canonical_values` directly from the aggregate files. The last column
counts the package documents (Markdown, excluding code and this folder) that contain the leading token. It is informational:
a zero means only that the documents phrase the number differently.

| Quantity | Canonical display | Evidence class | Source (data/public_aggregates/) | Documents containing it |
|---|---|---|---|---|
{chr(10).join(rows)}

## Discrepancies found and how they were resolved

| Item | Previous state | Resolution |
|---|---|---|
| H3 values in prose (Uganda 2020–21 random rate, difference, upper CI limits) | Some prose had 10.5, +6.5, 7.8 and 36.2 (rounded from rounded values) | Corrected to 10.4, +6.4, 7.7 and 36.1 from the unrounded file. The checker bans the old strings |
| January to August 2021 Malawi, January–February minus random | Two bootstrap runs of the same estimand: −46.9 to −29.2 (primary pipeline, `timing_validation.csv`) and −46.5 to −29.6 (review rerun, `calendar_lean_season_sensitivity.csv`, `window_paired_comparisons.csv`) | Canonical: −46.9 to −29.2, used in Table 3, the README and the reports. The rerun interval appears only in Table S17 and a `REVIEW_RESPONSE.md` footnote, both labelled. Point estimates are identical (−38.2) |
| Liberia 2021: frozen March–April (−5.7, −26.9 to +14.1) vs calendar July–August (−5.7, −26.3 to +11.8) | Looked like a conflict | Not a conflict: different windows that happen to have the same missed share (54.5%) |
| Table 1 counts | Shown with decimals (for example 297.0) | Integers |
| H3 "supported" | Read as "every horizon significant" | Now "supported directionally (3 of 3 positive; one interval includes zero)" |
| Missing-history robustness | "Survive any pattern of missing interviews" | "Identification range excludes zero in 3 of 4 lead comparisons; World Bank item 8 reaches zero" |

## Automated checks

`qc_checks.csv` lists every check of this build: main-table cells against sources; integer counts; banned wording and known
wrong roundings; credentials and local paths; identifier columns; figure validity; and the manifest.
"""


def doc_crosswalk() -> str:
    return """# Protocol-to-results crosswalk (protocol-locked multi-country investigation)

**Protocol.** `04_methods_results_reports/investigation/10_LOCKED_PROTOCOL_MULTICOUNTRY_HFPS.md`, committed in `8d33f4d` on 27 October 2026 at 09:31 EAT.
- Protocol SHA-256: `23afabbe12a849533c4614aa48eea3f34406c36f329c3219c2c8bb5a2095ba6d`.
- Parameters SHA-256: `a8ba13f0ab44e37eb3abec6d843c1b86c7967993f2a4211d5e417400364f7324`.

**Status.** Protocol-locked before access to the household-level and item-level outcomes, with prior exposure to some published
aggregate results. Not fully blind.

**Results:** `11_MULTICOUNTRY_RESULTS.md`, Table 4, Table S15 and Figure 5.

| Element | Prespecified in protocol | What was done | Result | Where |
|---|---|---|---|---|
| Countries | Burkina Faso, Ethiopia, Nigeria (2020 and 2021 panels), Tanzania, Uganda | All five assessed | Two (Burkina Faso, Uganda) had eligible primary H1 horizons. Ethiopia excluded from H1 by protocol. Nigeria and Tanzania had no usable horizon | Table 4, Table S14 |
| Outcome | FIES item 7, "hungry but did not eat", 30-day recall; HHS-type reference | As specified; item mapped by FIES position (D1) | — | `item_mapping_and_sources.csv` |
| Usability rule | At least 3 candidate rounds and at least 100 complete households per horizon | Applied | Five primary horizons usable across countries (Table S14) | Table S14 |
| H1 calendar rule (primary, confirmatory) | Supported if at least 2/3 below zero and none entirely above; contradicted if more than half above zero or at least two entirely above | Two eligible primary horizons | **Contradicted**: 2 of 2 above zero. Burkina Faso +10.9 (+6.9 to +14.7) pp; Uganda +3.4 (−3.9 to +8.8), individually inconclusive | Table 4, Fig. 5A |
| H2 data-driven transfer (secondary) | Every ordered pair of usable horizons in a panel | One testable pair (Uganda 2020–21 → 2022–23) | **Inconclusive**: −3.3 (−9.8 to +3.7). The pandemic-onset comparison is untestable | Table S15 |
| H3 second-contact rule (secondary) | Supported if positive in at least 2/3 of usable horizons | Three eligible primary horizons; Ethiopia untestable (round 1 asked only items 6–8) | **Supported directionally**: 3 of 3 positive (+6.2, +6.4, +1.5 per 100). The Uganda 2022–23 interval includes zero | Table 4, Fig. 5B |
| H4 rural vs urban (exploratory, single contrast) | Paired bootstrap of rural minus urban (rule − random) | Burkina Faso and Uganda 2020–21 | Direction as hypothesised. Burkina Faso −10.8 (−19.2 to −2.6); Uganda −6.2 (−13.5 to +2.4). The rule is less harmful for rural households, not beneficial | Table S15 |
| Inference | Percentile bootstrap, 2,000 draws, seed 20261028, finest cluster; unweighted primary analysis; exact missing-data ranges | As specified | H1 primary ranges both include zero | `11_MULTICOUNTRY_RESULTS.md` |
| Multiplicity | No correction; H1 the only confirmatory hypothesis | As specified | — | — |

## Deviations

None of the deviations changed a decision.

| # | Deviation | Effect on decisions |
|---|---|---|
| D1 | Items identified by FIES position, not only by English label | None |
| D2 | Split-sample groups re-formed as separate panels | Reported only as sensitivity (Table 4 lower block, Fig. 5C). Decisions unchanged |
| D3 | Tanzania round 9 file truncated in the official release | Tanzania unusable either way |
| D4 | Interview-date sources differ by country | Negligible (round medians) |
| D5 | Pandemic-onset flag coding corrected before results were read | Only Ethiopia 2019–20 flagged; no H2 pair affected |

## Not part of the locked test

- The post hoc explanation of the H1 failure: reported hunger declined round by round in 2020–21.
- Every Malawi analysis.
"""


def doc_source_map(stage: Path) -> tuple[str, pd.DataFrame]:
    rows = []
    for src, new in FIGURES_MAIN + FIGURES_SUPP:
        code, data = SOURCES.get(new, ("generate_figures.py or investigation_figures.py", "see 03_results_data"))
        rows.append({"package_item": new, "kind": "main figure" if (src, new) in FIGURES_MAIN else "supplementary figure",
                     "repository_file": src + ".{png,pdf,svg}", "generating_code": f"src/hunger_screening/{code}", "aggregate_inputs": data})
    for src, new in TABLES_MAIN:
        code, data = SOURCES[new]
        rows.append({"package_item": new, "kind": "main table", "repository_file": src + ".{csv,md}",
                     "generating_code": f"src/hunger_screening/{code}", "aggregate_inputs": data})
    for src, new, _ in TABLES_TRIAL_SUPP:
        rows.append({"package_item": new, "kind": "supplementary table", "repository_file": src + ".{csv,md}",
                     "generating_code": "src/hunger_screening/generate_tables.py", "aggregate_inputs": "trial aggregates (see table note)"})
    for p in sorted((stage / "02_tables" / "supplementary").glob("TableS*.md")):
        if any(p.stem == n for _, n, _ in TABLES_TRIAL_SUPP):
            continue
        rows.append({"package_item": p.stem, "kind": "supplementary table", "repository_file": f"tables/investigation/{p.stem[0].lower() + p.stem[1:]}.{{csv,md}}",
                     "generating_code": "src/hunger_screening/manuscript_tables.py", "aggregate_inputs": "review/, investigation/, multicountry/"})
    df = pd.DataFrame(rows)
    return "# Figure and table source map\n\nEvery figure and table in this package, the repository file it was copied from, the code that generates it, and its aggregate inputs (under `data/public_aggregates/`, copied to `03_results_data/`). A CSV version is `figure_table_source_map.csv`.\n\n" + df.to_markdown(index=False) + "\n", df


def doc_unresolved() -> str:
    return """# Unresolved submission requirements

These items cannot be resolved from the data or code. They do not block drafting the manuscript, but they block submission.

| # | Requirement | Why it matters | Who | Status |
|---|---|---|---|---|
| 1 | **Confirmation of the HHS questionnaire and scoring by the original authors** (Aggarwal et al. 2022) | The do-file and a table caption label the first HHS item "skipped a meal". The score matches the standard "no food of any kind" item in 99.1% of records, but the phone questionnaire and the frequency answers are not public | Corresponding author contacts the source authors | Open |
| 2 | **Independent statistical review and an institutional ethics decision** | The exact-bound solvers, bootstrap choices (district clusters for the World Bank survey are approximate) and inference wording need an independent statistician. Secondary analysis of public de-identified data still needs an institutional determination (exemption or approval) | Study team; institutional review board | Open |
| 3 | **Co-author details and affiliations** | Co-researchers are to be added (also in `CITATION.cff`), with accurate affiliations, contributions (CRediT), competing interests, funding, and any Ministry of Health Uganda permission to publish | Omoding Isaac | Open |

Further items needed for the journal (*Food Security*), from `MANUSCRIPT_OUTLINE_FOOD_SECURITY.md`:
- at least four suggested reviewers;
- author bios and photos;
- the AI-use disclosure;
- the exact catalog citation text for each World Bank dataset;
- a final check of the journal's current guidelines.
"""


def doc_test_report(ev: dict, sha: str, clean: bool, qc: pd.DataFrame) -> str:
    def g(*k, default="not recorded"):
        d = ev
        for x in k:
            if not isinstance(d, dict) or x not in d:
                return default
            d = d[x]
        return d
    nfail = int((qc.status == "FAIL").sum())
    return f"""# Test and release report

| Item | Result |
|---|---|
| Release | `{RELEASE}` ({RELEASE_DATE}) |
| Commit packaged | `{sha}` (working tree clean at build: {"yes" if clean else "NO"}) |
| Lint (`ruff check src tests scripts dashboard`) | {g("ruff")} |
| Tests (`pytest`), local | {g("pytest", "summary")} |
| Release-safety audit (`scripts/check_release_safety.py`) | {g("release_safety")} |
| Package QC (`qc_checks.csv`) | {len(qc) - nfail} of {len(qc)} checks pass{"" if nfail == 0 else f"; {nfail} FAIL"} |
| GitHub Actions CI for `{sha[:7]}` | {g("ci", "summary")} |
| CI run | {g("ci", "url")} |

## Determinism and archive integrity

A file cannot record a hash of the archive that contains it, so the double-build comparison and the
extract-and-verify results are recorded outside the ZIP:
- in `{NAME}.verification.txt`, next to the ZIP;
- in the hand-off message.

Within the package, `MANIFEST.sha256` lists the SHA-256 of every file. The `manifest matches files` row of
`qc_checks.csv` confirms it at build time.

## Notes

{g("notes", default="None.")}
"""


def doc_audit(qc: pd.DataFrame, hits: list, sha: str) -> str:
    fails = qc[qc.status == "FAIL"]
    by = qc.groupby("check").status.apply(lambda s: f"{(s == 'PASS').sum()} of {len(s)} pass").reset_index()
    return f"""# Final package audit

**Audited:** `{NAME}`, built from commit `{sha}`. The automated checks are in `hunger_screening/package_qc.py` and were
run on the staged package. The manual review items below were checked by reading the regenerated outputs.

## Automated checks

{by.to_markdown(index=False)}

**Overall:** {"ALL PASS" if fails.empty else f"{len(fails)} FAIL (listed below)"}.

{"" if fails.empty else fails.to_markdown(index=False)}

## Manual review against the revision instruction

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Figure 6: missingness, adversarial and random error shown separately; "3 of 4 exclude zero"; new title | Done | Figure 6; panels A, B and C |
| 2 | Figure 4: all windows, the best observed window and paired comparisons; no uniquely best month; July 2020 to June 2021 leads; the four-window result separate | Done | Figure 4; Table 3; Table S17 |
| 3 | Relabel to "protocol-locked multi-country investigation" with eligibility; not-fully-blind wording; old-to-new names | Done | Table 4 title; Figure 5; `old_to_new_filename_mapping.csv`; banned-wording check |
| 4 | Figure 5: A H1 (pp), B H3 (per 100), C D2 only | Done | Figure 5 |
| 5 | One rounding convention and an automated checker | Done | `NUMERICAL_RECONCILIATION.md`; `qc_checks.csv` |
| 6 | H2/H4 table with eligibility, including untestable comparisons | Done | Table S15 |
| 7 | Table 1 integer counts | Done | Integer-count check |
| 8 | Table 2: panel A CIs; panel B ranges labelled "not a CI" | Done | Table 2 checks |
| 9 | Table 3: World Bank panel; July 2020 to June 2021 lead (133; 38.3% vs 59.3%; −20.9); failed transfers; HHS vs FIES explicit | Done | Table 3 checks |
| 10 | Second contact: matched budgets; the H3 interval that includes zero; no cost-effectiveness claim; which Aggarwal analyses are possible | Done | Table S16; Table 4; `ALL_FINDINGS.md` |
| 11 | Model history consistent | Done | `METHOD_SELECTION_AND_MODELS.md` section 8 |
| 12 | Analysis history and evidence classes | Done | `ANALYSIS_HISTORY_AND_EVIDENCE_CLASSES.md` |
| 13 | Figure and table set reassessed | Done | Six main figures and four main tables; superseded tables removed; trial tables renumbered S19 to S22 |
| 14 | Title | Done | `00_READ_ME_FIRST.md`; outline |
| 15 | Food Security outline | Done | `MANUSCRIPT_OUTLINE_FOOD_SECURITY.md` |
| 16 | Prior work updated | Done | `04_CLOSEST_PRIOR_WORK.md` (FEWS NET row; how fully each paper was read) |
| 17 | Ledgers updated | Done | Claim-evidence ledger (34 claims); literature ledger (21 sources; Aggarwal et al. 2022 finding corrected); `DATA_CITATIONS.md` |
| 18 | Limitations and the three unresolved requirements | Done | `LIMITATIONS_AND_THREATS.md`; `UNRESOLVED_SUBMISSION_REQUIREMENTS.md` |
| 19 | Automated QA tests | Done | `tests/test_manuscript_package.py` |
| 20 | Quality-control folder | Done | This folder |
| 21 | Read-me covering the required elements | Done | `00_READ_ME_FIRST.md` |
| 22 | Deterministic build, manifest, integrity | Done | `MANIFEST.sha256`; verification file next to the ZIP |
| 23 | Commit, push and CI | See `TEST_AND_RELEASE_REPORT.md` | — |

## Residual risks found by the audit (not fixed by this package)

- **Some historical reports keep their original framing**, with a revision banner. Where they conflict with `ALL_FINDINGS.md`, `ALL_FINDINGS.md` and this package's main tables take precedence.
- **The locked protocol file still uses the original term "five-country"** in places. It is deliberately unchanged, because altering a locked protocol is not allowed.
- **Bootstrap intervals from separate runs of the same estimand can differ by a few tenths of a point.** One canonical value is designated in `NUMERICAL_RECONCILIATION.md`.
"""


def guide(sha: str, clean: bool, n_files: int, qc: pd.DataFrame) -> str:
    nfail = int((qc.status == "FAIL").sum())
    return f"""# Manuscript materials package (revised)

| | |
|---|---|
| **Release** | `{RELEASE}`, built {RELEASE_DATE} |
| **Source** | https://github.com/Isaac25-lgtm/household-hunger-screening, branch `main`, commit `{sha}` (working tree clean: {"yes" if clean else "no"}) |
| **Author** | Omoding Isaac, MSc Data Science and Analytics; Ministry of Health, Uganda; omodingisaac111@gmail.com. Co-researchers to be added |
| **Audit status** | {"All" if nfail == 0 else f"{len(qc) - nfail} of"} {len(qc)} automated checks pass (`07_quality_control/qc_checks.csv`); manual review in `07_quality_control/FINAL_PACKAGE_AUDIT.md` |
| **Contents** | {n_files} files including this guide; integrity list in `MANIFEST.sha256` |
| **Excluded** | No microdata, household identifiers, credentials or local logs |

## 1. Proposed title

**{TITLE}**

Running head: *Missed household hunger under infrequent screening*

## 2. What this package is for

The materials for drafting the manuscript elsewhere. **It is not the manuscript.** The writing map is
`04_methods_results_reports/MANUSCRIPT_OUTLINE_FOOD_SECURITY.md`, for the journal *Food Security*.

## 3. Folder map

| Folder | Contents |
|---|---|
| `01_figures/main` | Main figures 1 to 6 (PNG 300 dpi, PDF, SVG) |
| `01_figures/supplementary` | Figures S1 to S12 |
| `02_tables/main` | Main tables 1 to 4 (CSV and Markdown) |
| `02_tables/supplementary` | Tables S1 to S22 |
| `03_results_data` | Every aggregate result file behind the figures and tables |
| `04_methods_results_reports` | Findings, analysis history, outline, methods and model history, review response, audits, limitations, and the investigation reports (including the locked protocol and its results) |
| `05_references_and_ledgers` | Literature ledger, claim-evidence ledger, `DATA_CITATIONS.md` |
| `06_code_snapshot` | Analysis code, configuration, tests and scripts at the commit above |
| `07_quality_control` | Audit, numerical reconciliation, protocol crosswalk, source map, unresolved requirements, changelog, test and release report, CSVs |

## 4. Main figures and tables

| Item | Content |
|---|---|
| Figure 1 / Table 1 | Cohort flow (integer counts) |
| Figure 2 / Table 2 | Frequency frontier. Table 2 panel A: complete histories with bootstrap CIs. Panel B: full-frame identification ranges (not CIs) |
| Figure 3 | Intermittency of reported hunger |
| Figure 4 / Table 3 | Missed share by contact window in two Malawi panels; best observed window and paired comparisons; July 2020 to June 2021 leads |
| Figure 5 / Table 4 | Protocol-locked multi-country tests: H1 primary (pp), H3 primary (per 100 re-contacted), D2 sensitivity |
| Figure 6 | Robustness to missing histories (3 of 4 exclude zero), adversarial tipping points and random error |

The full list, with sources, is `07_quality_control/FIGURE_TABLE_SOURCE_MAP.md`. Old-to-new file names:
`07_quality_control/old_to_new_filename_mapping.csv`.

## 5. Headline results by evidence class

- **Frequency (exact design quantity).** With one random screen of six, 55.1% of Malawi reference-positive households are missed (95% CI 51.6 to 58.7%); Liberia 69.6%. Over the full Malawi frame the range is 50.8 to 59.3%, an identification range, not a CI.
- **Timing (out-of-time, not blind).**
  - July 2020 to June 2021, six windows, 133 reference positives: January–February missed 38.3% against 59.3% at random (−20.9 pp; −27.5 to −13.6).
  - The best observed window was November–December (37.6%). January–February and September–October cannot be separated from it.
  - January to August 2021, four windows, 102 reference positives: 21.6% against 59.8%. This uses a different reference, so it is not comparable.
- **World Bank Malawi (FIES item, not the HHS).** Early-year rounds did better than random in 2021. A round chosen on 2020 failed in 2021.
- **Protocol-locked multi-country investigation.** Five countries assessed; two had eligible primary calendar-test horizons.
  - H1 calendar rule: contradicted.
  - H2: inconclusive (one pair).
  - H3 second-contact rule: supported directionally (3 of 3 positive; Uganda 2022–23 interval includes zero).
  - H4: rural direction.
- **Robustness (post hoc sensitivity).**
  - 3 of 4 timing comparisons have missing-history identification ranges that exclude zero.
  - Worst-case answer error of 0.5 to 2.5% can erase each one.
  - Random error at hypothetical rates up to 20% does not.

## 6. Evidence classes and protocol wording

Use `04_methods_results_reports/ANALYSIS_HISTORY_AND_EVIDENCE_CLASSES.md` for the class of every finding. Describe the
multi-country investigation as: "Protocol-locked before access to the household-level and item-level outcomes, with
prior exposure to some published aggregate results." **No analysis is fully blind or prospectively registered.**
The protocol crosswalk is `07_quality_control/PROTOCOL_TO_RESULTS_CROSSWALK.md`.

## 7. Rounding convention

One decimal place, rounded from the unrounded stored values. Differences are computed before rounding. Integer
observed counts; expected counts are labelled. Details and the canonical values are in
`07_quality_control/NUMERICAL_RECONCILIATION.md`.

## 8. Measurement

- **HHS (trial).** Standard FANTA scoring, built from the "no food of any kind" item. "Skipped a meal" in the do-file is a mislabel.
- **World Bank.** FIES item 7 ("hungry but did not eat") and item 8 ("whole day without eating").
- **The two are different instruments and are never pooled.**

## 9. Rules to keep when writing

- Keep three uncertainty objects separate:
  - bootstrap confidence intervals;
  - identification ranges, which are not CIs;
  - hypothetical answer-error scenarios.
- Do not claim:
  - a uniquely best month, or an optimal schedule;
  - national or annual prevalence;
  - causal effects of interviewing less;
  - cost-effectiveness;
  - that the World Bank items are the HHS;
  - that H1 failed "across five countries";
  - that every H3 comparison was individually significant;
  - being first.
- Report discordance between overlapping recall periods as discordance, not as an error rate.
- Yield per 100 re-contacted households is contact efficiency, not cost.

## 10. Data and code availability

- **Data.** Aggarwal et al. (2022) supplement (CC BY 4.0); World Bank Microdata Library LSMS high-frequency phone surveys (`05_references_and_ledgers/DATA_CITATIONS.md`). Microdata are not redistributed.
- **Code.** The repository at the commit above (`06_code_snapshot`).

## 11. Reproducing the package

`python scripts/build_manuscript_package.py` from a clean checkout of the commit above. It regenerates the tables, runs the
checks and builds the deterministic ZIP. Two builds from the same commit are byte-identical.

## 12. Limitations

Consolidated in `04_methods_results_reports/LIMITATIONS_AND_THREATS.md`, final section.

## 13. Unresolved before submission

The three items below are in `07_quality_control/UNRESOLVED_SUBMISSION_REQUIREMENTS.md`:
1. Confirmation of the HHS questionnaire and scoring by the original authors.
2. Independent statistical review and an institutional ethics decision.
3. Co-author details and affiliations.

## 14. Readiness

- **For manuscript drafting:** ready. Every figure, table and number is regenerated, reconciled and checked.
- **For journal submission:** **not ready** until the three items above are resolved.
"""


def data_citations() -> str:
    src = (ROOT / "reports" / "investigation" / "README.md").read_text(encoding="utf-8")
    part = src[src.index("## Data sources and citations"):]
    return ("# Data citations\n\n" + part.split("\n", 1)[1] +
            "\n## Trial data\n\nAggarwal S, Jeong D, Kumar N, Park DS, Robinson J, Spearot A (2022). COVID-19 market disruptions and food "
            "security: Evidence from households in rural Liberia and Malawi. *PLOS ONE* 17(8): e0271488. "
            "https://doi.org/10.1371/journal.pone.0271488 (replication files in the article's supporting information, CC BY 4.0).\n")


# ------------------------------------------------------------------ build
def deterministic_zip(stage: Path, zpath: Path) -> None:
    files = sorted(p for p in stage.rglob("*") if p.is_file())
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files:
            info = zipfile.ZipInfo(f"{NAME}/{p.relative_to(stage).as_posix()}", date_time=ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            info.create_system = 3
            z.writestr(info, p.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", nargs="?", default=str(Path.home() / "Downloads"))
    ap.add_argument("--evidence", default=str(ROOT / "build" / "release_evidence.json"))
    ap.add_argument("--stage", default=str(ROOT / "build" / NAME))
    args = ap.parse_args()
    build_tables()
    tracked = set(git("ls-files").splitlines())
    sha = git("rev-parse", "HEAD")
    clean = git("status", "--porcelain") == ""
    ev = json.loads(Path(args.evidence).read_text(encoding="utf-8")) if Path(args.evidence).exists() else {}
    stage = Path(args.stage)
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    def put(src: Path, dest: Path, text: str | None = None) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if text is None:
            dest.write_bytes(src.read_bytes())
        else:
            dest.write_text(text, encoding="utf-8")

    for group, sub in ((FIGURES_MAIN, "main"), (FIGURES_SUPP, "supplementary")):
        for src, new in group:
            for ext in (".png", ".pdf", ".svg"):
                if (ROOT / (src + ext)).exists():
                    put(ROOT / (src + ext), stage / "01_figures" / sub / (new + ext))
    for src, new in TABLES_MAIN:
        for ext in (".csv", ".md"):
            put(ROOT / (src + ext), stage / "02_tables" / "main" / (new + ext))
    for src, new, label in TABLES_TRIAL_SUPP:
        for ext in (".csv", ".md"):
            p = ROOT / (src + ext)
            text = None
            if ext == ".md" and label:
                t = p.read_text(encoding="utf-8")
                old = t.split(".", 1)[0]  # "**Table N"
                text = "**" + label[:-1] + t[len(old):]
            put(p, stage / "02_tables" / "supplementary" / (new + ext), text)
    for p in sorted(TAB_SUPP.glob("table*.*")):
        put(p, stage / "02_tables" / "supplementary" / ("T" + p.name[1:]))
    for p in sorted(PUB.rglob("*")):
        if p.is_file() and p.suffix in {".csv", ".json"}:
            put(p, stage / "03_results_data" / p.relative_to(PUB))
    for folder, files in REPORTS.items():
        for f in files:
            put(ROOT / f, stage / folder / Path(f).name)
    put(None, stage / "05_references_and_ledgers" / "DATA_CITATIONS.md", data_citations())
    for item in CODE:
        p = ROOT / item
        for q in ([p] if p.is_file() else sorted(q for q in p.rglob("*") if q.is_file())):
            rel = q.relative_to(ROOT).as_posix()
            if rel in tracked and "__pycache__" not in rel:
                put(q, stage / "06_code_snapshot" / rel)

    qc_dir = stage / "07_quality_control"
    qc_dir.mkdir()
    cv = package_qc.canonical_values(PUB)
    for name in ("PROTOCOL_TO_RESULTS_CROSSWALK.md", "UNRESOLVED_SUBMISSION_REQUIREMENTS.md"):
        put(None, qc_dir / name, doc_crosswalk() if name.startswith("PROTOCOL") else doc_unresolved())
    sm_md, sm = doc_source_map(stage)
    put(None, qc_dir / "FIGURE_TABLE_SOURCE_MAP.md", sm_md)
    sm.to_csv(qc_dir / "figure_table_source_map.csv", index=False)
    cv.to_csv(qc_dir / "numerical_reconciliation.csv", index=False)
    put(None, qc_dir / "NUMERICAL_RECONCILIATION.md", doc_reconciliation(cv, stage))
    # placeholders so the read-me, mapping and manifest see the final file set; filled below
    for name in ("00_READ_ME_FIRST.md", "07_quality_control/CHANGELOG_FROM_PREVIOUS_PACKAGE.md",
                 "07_quality_control/old_to_new_filename_mapping.csv", "07_quality_control/qc_checks.csv",
                 "07_quality_control/FINAL_PACKAGE_AUDIT.md", "07_quality_control/TEST_AND_RELEASE_REPORT.md"):
        put(None, stage / name, "")
    files = sorted(p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()) + ["MANIFEST.sha256"]
    m, old = mapping_rows(files)
    m.to_csv(qc_dir / "old_to_new_filename_mapping.csv", index=False)
    put(None, qc_dir / "CHANGELOG_FROM_PREVIOUS_PACKAGE.md", doc_changelog(m, old, stage))

    qc = package_qc.run_all(stage, PUB, with_manifest=False)
    _, hits = package_qc.check_text(stage)
    qc.to_csv(qc_dir / "qc_checks.csv", index=False)
    put(None, qc_dir / "FINAL_PACKAGE_AUDIT.md", doc_audit(qc, hits, sha))
    put(None, qc_dir / "TEST_AND_RELEASE_REPORT.md", doc_test_report(ev, sha, clean, qc))
    put(None, stage / "00_READ_ME_FIRST.md", guide(sha, clean, len(files), qc))
    # the guide and reports were written after the text scan: re-scan the final text
    final_text, _ = package_qc.check_text(stage)
    if final_text[0]["status"] != "PASS" or (qc.status == "FAIL").any():
        print(qc[qc.status == "FAIL"].to_string() if (qc.status == "FAIL").any() else final_text[0]["detail"])
        raise SystemExit("package QC failed; nothing written to the output folder")

    lines = [f"# SHA-256 of every file in {NAME} except this manifest. Commit {sha}."]
    lines += [f"{package_qc.sha256(stage / r)}  {r}" for r in files if r != "MANIFEST.sha256"]
    (stage / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    man = package_qc.check_manifest(stage)[0]
    if man["status"] != "PASS":
        raise SystemExit(f"manifest check failed: {man['detail']}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    zpath = out_dir / f"{NAME}.zip"
    deterministic_zip(stage, zpath)
    n = sum(1 for p in stage.rglob("*") if p.is_file())
    print(f"{zpath} ({n} files, {zpath.stat().st_size} bytes, sha256 {package_qc.sha256(zpath)}); commit {sha}; clean {clean}; "
          f"QC {len(qc) - int((qc.status == 'FAIL').sum())}/{len(qc)} pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
