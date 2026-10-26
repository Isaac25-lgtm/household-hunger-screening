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
| later | 9 Git | Commits, clean-clone test, push, CI | see `reports/PROJECT_HANDOFF.md` | — |

## Decisions recorded

- **Duplicate rule:** earliest dated record per household-window (outcome-blind); valid HHS preferred over missing (uses missingness only).
- **Bootstrap units:** villages with ≥ 1 complete household (primary); all frame villages as a sensitivity check.
- **Label-error budget base:** observed binary 2020 screens per country (frame scope) or 6 × complete households (complete-only scope).
- **No ML:** see `reports/METHOD_SELECTION_AND_MODELS.md` §7.
- **Author metadata:** the git identity is "Isaac"; the surname was not assumed. CITATION/LICENSE use "Isaac (Isaac25-lgtm)" pending confirmation.
