# Can the household hunger screening study make a stronger contribution? Full investigation report

> **Revision note (27 October 2026, revised manuscript package).** Some statements in this historical report were corrected in place. The current, authoritative summary is `reports/ALL_FINDINGS.md`; the analysis history and evidence classes are in `reports/ANALYSIS_HISTORY_AND_EVIDENCE_CLASSES.md`. Changes are listed in the package's `07_quality_control/CHANGELOG_FROM_PREVIOUS_PACKAGE.md`.

*27 October 2026. Branch `investigation/strengthen-contribution`, starting from `main` at `53064ad`. Every number below was computed in this investigation from the source files. It comes from the aggregate files named in brackets under `data/public_aggregates/investigation/` or, for the baseline study, `data/public_aggregates/`. Numbers supplied in the instructions were used only to check reproduction; none of them entered a calculation.*

> **Update (27 October 2026, later the same day).** A protocol-locked test in five other countries' phone surveys has since been run; see `11_MULTICOUNTRY_RESULTS.md`.
>
> - **Calendar rule: contradicted.** Contacting households in the FEWS NET lean season did not beat a randomly timed contact (Burkina Faso 2020–21: +10.9 points; Uganda 2020–21: +3.4, inconclusive).
> - **Second-contact warning rule: supported** (3 of 3 testable horizons).
>
> The Malawi timing findings below stand, but they must be presented as **Malawi-specific**, not as a general lean-season rule.

## 1. Summary

**Short answer: yes, the study can be materially stronger, but not by enough to justify a high-impact framing today.** The investigation added a second, independent Malawi panel: the World Bank High-Frequency Phone Survey (HFPS), 2020–2024. It also ran calendar-matched tests on later years and computed exact robustness ranges for the timing comparison. Five things are now demonstrated:

1. **Timing replicates in independent data.** In both Malawi panels, a single contact during the peak hunger months (January–March) missed fewer of the households that reported hunger at any observed contact than a contact at a random observed time. This held in all six comparisons where those months were available:
   - **Aggarwal 2020:** January–February missed 17.8% against 55.1% for a random window.
   - **Aggarwal 2021:** 21.6% against 59.8%.
   - **Aggarwal, July 2020 – June 2021 year:** 38.3% against 59.3%.
   - **HFPS 2021, January round:** 23.9% against 35.1%.
   - **HFPS 2021, late February – mid-March round:** 25.9% against 41.4%.
   - **HFPS 2024, February–March round (group A):** 11.9% against 21.7%.

   The size of the gap differs a lot between datasets (11 to 38 percentage points). November and December contacts were inconsistent.
2. **Choosing a month from one earlier year can fail.** It worked when the training year was typical. It failed when the training data began at an unusual moment: the World Bank survey's first round (late May – June 2020) coincided with the pandemic onset and was also the first interview. Selecting on 2020 picked June. In 2021, June then missed 12.7 points more than random. In 2023–24 it missed 12.6 points more than random, while the December alternative missed 12.3 points fewer.
3. **Missing data cannot overturn the result, but small answer errors could.** For the primary outcomes, no pattern of missing interviews can erase the timing advantage (exact ranges). Worst-case errors in 0.5–2.5% of recorded answers can.
4. **Who is missed.** In the World Bank panel, the January advantage was concentrated in poorer and rural households. This is exploratory and descriptive.
5. **A second contact pays off less than a well-timed first one.** It adds about 9–12 identified households per 100 extra contacts. A one-line rule targets it well: re-contact first-contact negatives who answered "yes" to a milder food-insecurity question. A model trained on 2020 data did no better than simply counting those "yes" answers.

**What remains unproven.**
- No test is blind. Every dataset used had been partly seen before; the exposure log is in `00_PROTOCOL_AND_EXPOSURE_LOG.md`.
- The World Bank question is not the Household Hunger Scale (HHS).
- Nothing shows that programmes would deliver better assistance.
- Nothing extends beyond Malawi.
- The direction of the timing effect matches existing field guidance. People in Need's IndiKit guidance recommends collecting during or directly after the worst of the lean season. The contribution is to quantify that advice, validate it across datasets and years, test its robustness and show where it fails. It is not a discovery.

## 2. Repository state and preservation

