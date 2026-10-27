# Missed Household Hunger Under Infrequent Screening: Evidence from Liberia and Malawi

## Full scientific analysis report and manuscript-readiness assessment

| | |
|---|---|
| Report date | 27 October 2026 |
| Status | Independent reanalysis complete; manuscript **not** drafted; not peer reviewed |
| Code version | see `reports/PROJECT_HANDOFF.md` for the commit SHA of this report |
| Repository | https://github.com/Isaac25-lgtm/household-hunger-screening |
| Source data | Aggarwal et al. (2022), PLOS ONE 17(8): e0271488, S1 Data (doi:10.1371/journal.pone.0271488.s021), CC BY 4.0 |
| Configuration | `config/study.yaml` (SHA-256 recorded in `data/public_aggregates/results_summary.json`) |

---

## 1. Executive scientific conclusion

Among rural control households followed by phone in 2020, households that reported moderate/severe household hunger (HHS ≥ 2) usually did so intermittently. Of the reference-positive households, 75% in Malawi and 94% in Liberia were positive in only one to three of six bimonthly 30-day recall windows. As a result, screening fewer windows misses many of them:

- **Malawi** (227 complete histories, 185 reference-positive, 140 villages): retaining 1, 2 or 3 of the six windows at random misses **55.1% (95% village bootstrap 51.6–58.7)**, **31.9% (28.3–35.6)** and **18.2% (15.2–21.4)**. Over the full 297-household frame, with missing windows unrestricted, the one-screen value is **identified only within 50.8–59.3%**.
- **Liberia** (67 complete, 34 reference-positive, 47 villages): **69.6% (63.9–75.0)**, **47.5% (40.2–54.4)** and **30.7% (24.0–37.5)**. Only one third of the 206-household frame is complete, and the one-screen value is identified only within **39.8–78.6%**. Liberia's estimates are imprecise and weakly identified.

**Which windows are screened matters as much as how many.** In Malawi the single best window in 2020 was the lean-season Jan–Feb window (13.6% missed). Frozen and applied to 2021 it missed **21.6% (13.7–30.5)**, against **59.8%** for a random window: a difference of −38.2 pp (−46.9 to −29.2). The same holds in households complete in both years (20.2% vs 59.8%). In Liberia the 2020 choice (Mar–Apr) was unstable and did not clearly beat a random window in 2021 (−5.7 pp, −26.9 to +14.1; 22 reference-positive households).

These are statements about **ascertainment of households relative to six observed 30-day windows in one study sample**. They are not hunger prevalence, not annual incidence, not national or IPC undercounts, and not causal effects of interviewing less often.

All earlier exploratory numbers reproduced independently (48/48 checks). **Recommendation: CONDITIONAL GO to begin manuscript drafting** (§16), with the paper reframed around schedule design (frequency *and* timing) and positioned against Zhu et al. (2026).

## 2. Background, operational decision and novelty

Programmes that monitor a fixed cohort to identify households for follow-up must choose how often, and when, to interview. Food insecurity fluctuates within households over weeks and seasons (Nord et al. 2002; Na et al. 2017), so each interview with 30-day recall observes a short window. Sparser schedules miss more households that are hungry at some point. Zhu et al. (2026) recently quantified single-round *misclassification* against an annual-average benchmark using Indian weekly diaries. This study asks a related but distinct question for an experiential indicator in two African panels: **what share of households that screen positive at least once in six bimonthly windows would a schedule with fewer windows fail to identify, how robust is that to missing interviews and label error, and does a calendar window chosen in one year keep working in the next?**

The source study (Aggarwal et al. 2022) estimated *mean* food-security changes during COVID-19 market disruptions. It did not address household ascertainment, schedule design or missing-history identification. Citation screening of all 46 works citing it (OpenAlex) found no reuse of its data for this question. See §10 and `NOVELTY_AND_CLOSEST_WORK.md`.

## 3. Data, provenance, sample construction and QA

