# Response to the external review (27 October 2026)

*Author: Omoding Isaac (MSc Data Science and Analytics; Ministry of Health, Uganda). Analyses were run with AI assistance (Claude Code); see `docs/DEVELOPMENT_LOG.md`. New outputs are in `data/public_aggregates/review/`, code in `src/hunger_screening/review_responses.py`, tests in `tests/test_review_responses.py`.*

This document covers both rounds of review:
- the first review of the repository, and
- the follow-up that corrected parts of my first response (HHS scoring, the interpretation of discordance, and the "a priori" wording).

Every analysis requested is reported, including the ones that did not support the hypothesis.

## Evidence classes (how strong each Malawi timing result is)

| Class | What it means | Results in this class |
|---|---|---|
| **Exploratory, in-sample** | Window or schedule chosen and evaluated on the same data | 2020 single-window ranking (January–February 17.8% missed against 55.1% at random, six windows); best two-window pair in 2020 (January–February + March–April, 6.5% missed) |
| **Out-of-time, not blind** | Chosen on an earlier period, frozen, evaluated on a later period, but the later data had already been seen by the investigators | 2020 → 2021, four-window reference: **21.6%** missed (22 of 102) against 59.8%. July 2019 – June 2020 → July 2020 – June 2021, six-window reference: **38.3%** missed (51 of 133) against 59.3%. The frozen best pair (below). The World Bank Malawi transfer tests |
| **Calendar-based sensitivity, not blind** | Window fixed from an external source (FEWS NET typical-year lean season), applied after the exploratory findings | January–February (Malawi) and July–August (Liberia) in every available horizon (below) |
| **Genuinely out-of-sample and prespecified** | Protocol locked before the data existed locally | Only the five-country test (`reports/investigation/10_*`, `11_*`). The calendar rule was **contradicted**; the second-contact rule was **supported** |

**Denominators.** The 21.6% and 38.3% figures answer different questions and must not be compared directly:

| Figure | Reference | Households (reference-positive) |
|---|---|---|
| 21.6% | Four observed windows, January–August 2021 | 197 (102) |
| 38.3% | Six observed windows, July 2020 – June 2021 | 202 (133) |

A six-window reference gives a household more chances to be positive outside January–February. That is why 38.3% is higher.

## Issue-by-issue response

### 1. Is the HHS the standard HHS?

**Finding: the supplied score is consistent with standard HHS scoring and is built from the standard items.** The outcome is not redefined.

- **Scoring pattern.** In 4,698 of 4,740 records with all three items, the score equals the number of "yes" answers. In the other 42 it exceeds that number by 1 to 3, and it is never below it (`hhs_scoring_check_records.csv`).
  - Under standard FANTA scoring, each "yes" scores 1 if rarely or sometimes and 2 if often, so the excess equals the number of "often" answers.
  - The pattern therefore fits standard scoring with "often" reported about 1% of the time.
- **Item source.** The score matches a count built from `i3_1_nofood_4w` ("During the past 4 weeks, was there ever no food to eat of any kind in your house…", the standard first HHS question) in 99.1% of records.
  - A count built from the separate skipped-meal variable `i3_1_skip_4w` matches in only 74.5%.
  - That version would require scores *below* the yes count in 421 records, which standard scoring cannot produce.
  - The do-file and `table1.dta` caption "skipped a meal" is a presentation mislabel on the no-food variable.
- **Source article.** It describes a six-question HHS ranging from 0 to 6.
- **What could not be verified.** The frequency follow-up answers are not in the public supplement, so the 42 elevated scores cannot be reconciled answer by answer. The phone questionnaire is not in the supplement either.
- **Remaining step:** confirm the questionnaire with the source authors.
- **Sensitivity.** Rebuilding the outcome as "two or more of three hunger experiences" changes the reference status of 1 Malawi household and none in Liberia, and leaves the frontier unchanged to three decimals (`hhs_scoring_frontier_comparison.csv`).
- **Wording for the paper.**
  - HHS ≥ 2 is the standard moderate-or-severe threshold. In these data it is reached almost always through two or more hunger experiences reported rarely or sometimes, because "often" answers are rare.
  - Severe hunger (HHS ≥ 4) is too sparse for analysis (26 records).

### 2. Malawi timing and the lean season

**Calendar-based sensitivity analysis.** The window is fixed from FEWS NET typical-year calendars:
- Malawi lean season December–February, giving **January–February**.
- Liberia June–August, giving **July–August**.

This was done after the exploratory findings, so it is not blind and not prespecified. File: `calendar_lean_season_sensitivity.csv`.

| Horizon (reference windows) | Malawi: January–February missed vs random (95% CI) | Liberia: July–August missed vs random (95% CI) |
|---|---|---|
| Calendar 2020 (6) | 17.8% vs 55.1%: −37.3 (−43.6 to −30.6) | 79.4% vs 69.6%: +9.8 (−6.8 to +23.6) |
| July 2019 – June 2020 (6) | 17.4% vs 49.1%: −31.7 (−38.0 to −25.9) | — (Liberia starts January 2020) |
| July 2020 – June 2021 (6) | 38.3% vs 59.3%: −20.9 (−27.5 to −13.6) | 72.2% vs 68.5%: +3.7 (−14.5 to +24.4) |
| Calendar 2021, January–August only (4) | 21.6% vs 59.8%: −38.2 (−46.5 to −29.6) | 54.5% vs 60.2%: −5.7 (−26.3 to +11.8) |

