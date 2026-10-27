# Household hunger screening: all findings

*Author: Omoding Isaac (MSc Data Science and Analytics; Ministry of Health, Uganda). Compiled 27 October 2026 and updated after the external review (`REVIEW_RESPONSE.md`). It covers the reproduction of the original study, the World Bank Malawi replication and the locked five-country test. Every number was computed from the source data in this project. Detailed reports are under `reports/` and `reports/investigation/`. Aggregate results are under `data/public_aggregates/`.*

**How to read the uncertainty:**
- **CI** means a 95% cluster-bootstrap confidence interval. It reflects sampling noise.
- **Range** means an exact identification range: the best and worst values possible under the stated assumptions. It is *not* a confidence interval.
- **Missed share** means the share of households that reported hunger at least once among the observed interviews but that a reduced schedule would not catch.

---

## 1. Bottom line

1. **The original analysis is correct.** Every earlier number reproduces exactly from the raw data, and the interview dates confirm the "call every two months" design.
2. **Hunger is intermittent.** Most households that report hunger do so in only some interviews, so infrequent screening misses many of them. In Malawi one interview out of six misses about 55%; in Liberia, about 70%.
3. **In Malawi, timing matters.** In two separate Malawi panels, one contact in January–March missed far fewer households than a randomly timed contact, in every year where those months were observed.
4. **That timing advantage does not transfer as a general rule.** A test locked in advance in five other countries found that contacting households in the FEWS NET lean season did **not** beat random timing. In 2020–21, reported hunger declined round after round, and that trend swamped seasonality.
5. **A simple second-contact rule does transfer.** Re-contacting households that said "yes" to a milder hunger question finds more hungry households than re-contacting at random. This held in Malawi and in all 3 testable horizons of the locked test. A statistical model did no better than simply counting the milder "yes" answers.
6. **The results have limits.**
   - They survive any pattern of missing interviews.
   - Small amounts of worst-case answer error (0.5–2.5% of answers) could erase them. Random answer error at hypothetical rates up to 20% did not, in Malawi.
   - They are not national prevalence figures and say nothing about the effects of running fewer interviews in a real programme.
7. **Recommended paper:** "when to screen" is a local, year-specific question; a simple second-contact rule is portable. Good fits: *Global Food Security*, *Food Security*. *Food Policy* is a realistic stretch because of the locked test. This describes fit, not chances of acceptance.

---

## 2. Original study: reproduction and results

**Source:** Aggarwal et al. (2022), *PLOS ONE* 17:e0271488, supporting data, licensed CC BY 4.0.
- **Archive check:** SHA-256 `de2ae59d…66bb`, 9,098,158 bytes; matches the earlier record.
- **Outcome:** Household Hunger Scale (HHS) of 2 or more, in control households of a trial in rural Liberia and Malawi.

### 2.1 Data and design checks

- **Records:** 4,744 phone interviews. The baseline frame has 503 households (Malawi 297, Liberia 206); 483 households in 252 villages were interviewed at least once. All 22 integrity checks pass.
- **HHS score: standard scoring, checked.** The score equals the number of "yes" answers in 4,698 of 4,740 records, and exceeds it by 1 to 3 in the other 42. It is never below it, which fits standard FANTA scoring (1 point for rarely or sometimes, 2 for often).
  - It is built from the standard "no food of any kind in the house" item; the do-file's "skipped a meal" caption is a mislabel.
  - The frequency answers and the phone questionnaire are not public. Confirm with the source authors.
  - HHS 2 or more is the standard moderate-or-severe threshold, reached here almost always through two or more experiences reported rarely or sometimes.
- **One duplicate** household-window (Liberia, March–April 2020). It affects only the "any hunger" analysis.
- **Call schedule verified from dates:**
  - 94% of households stay in odd or even months throughout; the split is even (Malawi 150 / 147, Liberia 93 / 93).
  - The median gap between interviews is 61 days, and under 0.2% of gaps are shorter than 30 days.
  - So two-month windows are the right unit. With 30-day recall, about half the calendar is never observed.
- **Panel start:** Malawi interviews run from July 2019 to August 2021; Liberia from January 2020 to October 2021.

### 2.2 Cohorts (households with all six 2020 windows observed)

| | Malawi | Liberia |
|---|---|---|
| Complete households | 227 (76% of frame) | 67 (33%) |
| Of these, hungry at least once (HHS ≥ 2) | 185 | 34 |
| Villages | 140 | 47 |

