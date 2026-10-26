# Validation and test results

Only statuses actually observed are reported. Local runs: Windows 11, Python 3.12.10, project `.venv` (pandas 3.1.0, numpy 2.5.4, matplotlib 3.11.2, streamlit 1.66.1, plotly 7.1.0, pytest 9.1.1, ruff 0.17.2). Exact versions are in `requirements-lock.txt` and `reports/execution_environment.json`.

## Summary

| Gate | Command | Result (27 Oct 2026, local) |
|---|---|---|
| Lint | `ruff check src tests scripts dashboard` | **All checks passed** |
| Unit, statistical, integration and dashboard tests | `pytest -v -p no:cacheprovider` | **134 passed, 0 failed, 0 skipped** (14.8 s) |
| Full pipeline | `python -m hunger_screening.cli all --no-download` | Completed; 22/22 integrity checks; 48/48 reproduction checks |
| Idempotency | two consecutive full runs, SHA-256 of all CSV outputs | **29/29 files byte-identical** (after moving wall-clock runtimes to `logs/`) |
| Release-safety audit | `python scripts/check_release_safety.py` | **PASS** (166 candidate files; no raw data, identifiers, secrets or files > 5 MB) |
| Local dashboard | `streamlit run dashboard/app.py` + `GET /_stcore/health` | `ok`; root page HTTP 200 |
| CI on GitHub | `.github/workflows/ci.yml` on commit `fcaa5d2` | **success**: run 40404757667; install, lint, safety audit and tests passed (Ubuntu, Python 3.12; real-data tests skip by design) |
| Clean-clone simulation of CI (no private data) | fresh `git clone` + ruff + safety + pytest | **131 passed, 3 skipped** (the 3 real-data tests), lint clean, audit PASS |

## Test matrix

| Group (file) | Tests | Expected assertion | Status |
|---|---:|---|---|
| Exact estimand (`test_estimand_exact.py`) | 11 | C(n−K, m)/C(n, m) equals enumeration of every m-subset for **every** binary history with n = 1…7; K = 0 excluded; K = n, m = n, m > n − K, empty denominator; synthetic 40-household panel equals direct subset averaging; frontier monotone; recomputable from the K distribution | PASS |
| Missing-history bounds (`test_missing_bounds_exhaustive.py`) | 43 | Exact equality with slot-level brute force over **all** completions (40 random instances, n = 3–4, every m); moving-denominator case; single imputations inside range; all-negative world; invalid input | PASS |
| Label-error solver (`test_misclassification_solver.py`) | 37 | Exact equality with brute force over all corrected histories under budgets 0–3 (25 instances × m ∈ {1, 2}); flip-cost formula equals minimum Hamming distance for all 81 histories (n = 4); α = 0 equals missing bounds; ranges nest as budget grows (10 seeds × 3 m × 5 budgets); budget shared, not per household; certificate F(λ*) = 0 | PASS |
| Cluster bootstrap (`test_bootstrap_and_clusters.py`) | 6 | Village totals reproduce point estimate; a replicate equals the stacked-household recomputation; only whole villages resampled; seeded reproducibility; zero-denominator draws counted; all-village option; jackknife finite | PASS |
| Temporal freeze (`test_temporal_freeze.py`) | 6 | `LeakageError` when test-year data reach selection; selection invariant to test data; rule immutable (`FrozenInstanceError`); earliest tie-break; evaluation and random benchmark exact; all candidates listed | PASS |
| Date/slot mapping (`test_date_slot_mapping.py`) | 3 | Month → two-month window mapping; duplicate rule keeps earliest record **whatever its HHS**; invalid HHS → missing; never-observed frame households retained | PASS |
| Schema and merges (`test_schema_and_merges.py`) | 3 | Synthetic panel structure; **real source** 22/22 integrity checks; real cohort counts 227/185 and 67/34, one duplicate slot, duplicate does not change HHS ≥ 2 | PASS (real-data tests skip in CI) |
| Pipeline regression (`test_pipeline_regression.py`) | 6 | Public frontier recomputable from public K distribution; CI contains point; α = 0 label bounds equal missing bounds exactly (rational strings); nesting; all certificates 0; budgets respected; complete-only α = 0 equals point; reproduction table all pass; real-data frontier equals public file | PASS |
| Data safety (`test_data_safety.py`) | 6 | `.gitignore` blocks raw/interim/private/.env/.venv; no identifier columns in public CSVs; data dictionary holds no values; checker catches planted .dta, ID column and token; release set clean; source hash matches | PASS |
| Dashboard smoke (`test_dashboard_smoke.py`) | 13 | Every one of 9 sections renders without exception (Streamlit `AppTest`); threshold and country controls work; overview states the limits; empty-data guard shows a warning instead of crashing; app references no raw or interim paths | PASS |

## Statistical gates

| Gate | Evidence |
|---|---|
| Exact formula vs exhaustive enumeration | `test_estimand_exact.py` (all histories n ≤ 7) |
| Conditional denominators / zero-denominator | `missed_fraction` returns `None`; bootstrap counts zero-denominator draws (0 observed in real data); bounds report zero-positive-world feasibility (never feasible at the budgets used) |
| Clustered resampling respects villages and strata | Per-country calls; whole-village test; 140 and 47 resampling units |
| Missing-bound optimiser vs brute force; moving denominator | 40 random instances + targeted case |
| Label-error solver: identity, nesting, feasibility, brute force | Tests above + `label_error_bounds.csv`: 192 optimisations, ≤ 4 Dinkelbach iterations, all certificates 0, budget used ≤ budget |
| No future leakage in timing | `LeakageError` test; selection uses only `attrs['year'] == 2020` matrices |
| Uncertainty objects kept distinct | Separate files, columns, figure encodings (whisker vs hatched range) and captions |

## Known gaps (honest)

- **Browser-level visual testing** of the dashboard (screenshots at phone and desktop widths) was not performed; no browser automation was available. Coverage is `AppTest` rendering plus an HTTP health check.
- **Type checking** (mypy/pyright) was not run; the code uses type hints, but no checker is pinned.
- **Fresh-machine reproduction** was simulated by a clean clone in a temporary folder and by GitHub CI (synthetic and aggregate tests only). The full pipeline from download was not rerun on a separate computer.