- **Malawi:** the calendar window outperforms random in every horizon, including all three six-window references, where November–December can compete.
- **Liberia:** the calendar window does **not** outperform random. This is consistent with the five-country test.
- **README:** the four-window 21.6% no longer sits next to the six-window headline without its reference.

### 3. Intermittency versus noise

`single_window_positives.csv`:
- **Malawi:** 45 of 185 reference positives are positive in only one window. Of those, 26 scored exactly 2 there, at the threshold, and 19 scored 3 or more.
- **Liberia:** 16 of 34 (12 at exactly 2).
- **Persistent-only reference** (households positive in at least two windows):
  - The one-random-screen miss falls from 55.1% to 46.1% (Malawi) and from 69.6% to 57.4% (Liberia). Single-window positives inflate the frontier.
  - January–February still beats random in Malawi: −33.2 (−39.8 to −26.5).

### 4. Error budgets: anchoring and random error

- **No published reliability figure exists for the HHS.** I found no test-retest or misclassification statistics; the FANTA validation report (Deitchler et al. 2010) has none. No budget is presented as an estimated error rate.
- **Empirical observation (not an error rate).** In the World Bank Malawi survey, 1,485 households interviewed in rounds 11 and 12 less than 30 days apart, so with mostly overlapping 30-day recall periods, gave different answers in:
  - **23.9%** of pairs for "hungry but did not eat";
  - **10.0%** for "whole day without eating".

  This is **discordance**. It mixes real change in circumstances, recall differences, reporting behaviour and measurement error, and without further assumptions it is neither a misclassification probability nor a bound on one. It also concerns FIES items, not the HHS (`recall_overlap_discordance.csv`).
- **Random-error simulation** (`random_error_simulation.csv`). Observed answers were flipped at random at hypothetical rates of 5%, 10% and 20%, 1,000 simulations each. January–February stayed better than random in at least 999 of 1,000 simulations in both the July 2020 – June 2021 and the 2021 horizons. The mean advantage shrinks, for example to −9.1 points at 20% in the six-window horizon.
- **Contrast with worst-case errors.** The worst-case (adversarial) tipping points remain small (0.5–2.5% of answers). The honest summary is:
  - the timing result is robust to random error;
  - it is not robust to systematic error aimed at the chosen window;
  - there is no evidence on which kind dominates.

### 5. Liberia bounds: second scope

`missing_bounds_second_scope.csv`, one screen:

| Country | All frame households | Households with at least one observed 2020 window |
|---|---|---|
| Liberia | 39.8–78.6% (206 households, 24 never observed) | **48.6–77.9%** (182 households) |
| Malawi | 50.8–59.3% (297 households, 3 never observed) | 51.5–59.1% (294 households) |

The 24 never-contacted Liberia households account for about 9 points of the lower bound. Liberia stays secondary.

### 6. Best two-window schedule, frozen

Chosen on July 2019 – June 2020 (six windows, 179 complete households), the best pair is **November–December + January–February** (5.2% missed in training). It is not January–February + March–April.

In July 2020 – June 2021 (202 complete households, 133 reference positives) it missed **15.0%** against **36.4%** for a random pair. The difference is −21.4 points (−27.7 to −14.5). It was also the best pair in the test year (`frozen_best_pair.csv`).

The in-sample January–February + March–April figure (6.5%) is no longer headlined.

### 7. Housekeeping

- **Development log.** Moved from the repository root to `docs/DEVELOPMENT_LOG.md`. References to the local parent folder and an unrelated project were removed, and so were absolute local paths in reports.
  - These details remain in earlier commits; rewriting public history would need a force-push, which was not done.
  - A draft AI-use disclosure for the manuscript is in the README.
- **Authorship.** `CITATION.cff`, `LICENSE` and `pyproject.toml` now name Omoding Isaac (Ministry of Health, Uganda). Co-researchers will be added.
- **README.** En dashes and middots were replaced (ranges are written "a to b").
- **ERS Amber Waves 2015** (D'Souza and Tandon, Bangladesh). It shows that household-level data can misclassify *individuals* because food is shared unequally within households. That is complementary, concerning within-household allocation, and does not overlap with screening timing. It is added to the prior-work comparison.
- **Dashboard.** Public, read-only and aggregate-only; no change needed.

## What these responses do and do not establish

- **They make the existing claims defensible.** The outcome is the standard HHS. The Malawi calendar window holds against six-window references and under random error. The frozen pair holds out of time. Liberia's bounds are explained.
- **They do not make the contribution larger.** The only genuinely prespecified evidence is the five-country test, and there the calendar rule failed. The strongest honest claims are:
  1. In Malawi, lean-season timing has repeatedly mattered (exploratory and out-of-time, not blind).
  2. That advantage did not transfer as a calendar rule to other countries in a locked test.
  3. A simple second-contact rule did transfer.
- **Whether that is substantially stronger than the original timing finding is a judgement for the study team.** My view: it is more credible and more useful to programmes, but a solid field-journal paper, not a high-impact one, unless further genuinely prospective evidence is added.