### 2.3 Missed share when interviews are kept at random (CI in brackets)

| Interviews kept (of 6) | Malawi | Liberia |
|---|---|---|
| 1 | 55.1% (51.6–58.7) | 69.6% (63.9–75.0) |
| 2 | 31.9% (28.3–35.6) | 47.5% (40.2–54.4) |
| 3 | 18.2% (15.2–21.4) | 30.7% (24.0–37.5) |

- **Intermittency:** 75% of Malawi and 94% of Liberia's ever-hungry households were hungry in only one to three of the six windows.
- **Severe hunger (HHS ≥ 4):** degenerate. Every severely hungry household was severe in exactly one window.
- **Attrition:** dropout is linked to gender, age and roof type in Liberia, and to roof type and spending in Malawi. Weighting for it barely changes the one-interview estimates (Malawi 54.9%, Liberia 70.3%).

### 2.4 Robustness ranges (one interview kept)

| | Malawi | Liberia |
|---|---|---|
| Missing windows could be anything | 50.8–59.3% | 39.8–78.6% |
| Plus up to 5% of recorded answers wrong (hypothetical) | 39.6–65.0% | 25.1–82.5% |

### 2.5 Timing: one window chosen on 2020 data, tested on 2021

| | Malawi | Liberia |
|---|---|---|
| Window chosen (stability across 2,000 resamples) | January–February (100%) | March–April (62%) |
| 2021 missed, chosen window vs random | 21.6% (22 of 102) vs 59.8% | 54.5% vs 60.2% |
| Difference (CI) | **−38.2 points (−46.9 to −29.2)** | −5.7 (−26.9 to +14.1), inconclusive |
| Households complete in both years | 20.2% vs 59.8% (171 households, 89 hungry) | 61.5% vs 63.5% (13 hungry) |

### 2.6 New analyses of the same data (this investigation)

- **July–June year test (Malawi).** All six windows were candidates in both the training and the test year.
  - Training on July 2019 – June 2020 picked January–February (17.4% missed among 155 of 179 households; chosen in 99.6% of resamples).
  - In July 2020 – June 2021 it missed 38.3% against 59.3% at random, a difference of **−20.9 points (−27.5 to −13.6)**. November–December did about as well (37.6%).
- **Exact robustness of the Malawi 2021 timing result.**
  - The range over every possible completion of missing windows is −44.9 to −10.1 points, so the advantage survives any missing-data pattern.
  - Worst-case errors in **25 recorded answers (2.5%)** could erase it. In the July–June test, 8 answers (0.5%) could.
  - Liberia's range already includes zero.
- **Contacts (Malawi 2020, per 100 households):**

  | Schedule | Households identified |
  |---|---|
  | One random contact | 37 |
  | One January–February contact | 67 |
  | Two random contacts | 55 |
  | January–February + March–April (best pair, chosen in-sample) | 76 |

  One well-timed contact beats two random ones. The second contact adds about 9 identified households per 100 extra calls.
- **Best pair tested out of time.** Chosen on July 2019 – June 2020, the best pair is November–December + January–February (not the in-sample January–February + March–April). In July 2020 – June 2021 it missed 15.0%, against 36.4% for a random pair: −21.4 points (−27.7 to −14.5).
- **Second contact (Malawi 2020).** Re-contacting households with HHS = 1 at the first contact gave 61.0 later positives per 100 re-contacted, against 44.0 at random (difference +17.0; +6.6 to +28.4). Malawi 2021 and Liberia were inconclusive.

### 2.7 Responses to the external review (details in `REVIEW_RESPONSE.md`)

- **Evidence classes.**
  - *Exploratory, in-sample:* the 2020 rankings and the best 2020 pair.
  - *Out-of-time but not blind:* the 21.6% and 38.3% results and the frozen pair.
  - *Calendar-based sensitivity, not blind:* the FEWS NET window.
  - *Genuinely prespecified:* only the five-country test.
- **The 21.6% and 38.3% use different references.**
  - 21.6%: four windows, January–August 2021, 102 reference positives.
  - 38.3%: six windows, July 2020 – June 2021, 133 reference positives.
- **Calendar-based sensitivity** (FEWS NET lean season: Malawi December–February, so January–February; Liberia June–August, so July–August):
  - **Malawi:** beats random in every horizon (−37.3, −31.7 and −20.9 points against six-window references; −38.2 against four).
  - **Liberia:** does **not** (+9.8, +3.7, −5.7; all intervals include zero).
