# Manuscript readiness verdict

**Decision to start manuscript drafting: CONDITIONAL GO**
**Submission readiness: NOT READY** (see the blockers below)

A GO for drafting is not a statement that the paper is ready to submit or likely to be accepted.

## Why not HOLD

- Every earlier quantity reproduced independently: 48/48 checks, exact counts, point estimates and bounds; bootstrap endpoints within 0.5 pp.
- The source data passed 22/22 integrity checks, with provenance hash-verified.
- All solvers are exact and validated against brute force, and the test suite passes.
- The closest prior work (Zhu et al. 2026) overlaps the *message* but not the estimand, indicator, data, missing-data analysis or out-of-year timing test. No duplicate of the joint study was found.

## Why only CONDITIONAL

The conditions below must be met in the draft itself:

1. **Reframe around schedule design (frequency *and* timing).** The random-window frontier is a benchmark. In Malawi a single lean-season window chosen on 2020 missed 21.6% in 2021, against 59.8% for a random window. Presenting only "55% missed" would overstate the operational loss and invite the critique that real programmes do not pick windows at random.
2. **Position explicitly against Zhu et al. (2026, *Food Security*).** No "first" claims; state the differences in estimand, indicator, setting and methods.
3. **Treat Liberia as secondary and weakly identified** (33% complete; m = 1 range 39.8–78.6%; timing uninformative with 13–22 positives). Do not pool countries.
4. **Keep the three uncertainty objects visually and verbally separate** (bootstrap CI, identification range, hypothetical label-error envelope).

## Blockers before submission (ranked)

| Rank | Blocker | Severity | Who |
|---|---|---|---|
| 1 | Full-text reading of McDonough & Millimet (2024) and Zhu et al. supplementary material, plus a structured search of Scholar/SSRN/RePEc and grey literature (FEWS NET, WFP mVAM sentinel designs) for visit-frequency analyses | Critical | Researcher / co-author |
| 2 | Re-read the source article's Methods and the questionnaire for the exact HHS phone-item wording, interviewer protocol and call schedule (alternating months), and confirm the designated-window mapping with the original authors if possible | Critical | Researcher (optionally contact the source authors) |
| 3 | Decide the primary manuscript contrast (random frontier vs fixed/calendar schedules) and pre-register it before more exploration | Major | Researcher + methods co-author |
| 4 | Methods review of the bounds (sharpness proof, shared-budget formulation) by a statistician | Major | Methods reviewer |
| 5 | Target journal and reporting standard (e.g. *Food Security*, *Food Policy*, *Global Food Security*, *PLOS ONE*; STROBE-style reporting for secondary analysis) | Major | Researcher |
| 6 | Ethics: confirm institutional view on secondary analysis of public de-identified data (usually exempt; verify) | Major | Institution |
| 7 | Author identity and affiliation in CITATION/LICENSE (currently "Isaac (Isaac25-lgtm)") | Minor | Researcher |
| 8 | Optional: replication on a second high-frequency panel (e.g. World Bank HFPS or LSMS-ISA) to address external validity | Minor (strengthening) | Researcher |

## Established vs plausible

| Established (reproduced, exact or bootstrapped) | Plausible (supported but fragile) | Not supported / must not be claimed |
|---|---|---|
| Malawi random-window frontier 55.1 / 31.9 / 18.2% and its CIs | That lean-season timing generally beats random timing in Malawi (two years only) | National or annual undercount; IPC implications |
| Malawi frame bounds 50.8–59.3% (m = 1), narrow | Liberia complete-case frontier as representative of the Liberia frame | Causal effect of interviewing less often |
| Liberia frame bounds are wide (39.8–78.6%) | Any optimal fixed schedule (in-sample only) | Any cost-effectiveness claim |
| Intermittency: 75% (Malawi) and 94% (Liberia) of reference-positive households are positive in only 1–3 of six windows | — | Algorithmic novelty |