The public S1 Data archive (9,098,158 bytes; SHA-256 `de2ae59d…66bb`, matching the earlier record) was downloaded from PLOS on 26 Oct 2026, and two files were used: the household phone panel (4,744 records) and the baseline phone frame (503 control households: Malawi 297, Liberia 206). All 22 integrity checks passed. IDs are unique and never collide across countries, every phone record merges to the frame with consistent country and village, dates agree with recorded months, there are no repeated household-months, and HHS is an integer in 0–6 for all but one record (missing). The three HHS occurrence items are present but the frequency follow-ups are not, so the score cannot be rebuilt. It is, however, consistent with the items for every record (yes-count ≤ HHS ≤ 2 × yes-count). The source-provided score is therefore used.

Designated windows are two-month blocks (Jan–Feb … Nov–Dec), reflecting the parent design of alternating-month calls. One Liberia household had two records in one window, and the earliest was kept (outcome-blind). This does not affect HHS ≥ 2.

Complete six-window 2020 histories: **Malawi 227 of 297 (76%)** in 140 villages; **Liberia 67 of 206 (33%)** in 47 villages. Reference-positive: 185 and 34. Full flow: Table 1, Figure 1, `DATA_QUALITY_AND_COHORT_FLOW.md`.

Record-level data are not redistributed. Public outputs are aggregates checked by an automated release-safety audit.

## 4. Objectives, estimand and identification

**Primary estimand.** For complete household *i* with *K_i* positive windows of *n* = 6, and *m* windows retained uniformly at random without replacement:

M_m = Σ_i 1[K_i > 0] · C(6 − K_i, m)/C(6, m) ÷ Σ_i 1[K_i > 0].

M_m is conditional on (a) the analysed households and (b) the six observed 30-day windows. Households never positive are not in the denominator. The uniform-random design is a **benchmark** that averages over all C(6, m) fixed schedules (§7.3); operational schedules are fixed or calendar-based, and these are analysed separately (§7.3, §9).

**Identification.** For the complete-history estimate, M_m is computed exactly. Over the frame, with unknown missing windows, only a set is identified (§8.1). Under hypothetical label error, a wider set is identified (§8.2). The timing analysis is a separate four-window design (§9).

## 5. Methods (summary; full inventory in `METHOD_SELECTION_AND_MODELS.md`)

1. **Exact ascertainment frontier**: hypergeometric zero-success probability, exact rational arithmetic, m = 1…6.
2. **Village-cluster percentile bootstrap**: villages resampled with replacement within country, 2,000 draws (seed 20261026), with stability variants (20,000 draws; all frame villages as units; delete-one-village jackknife).
3. **Sharp missing-history bounds**: exact optimisation over all binary completions of missing windows. The denominator moves with the completion, and the optimum is found by exhaustive prefix search over sorted optional households (proof in the methods file).
4. **Shared-budget label-error bounds**: minimum flips to reach count *K* are max(0, k − K, K − k − r). A single country-level budget B = ⌊α · observed screens⌋ (α = 1, 5, 10%) is shared, and the ratio is optimised exactly by Dinkelbach iteration over an integer knapsack DP. Termination gives the optimality certificate F(λ*) = 0.
5. **Frozen timing assessment**: the best of four common windows (Jan–Aug) is chosen on 2020 only (ties → earlier) and evaluated in 2021 (full and matched cohorts) against a random-window benchmark with the same denominator. Uncertainty comes from village bootstrap, plus a bootstrap of the selection step to measure its stability.
6. **Secondary**: attrition balance (CR1 village-clustered), IPW under MAR-given-baseline, alternative thresholds (HHS ≥ 1, ≥ 4) and the fixed-schedule enumeration.

**No machine learning** was used in this trial-data analysis (a logistic regression benchmark was later fitted only for the World Bank second-contact decision problem; see `METHOD_SELECTION_AND_MODELS.md`, section on model history). The estimand is an exact design quantity, and a prospective risk-prediction task was considered and rejected (§6 of the methods file).

## 6. Model and method inventory: strengths, weaknesses and diagnostics