- **Single-window positives.** 45 of 185 (Malawi) and 16 of 34 (Liberia). Without them the one-screen miss falls to 46.1% and 57.4%, and the Malawi January–February advantage remains (−33.2; −39.8 to −26.5).
- **Liberia bounds.** Excluding the 24 never-contacted households changes the one-screen range from 39.8–78.6% to 48.6–77.9%.
- **Answer error.**
  - No published HHS test-retest or misclassification rate was found.
  - In World Bank Malawi rounds less than 30 days apart, answers differed in 23.9% ("hungry but did not eat") and 10.0% ("whole day") of 1,485 pairs. This is *discordance*, mixing real change, recall and reporting error; it is not an error rate.
  - With random flips at hypothetical rates of 5%, 10% and 20%, January–February stayed better than random in at least 999 of 1,000 simulations.

---

## 3. Independent replication: World Bank Malawi phone survey (2020–2024)

**Source:** *Malawi High-Frequency Phone Survey 2020–2024*, version 20, doi:10.48529/s2n6-9f47. Archive SHA-256 `5dfbd541…9c16`.
- **Size:** 15 food-security rounds, 20,610 records, 1,729 households.
- **Panel structure:** all households enter in round 1, with no refreshers. Rounds 19–21 alternate sample groups.
- **Measure:** FIES items with 30-day recall. Primary: "hungry but did not eat". Secondary: "whole day without eating". **These are not the HHS.**
- **Survey design:** no panel weights and no cluster IDs in the public files, so intervals resample districts or households and are approximate.

### 3.1 Reproduction of the ChatGPT Work figures

All figures reproduced exactly except one:
- 1,443 complete households, 933 hungry at least once.
- Missed share: January 23.9%, April 33.7%, late May–June 47.8%; random 35.1%.
- Second contact (January + April) adds 11.6 per 100 households.
- Missing-data range −14.8 to −4.7 points.

The exception: round 7 → round 8 gaps under 30 days are 4.3% (65 of 1,508), not 5.6%.

### 3.2 Timing within years ("hungry but did not eat")

| Cohort | Best single round | Random | Difference (CI) |
|---|---|---|---|
| 2021, January / April / late May–June (1,443 households) | January 23.9% | 35.1% | −11.2 (−15.6 to −7.3) |
| 2021, five rounds (1,387 households) | late Feb – mid-Mar 25.9% | 41.4% | −15.6 (−19.0 to −12.3) |
| 2020, five rounds (1,481 households) | June 2020 (pandemic onset) 32.1% | 37.2% | −5.1 (−8.1 to −1.9) |

- **November and December were inconsistent.** November 2020 was the worst round of 2020 (+7.9). December 2020 was close to random (−2.4).
- **Weighting** with each round's cross-sectional weights gives the same ordering.

### 3.3 Transfer: choose on earlier data, test later

| Test | Training chose | Later result vs random |
|---|---|---|
| 2020 → 2021 | June 2020 | **+12.7 points worse** (+10.3 to +15.3) |
| June/December/April, 2020–21 → 2023–24, group B | June | **+12.6 worse** (+8.5 to +16.6); December would have been −12.3 better |
| Same test, with the pandemic-onset June 2020 round replaced by June 2021 | December (100% stable) | **−12.3 better** (−14.7 to −9.8) |
| June / February–March, 2020–21 → 2023–24, group A | June (unstable, 53%) | +9.8 worse; February–March would have been −9.8 better |

**Lesson:** picking the month from data fails when the training period starts with an unusual shock or a first interview. These were *not* blind tests, because per-round rates had been seen beforehand.

### 3.4 Robustness, subgroups, yield, measurement

- **Robustness.** January's advantage survives any missing-data pattern (range −14.8 to −4.7). Worst-case errors in 79 answers (1.7%) erase it, or 46 answers (0.6%) across all five 2021 rounds. For "whole day without eating", missing data alone can reach zero.
- **Who is missed (exploratory).** The January advantage is larger for:
  - rural households: −13.1, against −7.3 urban;
  - the poorest fifth: −17.1, against −3.8 for the richest. The gap is −13.2 (−23.5 to −4.3).

  These come from 22 unadjusted comparisons.