- **Starting point.** `main` at `53064adc79de39cab238120ad24cf39a3f22cd75`, with a clean working tree, no stashes and no other branches. All work is on the new branch `investigation/strengthen-contribution`. Nothing was reset or deleted, and no baseline output changed: the baseline pipeline was not re-run, and all 134 baseline tests still pass.
- **World Bank archive.** `data/raw/MWI_2020-2024_HFPS_v20_M_Stata.zip` is 19,910,888 bytes. Its SHA-256 is `5dfbd541af7d791f1b1571d9c50e95c2f52619ef20a6b43b0bf665c3c36c9c16`, which matches the expected value. It was extracted, without overwriting, to `data/raw/worldbank_mwi_hfps_v20/extracted/` (279 files). That folder is separate from the Aggarwal files in `data/raw/extracted/`. Both folders are gitignored.
- **New code:**
  - `src/hunger_screening/hfps.py`: World Bank analyses.
  - `extensions.py`: new analyses of the Aggarwal data.
  - `history_bounds.py`: generic exact ranges.
  - `schedule_metrics.py`
  - `investigation_figures.py`
- **New configuration:** `config/investigation.yaml`.
- **New tests:** `tests/test_history_bounds.py` and `tests/test_investigation.py`.

## 3. Verification of the existing study

| Claim | Independent check | Result |
|---|---|---|
| 2020 complete six-window cohorts: Malawi 227 households (185 reference-positive), Liberia 67 (34) | Separate script, not using project code, built from the raw `.dta` files | Reproduced exactly |
| Missed share at 1 / 2 / 3 windows: Malawi 55.1 / 31.9 / 18.2%, Liberia 69.6 / 47.5 / 30.7% | Same script | Reproduced exactly |
| 2021 Malawi: 22 of 102 missed (21.6%) by the frozen January–February window, against 59.8% at random | Same script; training cohort 249 complete households (191 reference-positive), test cohort 197 (102) | Reproduced exactly |
| Two-month windows match the call schedule | Interview dates checked directly | **Supported.** 94% of households stay in odd or even months throughout. The split is even (Malawi 150 / 147; Liberia 93 / 93). The median gap between interviews is 61 days, and fewer than 0.2% of gaps are under 30 days. 6% of households switch parity at some point. |
| Panel start dates | Monthly record counts | **New fact.** Malawi interviews run from **July 2019** to August 2021, so its January–February 2020 interview was not the household's first. Liberia runs from January 2020 to October 2021, so its January–February 2020 window *was* the first interview. |

**Interpretation caveats** (reproduced here, not resolved):
- The 2021 reference covers four observed windows.
- With 30-day recall roughly every 61 days, about half of the calendar is never observed.
- "Reference positive" means positive in at least one observed window, not true hunger.
- Removing observed interviews after the fact is not the same as running fewer interviews.

## 4. World Bank Malawi HFPS: audit

*Source: Malawi High-Frequency Phone Survey 2020–2024, version 20, World Bank Microdata Library, catalog 3766, doi:10.48529/s2n6-9f47. These are public-use files: aggregates may be published with a citation, and the microdata may not be redistributed.*

| Fact | Value | Source file |
|---|---|---|
| Food-security rounds | 15: rounds 1–3, 5–9, 11, 12, 16, 18–21 | `hfps_round_audit.csv` |
| Household-round records / distinct panel households | 20,610 / 1,729 | same |
| Household ID unique within each round; each record links one-to-one to a cover-page record with the same panel ID | Yes, all rounds | `hfps_integrity_checks.csv` |
| Refreshment sample | None. Every household appears in round 1, so **round number and calendar time cannot be separated** | same |
| Sample groups | Rounds 19 (Dec 2023) and 21 (Apr 2024) are group B; round 20 (Feb–Mar 2024) is group A. No household is in both groups (19 ∩ 20 = 20 ∩ 21 = 0; 19 ∩ 21 = 600 households). The documentation does not say how households were assigned to groups. | `hfps_household_overlap.csv` |
| Fieldwork per round | 1–3 weeks per round, e.g. round 7: 20 Jan – 6 Feb 2021; round 8: 23 Feb – 15 Mar 2021; round 20: 22 Feb – 12 Mar 2024. Six records lack a date. | `hfps_round_audit.csv` |
| Gaps between interviews | Rounds 7→8: median 36 days, **4.3%** under 30 days. Rounds 11→12: median 19 days, **99.7%** under 30 days, so their 30-day recall periods overlap. Rounds 3→5: median 79 days (round 4 had no food-security module). | `hfps_interview_gaps.csv` |
| Survey weights | Cross-sectional weights adjusted for attrition within each round (Basic Information Document §3.2). **No panel weight.** | documentation |
| Clusters | No PSU, stratum or enumeration-area ID in the public files. Uncertainty therefore resamples districts (31) and, separately, households; neither is survey-design-correct. | data inspection |
| Logged call attempts | 2.3–3.1 per completed interview in 2020–2023, rising to 4.5–6.5 in rounds 19–21. The log covers completed households only, so effort spent on unreached households is not counted. | `hfps_round_audit.csv` |