| Method | Strength | Weakness | Diagnostics |
|---|---|---|---|
| Exact frontier | No approximation; transparent | Assumes random retention (a benchmark) | Equal to subset enumeration for all histories up to n = 7 |
| Village bootstrap | Respects clustering | Coarse in Liberia (34 positives, 47 clusters); ignores frame missingness | 2,000 vs 20,000 draws differ ≤ 0.2 pp; jackknife SE ≈ bootstrap SE |
| Sharp missing bounds | No assumptions; exact | Can be wide (Liberia) | Brute force on 40 random instances (all m) |
| Label-error bounds | Exact; one shared budget; certified | Budgets are hypothetical | Brute force on 25 instances × 4 budgets × 2 m; nesting; α = 0 identity |
| Timing | Frozen selection; leakage-guarded | Two years; cohort changes; small Liberia n | Leakage tests; bootstrap selection stability |
| IPW | Uses baseline covariates | Strong untestable MAR | Max weight 11.0 (Liberia), effective n 27 |

## 7. Results

### 7.1 Interview-count frontier (Table 2, Figure 2)

| m | Malawi missed (95% CI) | Liberia missed (95% CI) |
|---:|---|---|
| 1 | 55.1% (51.6–58.7) | 69.6% (63.9–75.0) |
| 2 | 31.9% (28.3–35.6) | 47.5% (40.2–54.4) |
| 3 | 18.2% (15.2–21.4) | 30.7% (24.0–37.5) |
| 4 | 9.7% (7.5–11.9) | 17.8% (12.5–23.2) |
| 5 | 4.1% (2.9–5.2) | 7.8% (4.8–10.9) |

In absolute terms, one random screen would miss an expected 102.0 of 185 reference-positive Malawi households and 23.7 of 34 in Liberia.

### 7.2 Intermittency (Figure 3)

Malawi K = 0…6: 42, 45, 44, 49, 25, 14, 8. Liberia: 33, 16, 11, 5, 1, 1, 0. Liberia's reference-positive households are almost all positive in only one or two windows, which explains its steeper frontier.

### 7.3 Fixed schedules (Figure S2; in-sample, exploratory)

Averaging over every fixed schedule reproduces the random frontier, but the spread across schedules is large. In Malawi the best single window (Jan–Feb) misses 17.8% and the worst (Jul–Aug) 83.2%. The best pair (Jan–Feb + Mar–Apr) misses 6.5%, against 71.4% for the worst pair. In Liberia the best and worst single windows miss 58.8% (May–Jun) and 79.4% (Jul–Aug). Selecting the best schedule in the same data is optimistic, which is why §9 tests a frozen choice out of year.

### 7.4 Secondary thresholds (Figure S3)

HHS ≥ 1 gives lower losses (Malawi 43.1%, Liberia 53.0% at m = 1; 207 and 56 reference-positive). For HHS ≥ 4, every severe-reference household (Malawi 12, Liberia 2) was severe in exactly one window, so the frontier is (6 − m)/6 and uninformative. Severe-only analysis is not recommended.

## 8. Robustness: missing histories and label error

### 8.1 Sharp missing-history bounds (Table 3, Figure 4)

| | Malawi (297 frame; 70 with missing windows) | Liberia (206; 139 with missing windows) |
|---|---|---|
| m = 1 | 50.8–59.3% | 39.8–78.6% |
| m = 2 | 27.8–36.5% | 20.7–59.9% |
| m = 3 | 15.1–22.1% | 10.7–43.1% |

These are **identification bounds, not confidence intervals**. In Malawi the missing data move the m = 1 answer by at most about ±4 pp around the complete-case value. In Liberia they could move it by −30/+9 pp. Single imputations fall strictly inside the bounds (Malawi m = 1: all-missing-negative 57.5%, all-missing-positive 52.2%), confirming that naive filling does not give the endpoints. The IPW estimate under MAR-given-baseline barely moves the complete-case values (Malawi 54.9%, Liberia 70.3%; Table S2). That shows only that observed baseline covariates do not explain selection; it does not show that selection is ignorable.

### 8.2 Hypothetical label-error budgets (Table 3, Figure 5)

| m = 1 | 1% budget | 5% budget | 10% budget |
|---|---|---|---|
| Malawi (16 / 82 / 165 flips) | 48.5–60.8% | 39.6–65.0% | 31.8–70.1% |
| Liberia (8 / 40 / 81 flips) | 37.1–79.4% | 25.1–82.5% | 12.0–83.3% |

Among complete histories only (isolating label error from missingness), a 5% budget gives Malawi 43.3–62.3% and Liberia 53.7–79.4% at m = 1. The qualitative conclusion that one random screen misses a large share holds in Malawi up to about a 5% error budget, but the precise level is sensitive to modest misclassification. These budgets are hypothetical, not estimated error rates.