- **Yield (per 100 households).** January alone 49.2; January + April 60.8; one random contact 42.0; two random 56.7.
- **Second contact.** Re-contacting January negatives with any milder "yes" gave 44.6 later positives per 100 re-contacted, against 30.4 at random and 39.2 when choosing the poorest. The difference is +14.1 (+11.0 to +17.3).
- **Model versus rule.** At half that budget, counting milder "yes" answers gave 52.9, a logistic model trained on 2020 gave 52.3, and random gave 30.4. The model adds nothing, so no machine learning is needed.
- **HHS-style score (2024 only).** 86–90% of households answering "yes" to "hungry but did not eat" score HHS-style ≥ 2, and 98% of those scoring ≥ 2 answered "yes".
- **Saturation.** Ever answering "yes" rises from 54% after one round to 83% after ten. Long reference periods make "missed share" less meaningful, so short horizons are needed.

---

## 4. Locked five-country test (World Bank LSMS phone surveys)

**How it was run:** the protocol was committed in `8d33f4d` (SHA-256 `23afabbe…5ba6d`) **before** any data were downloaded. The lean-season months were fixed in advance from FEWS NET typical-year calendars. The archives were downloaded by the study owner and their checksums recorded.

| Panel | Usable horizons |
|---|---|
| Burkina Faso | 2020–21 |
| Uganda | 2020–21; 2022–23 (no lean-season round, so not testable for H1) |
| Ethiopia | 2019–20 (excluded from H1 by protocol: no single national lean season) |
| Nigeria (both panels) | none (only 2 food-security rounds per year) |
| Tanzania | none (module asked only of a subsample; round 9 file damaged in the official release) |

### H1: lean-season calendar rule against random — **contradicted**

| Horizon | Rule picks | Rule missed | Random | Difference (CI) |
|---|---|---|---|---|
| Burkina Faso 2020–21 | July 2021 | 76.9% | 66.0% | **+10.9 (+6.9 to +14.7)** |
| Uganda 2020–21 | March 2021 | 62.3% | 59.0% | +3.4 (−3.9 to +8.8) |
| *Sensitivity:* Burkina Faso 2022–23, two sample groups | July / September 2023 | 24.2% / 24.7% | 56.5% / 56.7% | −32.3 / −32.1 |
| *Sensitivity:* Uganda 2023–24, one group | March 2024 | 61.8% | 54.8% | +7.0 (−0.8 to +14.7) |

**Why it failed (post-hoc exploratory).** In every 2020–21 horizon the earliest round was the best single contact:
- Burkina Faso: November 2020.
- Ethiopia: April 2020.
- Uganda: August 2020.

Reported hunger then fell round by round, which may be pandemic recovery or people getting used to the survey. In the calmer 2022–23 Burkina Faso data, the lean-season rounds had 28–29% "yes" against about 10% in other rounds.

### Other hypotheses

- **H2, data-driven transfer:** one testable pair (Uganda); inconclusive at −3.3 (−9.8 to +3.7).
- **H3, second-contact rule: supported.** Burkina Faso +6.2 (+4.8 to +7.8); Uganda 2020–21 +6.5 (+4.4 to +8.8); Uganda 2022–23 +1.5 (−1.8 to +5.3). That is 3 of 3 positive, and 6 of 7 including the sensitivity groups.
- **H4, rural vs urban:** the rule did relatively better for rural households (Burkina Faso −10.8, from −19.2 to −2.6; Uganda −6.2, inconclusive). Exploratory.

**Deviations from the protocol (all documented; none changes a decision):**
- D1: items were identified by their standard FIES position, because labels were truncated or in French.
- D2: split-sample groups were analysed as separate panels, as a sensitivity analysis only.
- D3: Tanzania round 9 was excluded because the file is damaged.
- D4: interview dates came from different source variables in different countries.
- D5: a coding fix to the pandemic-onset flag.

---

## 5. Literature and novelty