**Measurement (checked against the round 7, 11 and 20 questionnaires).** The module is the 8-item Food Insecurity Experience Scale (FIES). Each item asks: "During the last 30 days, was there a time when you, or others in your household, …". Answers are yes or no.

- **Primary item, s8q7:** "were hungry but did not eat because there was not enough money or other resources for food."
- **Secondary item, s8q8:** "went without eating for a whole day."

Rounds 20 and 21 add frequency follow-ups to items 6–8 using the HHS categories: rarely (1–2 times), sometimes (3–10 times), often (more than 10 times). The official HHS asks three different questions: no food of any kind in the house; going to sleep at night hungry; a whole day and night without eating. So:

- **This is related-item triangulation, not an HHS replication.** No result in this report is labelled "HHS ≥ 2" for the World Bank data.
- The three frequency-scored items give an **HHS-analogue score**, available only in rounds 20 and 21, and only cross-sectionally (`hfps_hhs_analogue.csv`):
  - Of households answering "yes" to s8q7, 89.5% (round 20) and 85.7% (round 21) score 2 or more.
  - Of households scoring 2 or more, 98.0% and 97.8% answered "yes" to s8q7.

**Reproduction of the ChatGPT Work numbers.** Every reported number reproduced except one date-gap share (§9):
- 1,443 complete households; 933 positive at least once on s8q7.
- Missed share by round: 23.9% (January), 33.7% (April), 47.8% (late May–June); 35.1% at random.
- s8q8: 34.4%, 47.7% and 61.3%; 47.8% at random.
- 49.2 and 60.8 identified per 100 households, so the second contact adds 11.6.
- Five-round cohort: 1,387 households, with round 8 ahead of round 7.
- 2020→2021 transfer: June 2020 selected; 47.8% missed in 2021, against 23.9% for January and 35.1% at random.
- Missing-data ranges: s8q7 −14.8 to −4.7 points; s8q8 −21.3 to +0.9 points, over a frame of 1,632 households.
- The poorest households show a larger timing advantage than the richest.

## 5. Results

### 5.1 Single-contact timing within each year

*Source: `hfps_single_round.csv`. Complete cohorts, s8q7. Brackets are 95% district-cluster bootstrap intervals.*

| Cohort | Reference-positive / complete households | Best single round, missed | Random, missed | Best minus random (pp) |
|---|---|---|---|---|
| 2021, rounds 7 / 9 / 11 | 933 / 1,443 | January: 23.9% (20.3–27.4) | 35.1% | −11.2 (−15.6 to −7.3) |
| 2021, rounds 7 / 8 / 9 / 11 / 12 | 986 / 1,387 | Late Feb – mid-Mar: 25.9% (21.6–30.0) | 41.4% | −15.6 (−19.0 to −12.3) |
| 2020, rounds 1 / 2 / 3 / 5 / 6 | 1,173 / 1,481 | June 2020: 32.1% (28.9–34.9) | 37.2% | −5.1 (−8.1 to −1.9) |

- **2021 rankings.** In the three-round cohort, April was no better than random (−1.5) and late May–June was worse (+12.7). In the five-round cohort, late May–June and June were worse than random (+10.8, +15.9).
- **2020 rankings.** December 2020 was close to random (−2.4; −5.0 to +0.1). November 2020 was the worst round (+7.9).
- **Weighting.** Using each horizon's last-round cross-sectional weight (not a panel weight) keeps the same ordering: January 19.3%, April 33.5%, late May–June 45.6%; random 32.8%.
- **Household bootstrap.** Resampling households instead of districts gives slightly narrower intervals, e.g. January minus random −13.7 to −8.8.

