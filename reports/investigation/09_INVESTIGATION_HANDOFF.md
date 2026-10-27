# Investigation handoff

*27 October 2026.*

## Where things are

| Item | Location / state |
|---|---|
| Branch | `investigation/strengthen-contribution`, created from `main` at `53064ad`. **Committed locally; not pushed, not merged** |
| World Bank archive (yours; checksum verified) | `data/raw/MWI_2020-2024_HFPS_v20_M_Stata.zip`, unchanged |
| Extracted World Bank microdata | `data/raw/worldbank_mwi_hfps_v20/extracted/` (gitignored; separate from `data/raw/extracted/`) |
| New code | `src/hunger_screening/{hfps,extensions,history_bounds,schedule_metrics,investigation_figures}.py`; command `python -m hunger_screening.cli investigation` |
| New configuration | `config/investigation.yaml` |
| New tests | `tests/test_history_bounds.py` (20), `tests/test_investigation.py` (12) |
| Aggregate outputs | `data/public_aggregates/investigation/` (20 CSV files + `hfps_summary.json`) |
| Figures | `figures/investigation/figI1`–`figI5` (PNG, SVG, PDF); previews in `figures/README/` |
| Reports | `reports/investigation/00`–`09` (this folder) |

## What changed in existing files

- **`scripts/check_release_safety.py`:** the World Bank household ID (`y4_hhid`) and the internal household column (`hh`), plus `case_id` and `ea_id`, are now blocked as identifier columns.
- **`tests/test_data_safety.py`:** the identifier check now also covers subfolders of `data/public_aggregates/`.
- **`src/hunger_screening/cli.py`:** new `investigation` step. `all` runs it only when the World Bank data are present.
- **Baseline analyses, outputs, reports, dashboard:** unchanged.

## What was tested

| Gate | Result (local, 27 Oct 2026) |
|---|---|
| `pytest` (full suite) | **166 passed**, 0 failed, 0 skipped (134 baseline + 32 new) |
| `ruff check src tests scripts dashboard` | All checks passed |
| Release-safety audit | PASS on 232 candidate files |
| Determinism | 20/20 investigation CSV files byte-identical across two runs |
| Exact solver | Equal to brute force on 180 random small instances, and to both baseline solvers where their targets overlap |
| Clean clone of the branch, no private data (CI simulation) | 162 passed, 4 skipped (the 3 Aggarwal and 1 World Bank real-data tests); lint and audit pass |
| CI on GitHub | **Not run**, because nothing was pushed |

## What remains

See `07_REQUIRED_WORK_BEFORE_SUBMISSION.md`. The decisions that need you:

1. Lock and run a multi-country test (needs your World Bank login).
2. Whether to request MIRA data.
3. The manuscript framing.
4. Author details and ethics.
5. Whether to push or merge this branch.

## Pushed or published?

**Nothing was pushed, merged, deployed, emailed or submitted.** Everything is local on the investigation branch. Pushing the branch would publish the new aggregate CSV files and figures, which the World Bank terms allow with a citation. Raw data, household IDs and household-level files remain local and gitignored.

## Update: locked multi-country test (27 Oct 2026)

- **Protocol:** `10_LOCKED_PROTOCOL_MULTICOUNTRY_HFPS.md`, locked in commit `8d33f4d` before any of the six archives existed locally.
- **Results:** `11_MULTICOUNTRY_RESULTS.md`, with outputs in `data/public_aggregates/multicountry/` and figure `figI6_multicountry_locked_test`.
- **Archives:** six, supplied by you, checksums recorded. Stored in `data/raw/multicountry/` (gitignored); originals remain in your Downloads folder.
- **Decisions:**
  - **H1, calendar rule: contradicted.** Burkina Faso 2020–21 +10.9 points (+6.9 to +14.7); Uganda 2020–21 +3.4 (−3.9 to +8.8).
  - **H3, second-contact rule: supported** (3 of 3 testable horizons).
  - **H2:** inconclusive.
  - **H4:** the rule does relatively better for rural households.
- **Deviations D1–D5** are documented in the results report. None changes a decision.
- **New code and tests:** `src/hunger_screening/multicountry.py`, `tests/test_multicountry.py`. Full suite: 172 passed; lint clean; release audit PASS; outputs byte-identical across two runs.
- **Credentials:** your World Bank password was held only in a temporary scratchpad file for the attempted login, then deleted. The scripted login failed because of the site's bot protection. The password is not in the repository. Please rotate it.