## 9. Calendar timing: 2020 selection, frozen 2021 evaluation (Tables 4–5, Figures 6–7)

| | Malawi | Liberia |
|---|---|---|
| 2020 four-window complete / reference-positive | 249 / 191 | 89 / 43 |
| Selected on 2020 (ties → earlier) | Jan–Feb (13.6%) | Mar–Apr (58.1%) |
| Selection stability (2,000 village bootstraps of 2020) | Jan–Feb 100% | Mar–Apr 62%, May–Jun 20%, Jan–Feb 15%, Jul–Aug 2% |
| 2021 cohort: frozen vs random | 21.6% (13.7–30.5) vs 59.8% (55.1–63.8); n+ = 102 | 54.5% (31.6–77.3) vs 60.2% (53.0–67.5); n+ = 22 |
| Difference (95% bootstrap) | −38.2 pp (−46.9 to −29.2) | −5.7 pp (−26.9 to +14.1) |
| Matched both years: frozen vs random | 20.2% vs 59.8%; n = 171, n+ = 89 | 61.5% vs 63.5%; n = 40, n+ = 13 |

In Malawi, 2021 Jan–Feb positivity was lower than in 2020 (39.8% vs 66.3% of observed screens; Figure S1), yet the lean-season window still identified most reference-positive households. In 2021 Jul–Aug (70.6%) did better than May–Jun (83.3%), unlike 2020; this is post hoc disclosure only. The Liberia timing result is uninformative. With two adjacent pandemic-era years, this shows *transfer across one year*, not a stable seasonal optimum, and it is not a causal estimate of moving an interview calendar.

## 10. Closest literature and novelty verdict

The closest study is **Zhu, Gupta, Doan & Michuda (2026), *Food Security* 18(5):1509–1524**. With 305 Indian households keeping weekly diaries for a year, they find single-round misclassification of 15–48% across expenditure-based indicators, falling to 6–15% when indicators are combined. Their core message (one-off measurement misidentifies households because food security fluctuates) **pre-empts** a "first" claim here. Differences: an experiential HHS screen with 30-day recall; an ever-positive ascertainment estimand rather than annual-average classification; the full m = 1…6 frontier; sharp missing-data and label-error identification; a frozen out-of-year timing test; and two African countries with clustered inference. Other relevant work: Na et al. 2017 (monthly HFI in Zambia), Livings et al. 2023 (past-year under-reporting), Nord et al. 2002 (frequency and duration), McDonough & Millimet 2024 (partial identification of food-security dynamics under measurement error), Bell et al. 2019 (recall decay by survey frequency) and Lentz et al. 2025 (IPC undercounts acute hunger; cited only to delimit claims).

**Verdict:** no duplication of the joint study was found. The contribution is a modest applied measurement advance whose novelty rests on the estimand, bounds and timing test, not on any method. Full table: `NOVELTY_AND_CLOSEST_WORK.md`.

## 11. Scientific validity

The main threats are detailed in `LIMITATIONS_AND_THREATS.md`:

- **Retrospective thinning ≠ prospective design.** Responses, recall and attrition could differ if fewer interviews were actually conducted.
- **Observation windows.** About half the year is unobserved, so the reference is not truth.
- **Selection into complete histories.** Large in Liberia; bounded, not assumed away.
- **Measurement.** HHS is self-reported and validated for population prevalence rather than household screening; label error is handled only hypothetically.
- **Small samples.** Liberia has 34 positives and 47 villages; the matched timing cohort has 13 positives.
- **Multiplicity.** Exploration of windows and schedules; the frozen test addresses only timing.
- **Period and sample.** COVID-era data; control households of an RCT; not representative.
- **Costs.** No cost data, so no optimal-frequency claim.

## 12. Alternative interpretations, falsification and discrepancies