For the Aggarwal data (`aggarwal_fixed_schedules.csv` and the baseline outputs), January–February is the best single window in Malawi 2020: 33 of 185 reference-positive households missed (17.8%), against 55.1% at random. Liberia's best windows are May–June and November–December, both 20 of 34 missed (58.8%), against 69.6% at random.

### 5.2 Transfer tests: choose on earlier data, freeze, evaluate later

*Sources: `hfps_transfer_tests.csv`, `hfps_transfer_selection_stability.csv`, `aggarwal_july_june_test.csv` and the baseline `timing_validation.csv`.*

| Test | Training data → chosen window (training missed; selection stability) | Test-year missed: chosen vs random | Chosen minus random (95% CI) |
|---|---|---|---|
| Aggarwal Malawi, calendar 2020 → 2021 (baseline) | Jan–Feb (13.6%; 100%) | 21.6% vs 59.8% | −38.2 (−46.9 to −29.2) |
| Aggarwal Liberia, calendar 2020 → 2021 (baseline) | Mar–Apr (58.1%; 62%) | 54.5% vs 60.2% | −5.7 (−26.9 to +14.1) |
| **Aggarwal Malawi, July 2019 – June 2020 → July 2020 – June 2021 (new; all six windows are candidates)** | Jan–Feb (17.4% among 155 of 179 households; 99.6%) | 38.3% vs 59.3% (133 of 202 households; 138 villages) | **−20.9 (−27.5 to −13.6)** |
| HFPS, 2020 rounds → 2021 (reproduction) | June 2020 (32.1%) | 47.8% vs 35.1% (round 11) | +12.7 (+10.3 to +15.3) |
| **HFPS calendar-matched, group B: Jun / Dec / Apr in 2020–21 → 2023–24** | June (27.4% among 1,116 of 1,509 households; 75%) | June 2023: 39.5% vs 26.9% (443 of 556 households) | **+12.6 (+8.5 to +16.6)** |
| Same test, trained on group-B households only | June (29.6%; 52%) | same as above | +12.6 |
| **Same test, with the pandemic-onset June 2020 round replaced by June 2021** | **December** (20.8%; 100%) | Dec 2023: 14.7% vs 26.9% | **−12.3 (−14.7 to −9.8)** |
| **HFPS calendar-matched, group A: Jun / Feb–Mar** | June (23.1% vs 23.3% for Feb–Mar; 53%) | June 2023: 31.5% vs 21.7% (447 of 615 households); Feb–Mar 2024 would have missed 11.9% | **+9.8 (+6.2 to +13.8)** |

The secondary item, s8q8, behaves the same way (`hfps_transfer_tests.csv`):
- Training picked June every time.
- In group B, June 2023 missed 53.8% against 43.8% at random, while December 2023 missed 25.0%.
- In group A, June missed 44.3% against 32.4% at random, while February–March missed 20.4%.

**Interpretation.**

- **Exposure.** The 2023–24 ranking could be predicted from round-level "yes" rates printed during the audit, before any household-level computation. These are calendar-matched re-specifications, not blind tests.
- **What the tests show.** Selection from one earlier year transferred well when the training year was typical. It failed when the training data started at the pandemic onset with the first interview. That round cannot be separated into a pandemic shock and a first-interview (panel-conditioning) effect, because the panel has no refreshment sample.
- **A simple calendar rule.** "Screen in January–March", fixed in advance from published seasonal calendars, would have worked in every test where those months were available. FEWS NET, cited by Smith et al., gives January–February as the worst period for most households. It would not have been tested in the 2020 World Bank data or in the 2023–24 group-B horizon, which contain no January–March rounds.

### 5.3 Decision robustness: exact ranges and tipping points

*Sources: `hfps_decision_robustness.csv` and `aggarwal_timing_robustness.csv`. Contrast: missed share of the chosen contact minus that of a random contact. Frame: households observed at least once in the horizon. Missing screens can take any value, plus a shared budget of flipped recorded answers chosen adversarially. These are identification ranges, not confidence intervals. The solver is validated by brute force (§7).*

