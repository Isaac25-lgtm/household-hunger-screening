# Execution log

Times are local (EAT, UTC+3) on 26–27 Oct 2026. Commands are abbreviated; full outputs are in local `logs/` (gitignored).

| Time | Phase | Action / command | Outcome | Decision / open issue |
|---|---|---|---|---|
| 23:25 | 1 Source | Inventoried parent folder `PUBLISHING` | Only an unrelated `Remittance AI` project and an empty `household-hunger-screening` folder. No `.dta`, `.zip`, earlier dossier, report, ledger or evidence ZIP found | All evidence regenerated from the publisher |
| 23:26 | 1 Source | `git ls-remote` on target repo | Repo exists and is empty (no refs) | No history to reconcile |
| 23:27 | 1 Source | `curl` PLOS S1 Data | HTTP 200; 9,098,158 bytes; SHA-256 `de2ae59d…66bb` | **Matches** earlier provenance exactly |
| 23:28 | 1 Source | Extracted archive to `data/raw/extracted`; read `readme.docx` and `replication_dofile.do` | Do-file confirms "roughly half called each calendar month" (alternating schedule) | Two-month designated windows adopted |
| 23:29 | Env | `python -m venv .venv` + pip install | First attempt failed (Windows file lock on scipy wheel); retried without scipy (not needed) | Installed pandas 3.1.0 etc.; lockfile frozen |
| 23:35 | 2 Data | Variable inventory and integrity audit (system Python) | 4,744 / 503 / 483 / 252 confirmed; HHS items consistent; frequency items absent | Use source HHS score |
| 23:38 | 3 Core | Prototype frontier | 55.1/31.9/18.2 and 69.6/47.5/30.7 reproduced | Proceed to package |
| 23:40–00:05 | 3–5 | Wrote package modules; ran `pipeline.run()` | 22/22 integrity, 48/48 reproduction checks pass in ~20 s | — |
| 23:52 | 6 Lit | Crossref (9 DOIs), OpenAlex citing works (46), web search | Found **Zhu et al. 2026 (*Food Security*)**, the closest prior work; full text read | Not a duplicate; novelty is modest; reframe needed |
| 00:00 | 4 Tests | Brute-force tests for bounds and solver | 91 passed | — |
| 00:05 | 7 Figures | dataviz palette validated (blue/orange pass CVD in light and dark); rendered 12 figures; visual inspection | Fixed label collisions, legends and table column bugs | — |
| 00:10 | Env | Full pipeline under venv (pandas 3.1) | Works; outputs not byte-identical across runs because solver runtimes were stored | Moved runtimes to `logs/`; now 29/29 CSVs identical |
| 00:14 | 8 Dashboard | Streamlit app; `AppTest` smoke tests | 1 failure: `st.cache_data` keyed on file name leaked data between app instances | Fixed (cache keyed on full path); 13/13 pass |
| 00:15 | 8 Dashboard | Local launch + health check | `ok`, HTTP 200 | Server bound to all interfaces by default → launch script pins `localhost` |
| 00:20 | 9 Safety | Release audit | Flagged `id` column in literature ledger (false positive) and found that `logs/dashboard_local.log` records the machine's public IP | Renamed column to `ref_id`; **all of `logs/` gitignored** |
| 00:25 | 9 Tests | `ruff` + `pytest` in venv | Lint clean; **134 passed, 0 skipped** | — |
| 00:27 | 9 Git | 6 scoped commits; clean-clone test (131 passed, 3 skipped); `git push -u origin main` (no force) | Remote `main` = `fcaa5d2`; README, figures, reports and workflow verified via the GitHub API | — |
| 00:30 | 9 CI | GitHub Actions run 40404757667 | **success** (install, lint, safety audit, tests) | Dashboard not publicly deployed: Streamlit Cloud needs the owner's interactive sign-in |

## Decisions recorded