| Work | Overlap with ours | What ours adds |
|---|---|---|
| Zhu, Gupta, Doan & Michuda 2026, *Food Security* (financial diaries, India) | A single survey round misclassifies 15–48% of households | Timing at a fixed contact budget; out-of-time tests; exact ranges; African panels |
| Smith, Christian, Dillon, Lentz, Michelson & Upton 2026, *Food Policy* (MIRA monthly HHS, southern Malawi) | Hunger peaks December–February; forecasting | They leave "optimal monitoring frequency" open; we test it |
| Wollburg, Markhof & Jolliffe 2025, draft (World Bank phone surveys, including Malawi) | "Ever food insecure" far exceeds point prevalence | Timing, transfer and robustness |
| Deisemann et al. 2024, slides | Seasonality explains only 1–5% of FIES variance | Consistent with our finding that seasonal rules often fail |
| McDonough & Millimet 2024, *AJAE* | Partial identification under measurement error (US) | Applied to a screening-schedule contrast, with tipping points |
| People in Need IndiKit guidance | Already recommends surveying in the lean season | We show when that advice fails |
| D'Souza & Tandon 2015, ERS *Amber Waves* (Bangladesh) | Household measures misclassify individuals (within-household sharing) | Complementary: misclassification over time, not within households |

**Novelty verdict:** a modest contribution, now strengthened by the locked test. The paper cannot claim to be "first".

---

## 6. Data access

| Dataset | Status |
|---|---|
| Aggarwal S1 Data | Used |
| World Bank phone surveys (Malawi + 5 countries) | Used; aggregates only, cited with DOIs |
| MIRA monthly HHS (CRS / Cornell) | Not public; needs a request (not sent) |
| Malawi RFMS | Not public; overlap with MIRA unknown |
| Myanmar household welfare survey | Not obtained (the download form asks for your identity) |
| Tanzania round 9 | Damaged in the Stata release; a CSV version could be checked |

---

## 7. What can and cannot be claimed

**Can claim:**
- Household hunger in these panels is intermittent.
- An exactly calculated share of hungry households is missed as interviews are cut.
- In Malawi, January–March contacts outperformed random timing in every observed year and in two independent panels.
- Choosing the month from one earlier year can fail after shock periods.
- A FEWS NET lean-season calendar rule did not transfer to Burkina Faso or Uganda in 2020–21 (locked test).
- A simple second-contact warning rule transfers.

**Cannot claim:**
- national or yearly prevalence, or IPC phases;
- causal effects of interviewing less;
- improved assistance or health;
- cost-effectiveness;
- an optimal schedule;
- that the World Bank items are the HHS;
- being first;
- generalisation of the Malawi timing result.

---

## 8. Main limitations

- **Instruments.** Phone surveys only. The HHS (Aggarwal) and FIES single items (World Bank) cannot be pooled.
- **Reference.** "Hungry" means positive in at least one observed interview, not true hunger. Long horizons saturate.
- **Selection.** Analyses use complete-case cohorts. Attrition is related to household characteristics. The World Bank surveys have no panel weights or cluster IDs, so their intervals are approximate.
- **Confounding.** Survey round and calendar time cannot be separated, including the first-round and pandemic effects.
- **Response error.** Small worst-case answer errors can reverse the timing rankings.
- **Blindness.** Malawi and Liberia results are not blind, and only part of the five-country test was testable.

---

## 9. Recommended paper and next steps

**Working title:** *When to ask about hunger: seasonal timing helps in Malawi but does not transfer as a calendar rule, while a simple second-contact rule does.*

**Structure:**
1. Malawi evidence (two panels) with its limits.
2. The locked five-country test.
3. The second-contact rule.
4. Liberia and secondary items in the supplement.

**Before submission:**
- **Design and literature.**
  - Confirm the Aggarwal call design from its documentation or with the authors.
  - Read McDonough & Millimet and Guthoff et al. in full.
  - Check the publication status of Wollburg et al.
- **Review.**
  - Statistical review of the exact-range solver and the bootstrap choices.
  - Ethics determination.
- **Paperwork.**
  - Confirm the HHS questionnaire with the source authors.
  - Add the co-researchers to `CITATION.cff`.
  - Draft the manuscript.
- **Optional.**
  - The Tanzania CSV.
  - A data request for MIRA's monthly hunger-scale data.

---

## 10. Project state and quality checks

- **Branch.** All work is merged into `main` on GitHub, with no force-push.
- **Checks.**
  - 176 automated tests pass.
  - Lint is clean.
  - The release-safety audit passes: no raw data, IDs or credentials on GitHub.
  - Results are byte-identical across repeated runs.
  - The exact solver matches brute-force enumeration.
- **Kept local only (gitignored):** all microdata, `data/raw/`, `data/interim/` and `logs/`.
- **Security.** Rotate the World Bank password. The temporary copy was deleted and it is not in the repository.