| Analysis | Frame households (with a missing screen) / recorded answers | Complete-case difference | Range, missing screens only | Range, plus 1% of answers flipped | Smallest number of flips that erases the advantage |
|---|---|---|---|---|---|
| Aggarwal Malawi 2021, Jan–Feb vs random of 4 | 283 (86) / 985 | −38.2 | −44.9 to −10.1 | −49.2 to −6.4 | 25 (2.5%) |
| Aggarwal Malawi, July 2020 – June 2021, Jan–Feb vs random of 6 | 291 (89) / 1,583 | −20.9 | −29.8 to −3.1 | −36.0 to +2.9 | 8 (0.5%) |
| Aggarwal Liberia 2021, Mar–Apr vs random | 146 (86) / 423 | −5.7 | −41.0 to +27.7 | — | 0 (already includes zero) |
| HFPS 2021, rounds 7/9/11, s8q7: January vs random | 1,632 (189) / 4,646 | −11.2 | −14.8 to −4.7 | −17.6 to −2.0 | 79 (1.7%) |
| HFPS 2021, rounds 7/8/9/11/12, s8q7: January vs random | 1,640 (253) / 7,730 | −10.5 | −15.0 to −2.9 | −20.2 to +2.2 | 46 (0.6%) |
| HFPS 2021, rounds 7/9/11, s8q8: January vs random | 1,632 (189) / 4,646 | −13.4 | −21.3 to +0.9 | — | 0 |

**Reading this table.** For the primary outcomes, the advantage survives *any* completion of the missing interviews. That assumption-free result is stronger than imputation. Worst-case flips of 0.5–2.5% of recorded answers can erase it.

Adversarial flips are a deliberately extreme model, not an estimate of real response error. Still, the paper should state that the ranking assumes response errors that are small and not systematically aimed at the chosen month. Without that assumption, the data cannot rule out a reversal.

### 5.4 Who is missed (exploratory)

*Source: `hfps_subgroups.csv`. HFPS rounds 7/9/11, s8q7. January minus random, missed share, with 95% district-bootstrap intervals.*

| Group | Reference-positive / complete households | January missed | Random missed | Difference |
|---|---|---|---|---|
| All | 933 / 1,443 | 23.9% | 35.1% | −11.2 (−15.6 to −7.3) |
| Rural | 629 / 909 | 21.3% | 34.4% | −13.1 (−18.4 to −7.9) |
| Urban | 304 / 534 | 29.3% | 36.6% | −7.3 (−12.3 to −3.9) |
| Wealth quintile 1 (poorest) | 84 / 95 | 11.9% | 29.0% | −17.1 (−24.7 to −9.6) |
| Wealth quintile 5 (richest) | 200 / 477 | 36.0% | 39.8% | −3.8 (−9.0 to +3.2) |
| Q1 minus Q5, in the difference | — | — | — | −13.2 (−23.5 to −4.3) |
| Southern / Central / North region | 404 / 388 / 141 reference-positive | — | — | −14.1 / −9.9 / −6.6 (North interval includes zero) |

For the secondary item, the Q1 minus Q5 gap is −12.9 (−32.1 to +6.0).

**Caveats.** These are 11 groups × 2 items with no multiplicity adjustment. They cover complete households only, are unweighted, and use coarse clusters. The share of households ever positive also differs sharply by wealth: 88% in Q1 against 42% in Q5. So the poorest group's reference set is close to saturated, and its random benchmark is lower for mechanical reasons.

**Reading.** The data suggest that a January contact mainly helps identify hunger in poorer and rural households, while for the richest the timing barely matters. Treat this as a hypothesis to confirm in other data.

### 5.5 Contacts, yield and the second contact

*Sources: `aggarwal_fixed_schedules.csv`, `hfps_fixed_schedules.csv`, `hfps_second_contact.csv`, `aggarwal_second_contact.csv` and `hfps_model_vs_rule.csv`. Identified means positive at the retained contact(s), among complete households. All comparisons are in-sample.*

| Cohort | Random one contact | Best one contact | Best two contacts | Random two contacts | Gain from the second contact (per 100 extra contacts) |
|---|---|---|---|---|---|
| Aggarwal Malawi 2020 (per 100 households) | 36.6 | Jan–Feb: 67.0 | Jan–Feb + Mar–Apr: 76.2 | 55.5 | +9.3 |
| HFPS 2021, rounds 7/9/11, s8q7 (per 100 households) | 42.0 | January: 49.2 | Jan + Apr: 60.8 | 56.7 | +11.6 |