- **Duplicate rule:** earliest dated record per household-window (outcome-blind); valid HHS preferred over missing (uses missingness only).
- **Bootstrap units:** villages with ≥ 1 complete household (primary); all frame villages as a sensitivity check.
- **Label-error budget base:** observed binary 2020 screens per country (frame scope) or 6 × complete households (complete-only scope).
- **No ML:** see `reports/METHOD_SELECTION_AND_MODELS.md` §7.
- **Author metadata:** the git identity is "Isaac"; the surname was not assumed. CITATION/LICENSE use "Isaac (Isaac25-lgtm)" pending confirmation.

## Contribution-strengthening investigation (27 Oct 2026, EAT)

| Time | Phase | Action / command | Outcome | Decision / open issue |
|---|---|---|---|---|
| 08:20 | Repo | `git status`, log, branches; `git switch -c investigation/strengthen-contribution` | `main` = `53064ad`, clean, no stashes | All work on the branch; nothing merged |
| 08:22 | WB data | `sha256sum` on `data/raw/MWI_2020-2024_HFPS_v20_M_Stata.zip` | `5dfbd541…9c16`, matches | Extracted with `unzip -n` to `data/raw/worldbank_mwi_hfps_v20/extracted` (279 files) |
| 08:25 | WB audit | Variable labels, value labels, cover-page merges, dates | 15 food-security rounds; 20,610 records; 1,729 households; groups A/B in rounds 19–21; no PSU/strata | Round-level marginals of s8q7/s8q8 for all rounds were printed here (exposure logged in the protocol) |
| 08:30 | Verify | Independent script on the Aggarwal raw files | 227/185, 67/34, frontier and 22/102 reproduced exactly; odd/even-month schedule confirmed; Malawi panel starts Jul 2019 | — |
| 08:35 | Literature | Crossref/OpenAlex; Smith et al. (author version), Wollburg et al. draft, Deisemann slides read; IndiKit timing guidance | Novelty narrowed: lean-season timing is established guidance | Reframe as quantification, validation and robustness |
| 08:45 | Docs | World Bank questionnaires r1/r7/r11/r20 and basic information document | 30-day recall confirmed; HHS-style frequency categories only in rounds 20–21; no panel weights | — |
| 08:55 | Protocol | `reports/investigation/00_PROTOCOL_AND_EXPOSURE_LOG.md` written | Locked before household-level 2022–24 results | Not a preregistration |
| 09:00 | Solver | `history_bounds.py` + brute-force tests | First version failed 14/20 tests (Dinkelbach started from a single household) | Fixed (start from a full feasible world); 20/20 pass |
| 09:20 | Analysis | `hfps.run()`, `extensions.run()` | All ChatGPT Work numbers reproduced except rounds 7→8 gaps < 30 days (4.3% vs 5.6%) | Discrepancy recorded |
| 09:40 | Model | Logistic score trained on 2020 vs count rule | No gain over the count rule | No ML recommended |
| 09:50 | QA | ruff; pytest; release audit; two runs hashed | 166 passed; lint clean; PASS (232 files); 20/20 CSV identical | Not pushed |
| 09:31 | Protocol | Multi-country protocol committed (`8d33f4d`) before any download | SHA-256 23afabbe…5ba6d | Locked |
| 09:32 | Access | Scripted Microdata Library login with your supplied credentials | Login POST returned empty pages (bot protection) | Credentials deleted from scratchpad; manual download |
| 10:00 | Data | Six archives copied from Downloads; checksums recorded; extracted | Tanzania round 9 Stata file truncated in the published archive | Deviation D3 |
| 10:10 | Audit | Metadata-only scans: items, IDs, dates, clusters; horizon structure | Several split-sample horizons; Nigeria/Tanzania unusable | Deviations D1, D2, D4, D5 recorded |
| 10:15 | Analysis | `multicountry.run()` | H1 contradicted (primary 2/2 above zero); H3 supported (3/3) | Reported as is |
