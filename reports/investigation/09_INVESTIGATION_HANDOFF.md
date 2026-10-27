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