Per completed contact, the yield is 49–67 identified per 100 for the best single contact, against 30–38 for the best pair. In Malawi, one well-timed contact identifies more than two randomly timed ones (67.0 against 55.5).

**Second contact.** Which households that were negative at the January contact should be re-contacted? The budget is the number of warning-sign households. A warning sign means "yes" to any of FIES items 1–6 (World Bank data) or HHS = 1 (Aggarwal data).

| Analysis | Re-contacted | Warning-sign rule | Poorest first | Random | Warning minus random (95% CI) |
|---|---|---|---|---|---|
| HFPS 2021, s8q7: January, then rounds 9 and 11 | 386 of 733 negatives | 44.6 per 100 (77% of later positives captured) | 39.2 | 30.4 | +14.1 (+11.0 to +17.3) |
| HFPS 2021, s8q7: January, then four later rounds | 371 of 706 | 62.0 | 51.9 | 43.2 | +18.8 (+15.8 to +21.5) |
| Aggarwal Malawi 2020, HHS = 1 at Jan–Feb, then five later windows | 41 of 75 | 61.0 | 41.5 | 44.0 | +17.0 (+6.6 to +28.4) |
| Aggarwal Malawi 2021 | 19 of 117 | 31.6 | 21.1 | 18.8 | +12.8 (−4.7 to +32.9) |
| Aggarwal Liberia, 2020 and 2021 | 18 and 27 | 55.6 and 29.6 | 55.6 and 22.2 | 44.1 and 25.5 | Both intervals include zero |

**Model versus rule.** A logistic model was trained only on a 2020 version of the same problem (first contact July 2020; later rounds August and November 2020). Its inputs were the six milder items, wealth, urban residence and region. It was applied unchanged to 2021.

- **Same budget as the rule:** every rule picks the same households by construction.
- **Half that budget (193 re-contacts):** counting the milder "yes" answers gives 52.9 per 100, the model 52.3, the any-"yes" rule 44.6 and random selection 30.4. For s8q8 the figures are 17.1, 18.4, 13.9 and 10.8.

The model adds nothing material over a transparent count, so no machine-learning model is recommended. This agrees with Smith et al. (2026), who found that past food-security measures forecast better than asset indices.

### 5.6 Saturation of "ever positive"

*Source: `hfps_saturation.csv`. 1,294 households complete in all ten 2020–21 rounds.*

The share ever answering "yes" to s8q7 rises from 53.7% after one round to 74.2% after three, 80.8% after six and 83.4% after ten; for s8q8 it rises from 25.0% to 48.3%. Over long reference periods, "reference positive" covers most of the population. "Missed share" then stops describing a targeting error and becomes a property of the observation design. Short, explicitly stated horizons are needed.

## 6. Evaluation of the candidate research paths

| Path | What was tested | Verdict |
|---|---|---|
| A. External validation of practical schedules | World Bank panel; calendar-matched transfer to 2023–24; Aggarwal July–June re-specification | **Partly achieved.** Independent replication of the direction, but no blind test, a different instrument and no documented programme calendar to compare against |
| B. Timing, frequency and decision value | Yield per 100 households and per 100 contacts; second-contact increments; logged call attempts | **Achieved descriptively.** No monetary cost can be documented for the World Bank survey or the trial, so none is reported |
| C. Who is missed | Urban/rural, wealth, region | **Exploratory signal only.** Larger advantage for poorer and rural households; not confirmatory |
| D. Transfer failure and stability | Pandemic-onset training round versus a typical year | **Useful, honest negative result**, with the round-1 shock and first-interview effect confounded |
| E. Decision robustness | Exact ranges for the timing contrast; tipping points | **Achieved.** New for this question; the advantage is robust to missing data and fragile to adversarial error |
| F. Different measures | FIES items 7 and 8; HHS-analogue score in 2024 | **Triangulation only.** Same direction for both items; HHS-analogue concordance 86–98% |
| G. Additional data | MIRA/RFMS, Madagascar, Myanmar, other HFPS countries | **Blocked or not obtained.** See `03_DATASET_INVENTORY_AND_ACCESS_LEDGER.md` |
| H. Own ideas | (i) Second-contact warning-sign rule with a model compared over time; (ii) January–March calendar rule; (iii) saturation of "ever positive"; (iv) a generic exact solver for any screening contrast | (i)–(iii) give practical, modest results; (iv) is a reusable method contribution |

