# Investigation protocol and exposure log

*Written 27 October 2026, before any household-level analysis of the 2022–2024 World Bank HFPS rounds and before the Aggarwal July–June re-specification was computed. This is **not** a preregistration: every dataset below had already been partly seen, and the exposure is listed so readers can judge how much each result was open to data-driven choices.*

## 1. What was already known before this protocol

| Data | Already seen (by whom) | Consequence |
|---|---|---|
| Aggarwal et al. (2022) S1 Data, 2020 and 2021 HHS windows | Everything in the repository baseline (frontier, bounds, 2020→2021 frozen timing test), by this project | Any re-analysis of 2020–2021 is a robustness re-specification, not a new test |
| Aggarwal Malawi, July–December 2019 | Monthly record counts only (data audit); no outcome analysis | Outcomes not previously analysed, but they enter only as *training* data in the July–June test below |
| HFPS Malawi rounds 1–12 (2020–2021) | Exploratory analyses by ChatGPT Work (rounds 7/9/11 comparison, round 8 sensitivity, 2020→2021 transfer, missing-data bounds, wealth subgroup), reported to us as numbers only. Code and report not available | All 2020–2021 HFPS results are reproductions or exploratory extensions |
| HFPS Malawi rounds 16, 18, 19, 20, 21 (Nov 2022 – Apr 2024) | During today's data audit, round-level marginal counts of s8q7 and s8q8 were printed for **every** round (e.g. s8q7 "yes": r16 803/1,367; r18 671/1,343; r19 472/685; r20 439/680; r21 364/616). ChatGPT Work also opened these files for record counts | The *ranking* of single rounds by detection share in 2022–2024 is essentially determined by these marginals (same denominator within a cohort), so **no untouched ranking test remains** in the HFPS. Magnitudes and household-level quantities were not computed |

## 2. Frozen analysis specification (locked before computing household-level 2022–2024 results)

Common definitions (all analyses):
- **Positive screen**: item answered YES (code 1). NO (2) is negative. Any other value or missing is a missing screen.
- **Reference-positive household**: positive in at least one of the rounds that define the reference horizon. "Missed" means negative in the retained round(s). The reference is the set of observed rounds, not true hunger.
- **Primary item**: s8q7 ("You, or others in your household, were hungry but did not eat because there was not enough money or other resources for food", 30-day recall). **Secondary item**: s8q8 ("went without eating for a whole day"). Neither is an HHS item and neither is called HHS.
- **Random benchmark**: expected missed share when one (or m) of the observed rounds is chosen uniformly at random, computed exactly as C(n−K, m)/C(n, m).
- **Uncertainty**: percentile bootstrap, 2,000 draws, seed 20261027, resampling **districts** (31 units; coarse; not survey-design-correct because PSU/strata are not in the public files), with a household-resampling bootstrap reported alongside. Unweighted primary; a sensitivity uses the cross-sectional weight of the last round of the horizon, explicitly labelled as not a longitudinal weight.

Locked analyses:

1. **HFPS reproduction (2021).** Cohort complete on the item in rounds 7, 9, 11. Missed share for each single round and for random; identified per 100 complete households; increment from adding round 9 to round 7. Then the five-round set (7, 8, 9, 11, 12) with exact frontier m = 1…4 and inter-interview gaps from actual dates.
2. **HFPS 2020→2021 transfer (reproduction).** Train on households complete in rounds 1, 2, 3, 5, 6; select the round with the lowest missed share (earliest on ties); evaluate the calendar-corresponding 2021 round (late May–June = round 11) in the 7/9/11 cohort.
3. **HFPS calendar-matched transfer, 2020/21 → 2023/24 (new specification, ranking not blind).**
   - *Group B (primary)*: candidates June, December, April. Training horizon: round 1 (Jun 2020), round 6 (Dec 2020), round 9 (Apr 2021), households complete on all three. Test horizon: round 18 (Jun 2023), round 19 (Dec 2023), round 21 (Apr 2024), Sample_Type B households complete on all three.
   - *Training variant*: replace round 1 (pandemic-onset round) by round 11 (late May–Jun 2021), to show how selection depends on including a shock round.
   - *Group A*: candidates June, February–March. Training rounds 1 and 8; test rounds 18 and 20.
   - Report the frozen choice, its test missed share, each alternative and random. Selection stability by household bootstrap of the training data.
4. **Aggarwal Malawi July–June re-specification.** Train on July 2019 – June 2020 (all six two-month windows), select the window with the lowest missed share among complete households (earliest on ties), evaluate on July 2020 – June 2021. Threshold HHS ≥ 2. Village-cluster bootstrap as in the baseline.
5. **Equal-budget schedules (decision metrics).** For each cohort, every fixed schedule of 1 and 2 contacts: identified per 100 enrolled complete households, per 100 completed contacts, and per 100 call attempts (HFPS only, from the attempt log in section 1 files), plus the increment from the second contact. In-sample; no optimum is claimed.
6. **Who is missed.** HFPS 2021 7/9/11 cohort, s8q7: by urban/rural, 2019 wealth quintile, region. Ever-positive count, missed share of the early-year round, random, and the difference, with bootstrap intervals. Exploratory; cells with fewer than 30 reference positives flagged; no multiplicity correction claimed as confirmatory.
7. **Decision robustness (exact).** For the fixed-versus-random difference D, exact worst/best values over all completions of missing screens (frame = households observed at least once in the horizon), then with a shared budget of hypothetical flips of observed screens; the smallest budget that can reverse the sign of D (tipping point). Applied to HFPS 2021 (7/9/11) and Aggarwal Malawi 2021 (frozen Jan–Feb vs random). Solver validated by brute force before use.
8. **Measurement triangulation.** Rounds 20 and 21 (cross-sectional only): an HHS-analogue score from s8q6/6a, s8q7/7a, s8q8/8a using HHS scoring (rarely or sometimes = 1, often = 2). Reported as "HHS-analogue", never as HHS. Concordance with s8q7 occurrence.
9. **Second-contact rule (own idea, exploratory).** With budget for a second contact to half of the households negative at the first contact, compare: random half; poorest by 2019 wealth; "warning-sign" households (negative on the primary item but positive on a milder item at the first contact: HFPS FIES items 1–6; Aggarwal HHS = 1). Outcome: additional reference positives identified. Rules use only information available at the first contact.

Anything run outside this list is reported as an unplanned deviation in the negative/failed-tests record.