- *"High loss is an artefact of random retention."* Partly true. Fixed lean-season schedules do much better in Malawi (§7.3, §9), so the frontier is presented as a benchmark.
- *"Positives are noise, not hunger."* If many single positives were classification errors, the 'true' frontier would be lower. The label-error analysis shows the m = 1 Malawi value stays at or above 39.6% unless more than 5% of observed labels are wrong.
- *"Attrition drives the result."* Malawi bounds are narrow (50.8–59.3%), which rules this out there. In Liberia it cannot be ruled out.
- *Discrepancies:* none in reproduction. Interpretive changes are listed in `REPRODUCTION_AUDIT.md`: the random-window framing, Liberia timing instability, weak identification in Liberia and degenerate severe hunger.

## 13. Practical implications (bounded)

For a programme repeatedly screening a fixed rural cohort with HHS and 30-day recall in settings like these:

- **Frequency.** Moving from six to three bimonthly screens would miss roughly one in five (Malawi) to one in three (Liberia) households that screen positive at least once, if windows were dropped at random.
- **Timing.** Where hunger is strongly seasonal (Malawi), placing even one screen in the lean season captured most households that screened positive at any time in the four observed windows, and this held out of year.
- **Missing data.** Missing follow-up can make it impossible to know how many households were missed (Liberia).

What the results cannot provide is a cost-optimal schedule. That requires per-interview costs, the value of timely detection and the consequences of false negatives, none of which are in these data.

## 14. Manuscript vs supplement; proposed outline

**Main text** (4–6 displays): Figure 2 (frontier, hero), Figure 4 (bounds), Figure 6 (timing), Table 2, Table 3, Table 5. Optional: Figure 1 or Table 1. **Supplement:** Figures 3, 5, 7, 8, 9, S1–S3; Tables 4, S1–S4; full methods proofs; reproduction audit.

**IMRaD skeleton**
1. *Introduction:* repeated household screening; intermittency; Zhu et al. (2026) and other prior work; gap (ascertainment estimand for HHS, missing-data identification, out-of-year timing).
2. *Methods:* data and frame; windows; estimand; exact frontier; bootstrap; sharp bounds; label-error sensitivity; frozen timing design; pre-specified primary and secondary analyses.
3. *Results:* cohort; intermittency; frontier; bounds; timing; secondary analyses.
4. *Discussion:* frequency vs timing; Malawi vs Liberia; identification limits; comparison with Zhu et al.; limitations; implications and data needed for cost optimisation.

## 15. Outstanding tasks requiring people outside this pipeline

| Task | Who | Why |
|---|---|---|
| Re-read the source Methods and questionnaire; confirm the alternating-month schedule and HHS phone wording, ideally with the source authors | Researcher | The window mapping is central to the estimand |
| Full-text review of McDonough & Millimet (2024) and structured grey-literature search | Researcher / co-author | Novelty positioning |
| Statistical review of bounds and shared-budget formulation | Methods co-author | Rigour |
| Ethics determination for secondary analysis of public de-identified data | Institution | Journal requirement |
| Decide the primary contrast; pre-register | Team | Prevent garden-of-forking-paths |
| Author name and affiliation | Researcher | Metadata currently uses the GitHub handle |

## 16. Decision

**CONDITIONAL GO to begin manuscript drafting.** The conditions are: reframe around frequency *and* timing, with the random frontier as benchmark; cite and differentiate Zhu et al. (2026) prominently; keep Liberia secondary; keep CIs, bounds and label-error envelopes separate.

**Submission readiness: NOT READY.** The critical blockers are the source-design confirmation, the remaining literature work, and the methods and ethics review (`MANUSCRIPT_READINESS_VERDICT.md`). No acceptance probability is offered.

## 17. Reproduction

```powershell
git clone https://github.com/Isaac25-lgtm/household-hunger-screening.git
cd household-hunger-screening
powershell -ExecutionPolicy Bypass -File scripts\bootstrap_environment.ps1
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1      # download + verify + analyse + figures + tables + tests + safety audit
powershell -ExecutionPolicy Bypass -File scripts\run_dashboard.ps1 # http://localhost:8501
```

Input checksum: S1 Data ZIP SHA-256 `de2ae59d6190d70722b3aac33a9363e23ebea907ca639f7224bca2d9b11b66bb` (9,098,158 bytes). Local test status at report time: 134 passed, 0 failed, 0 skipped (`VALIDATION_AND_TEST_RESULTS.md`). Two consecutive full runs produced byte-identical CSV outputs (29 files). Git commit and CI status: `PROJECT_HANDOFF.md`.