Ideas rejected or not pursued:
- **Satellite or weather data:** no decision question that the survey data cannot already answer. Smith et al. show satellite data underperform when outcome data are scarce.
- **A pooled cross-dataset estimate:** the instruments differ.
- **Monetary cost-effectiveness:** no documented per-contact costs.
- **Region-level schedule optimisation:** too few households per region, and it would invite overfitting.

## 7. Methods and validation

- **Estimands.**
  - Missed share = missed reference positives ÷ reference positives.
  - Identified per 100 households = identified ÷ complete households × 100.
  - Identified per 100 contacts = identified ÷ (contacts per household × households) × 100.
  - The random benchmark is computed exactly from the hypergeometric formula C(n−K, m) / C(n, m).
- **Uncertainty.** Percentile bootstrap, 2,000 draws, seed 20261027. Whole villages are resampled for the Aggarwal data; districts (31), and separately households, for the World Bank data. All statistics in a table share the same draws, so differences are paired. Zero-denominator draws are counted, and there were none in the main analyses.
- **Exact ranges** (`history_bounds.py`). Every household history reachable by completing missing screens, or by flipping recorded answers within a budget, is considered. The method is Dinkelbach iteration on the ratio of sums, solved exactly as a multiple-choice knapsack over the integer flip budget. Each household is represented by its best value at each flip count, and a certificate F(λ*) = 0 is checked at termination. Validation:
  - Equal to exhaustive brute force on 180 random small instances: five contrasts × budgets 0–2 × 12 instances.
  - Equal to the baseline project's two independent solvers wherever their targets coincide.
  - Ranges nest as the budget grows; the tipping-point search is checked at B and B − 1.
- **Leakage control.** The selection function receives only training data. A test verifies that changing the test-year data leaves the choice and the training statistics unchanged.
- **Reproducibility.** All 20 investigation CSV files are byte-identical across two full runs. The test suite has 166 tests, all passing locally: the 134 baseline tests plus 32 new ones. Lint is clean, and the release-safety audit passes on 232 candidate files.

## 8. How to reproduce

```powershell
cd household-hunger-screening   # the cloned repository folder
git switch investigation/strengthen-contribution
# 1. Place the World Bank archive at data\raw\MWI_2020-2024_HFPS_v20_M_Stata.zip (download it with your own
#    Microdata Library account; it is not redistributed), then extract it:
Expand-Archive data\raw\MWI_2020-2024_HFPS_v20_M_Stata.zip data\raw\worldbank_mwi_hfps_v20\extracted
# 2. Baseline study outputs are needed by the Aggarwal extensions (already present, or regenerate):
.\.venv\Scripts\python.exe -m hunger_screening.cli analysis --no-download
# 3. Investigation (checks the World Bank checksum first; about 40 s):
.\.venv\Scripts\python.exe -m hunger_screening.cli investigation
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\check_release_safety.py
```

**Outputs:**
- `data/public_aggregates/investigation/`: 20 CSV files and one JSON summary.
- `figures/investigation/`: figures I1–I5 in PNG (300 dpi), SVG and PDF.

## 9. Discrepancies and corrections

- **Rounds 7→8 interview gaps under 30 days.** I find 4.3% of households with both dates (65 of 1,508); ChatGPT Work reported 5.6%. I computed calendar-day differences between the two rounds' interview dates. The cause of the difference is unknown, because the earlier script is not available.
- **A label error in my own first draft.** The Aggarwal second-contact rows were initially labelled "milder item"; the rule is HHS = 1. Corrected before any output was used.

## 10. Recommendation

Publish an honest applied paper built on both Malawi panels (options in `06_MANUSCRIPT_OPTIONS.md`), with Liberia as supplementary material. Make **timing at a fixed contact budget** the central question. Report the transfer-failure result and the tipping points prominently.

A selective policy journal becomes a realistic stretch only with one of the following, together with the confirmations listed in `07_REQUIRED_WORK_BEFORE_SUBMISSION.md`:

- a **protocol-locked, genuinely untouched external test**, for example other LSMS-HFPS countries whose food-security outcomes nobody on this project has examined; or
- **MIRA monthly HHS data** obtained through a data-sharing agreement.
