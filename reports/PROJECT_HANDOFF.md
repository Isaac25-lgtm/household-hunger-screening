# Project handoff

*State as of 27 October 2026.*

## Where things are

| Item | Location / value |
|---|---|
| Local project | `F:\MY FILES\DATA SCIENCE\PUBLISHING\household-hunger-screening` |
| GitHub | https://github.com/Isaac25-lgtm/household-hunger-screening (branch `main`) |
| Analysis commit pushed | `fcaa5d28f342b43585dbd76e3e9cec5872d59a7b` (6 scoped commits; no force-push) |
| CI on that commit | **success**: GitHub Actions run [40404757667](https://github.com/Isaac25-lgtm/household-hunger-screening/actions/runs/40404757667) (Install, Lint, Release-safety audit, Tests all succeeded; ubuntu-latest, Python 3.12; 21:29–21:30 UTC) |
| Dashboard (local) | `scripts\run_dashboard.ps1` → http://localhost:8501 (the same app was launched on test port 8517 and verified: `/_stcore/health` = ok, root HTTP 200; all 9 sections pass `AppTest`) |
| Dashboard (public) | **Not deployed** (no hosted URL exists). Deploy at share.streamlit.io: repo `Isaac25-lgtm/household-hunger-screening`, branch `main`, file `dashboard/app.py` |
| Source data (local only, gitignored) | `data\raw\download\S1_Data.zip` (SHA-256 `de2ae59d…66bb`), `data\raw\extracted\` |
| Household-level intermediates (local only) | `data\interim\` (slot matrices, bootstrap replicates) |
| Logs (local only) | `logs\` (pipeline log, solver runtimes, pytest output, dashboard log) |

## What was done

1. Provenance: downloaded and hash-verified the PLOS S1 Data; 22/22 integrity checks.
2. Independent reconstruction of the frame, designated windows and cohorts; 48/48 earlier quantities reproduced.
3. Exact frontier, village bootstrap (with stability checks), sharp missing-history bounds, shared-budget label-error bounds (certified exact), and frozen 2020 → 2021 timing test with selection-stability bootstrap.
4. Secondary analyses: thresholds, fixed schedules, attrition balance, IPW.
5. Literature: Crossref/OpenAlex verification, citing-work screen (46), closest work identified and read in full (Zhu et al. 2026).
6. 12 figures (PNG/SVG/PDF), 9 tables, 11 reports, a Streamlit dashboard, 134 tests, CI and a release-safety audit.

## Verdict

**CONDITIONAL GO** to begin manuscript drafting; **NOT READY** to submit. See `MANUSCRIPT_READINESS_VERDICT.md`.

## Next steps (in order)

1. Confirm the alternating-month design and HHS phone wording from the source Methods/questionnaire (ideally with the source authors).
2. Finish the literature work (McDonough & Millimet full text; grey literature on sentinel visit frequency).
3. Fix and pre-register the primary contrast (frequency frontier as benchmark; calendar/fixed schedules as the operational comparison).
4. Draft the manuscript using the IMRaD skeleton in `FULL_SCIENTIFIC_ANALYSIS_REPORT.md` §14.
5. Methods review of the bounds; ethics determination; author metadata.
6. Optional: deploy the dashboard; replicate on a second panel.

## Resuming work

```powershell
cd "F:\MY FILES\DATA SCIENCE\PUBLISHING\household-hunger-screening"
.\.venv\Scripts\python.exe -m hunger_screening.cli all     # regenerate everything (about 40 s)
.\.venv\Scripts\python.exe -m pytest -q                    # 134 tests
.\.venv\Scripts\python.exe scripts\check_release_safety.py # before any push
```
