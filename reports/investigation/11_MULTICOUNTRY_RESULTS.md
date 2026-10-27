# Results of the locked multi-country test

*Run 27 October 2026 under the protocol in `10_LOCKED_PROTOCOL_MULTICOUNTRY_HFPS.md` (commit `8d33f4d`; SHA-256 of the protocol document `23afabbe…5ba6d`, confirmed by the run). Outputs are in `data/public_aggregates/multicountry/` and figure `figures/investigation/figI6_multicountry_locked_test.*`. Two runs gave byte-identical outputs.*

## Headline

- **H1 (calendar rule, primary): contradicted** under the locked decision rule. A single contact timed by the FEWS NET typical-year lean season did *not* miss fewer households than a randomly timed contact in either testable primary horizon. In Burkina Faso 2020–21 it missed **10.9 points more** (95% CI +6.9 to +14.7).
- **H3 (second-contact warning rule): supported.** Re-contacting first-contact negatives who answered "yes" to a milder FIES item gave more later positives per 100 re-contacts than random re-contact, in all 3 testable primary horizons.
- **H2 (data-driven transfer):** a single testable pair (Uganda), inconclusive.
- **H4 (rural vs urban):** in both primary horizons the rule did relatively better for rural households (exploratory, as pre-specified).
- **What this means for the paper:** the January–March advantage found in Malawi does **not** carry over as a general "screen in the lean season" rule. Whether a seasonal contact helps depends on the year and the setting.

## Data and provenance

| Panel | Archive (SHA-256, first 12 characters) | Food-security rounds containing item 7 | Usable horizons (locked rules) |
|---|---|---|---|
| Burkina Faso | `a3123aa7944e` | 2–7, 9–11, 13, 15, 17–23 | 2020–21 |
| Ethiopia | `2a7b77336844` | 1–6, 11, 15, 17, 18 | 2019–20 (excluded from H1 by protocol) |
| Nigeria 2020–21 | `8444b147092b` | 2, 4, 7 | none (at most 2 rounds per horizon) |
| Nigeria 2021–24 | `00bef7dad921` | 6, 9, 10, 13 | none (2 rounds per horizon) |
| Uganda | `dae5979baacc` | 2–18 | 2020–21; 2022–23 (no lean-season round, so not testable for H1) |
| Tanzania | `86bf8d080fc6` | 1, 7, 8, 10, 11 (9 unreadable; 12 not answered) | none |

The archives were downloaded by the study owner from the World Bank Microdata Library. They are stored unchanged under `data/raw/multicountry/` (gitignored). Only aggregates are published.

## H1: calendar rule against random retention (item: "hungry but did not eat")

| Horizon | Analysis | Rounds (rule round) | Complete / reference-positive households | Rule missed | Random missed | Difference (95% CI) | Weighted difference | Missing-data range |
|---|---|---|---|---|---|---|---|---|
| Burkina Faso 2020–21 | **Primary** | 4, 5, 6, 7, 9, 10, **11 (7 Jul 2021)** | 1,686 / 398 | 76.9% | 66.0% | **+10.9 (+6.9 to +14.7)** | +6.6 | −13.8 to +20.2 |
| Uganda 2020–21 | **Primary** | 2, 3, 4, 5, **6 (28 Mar 2021)** | 1,919 / 539 | 62.3% | 59.0% | +3.4 (−3.9 to +8.8) | +4.3 | −17.1 to +15.7 |
| Burkina Faso 2022–23, group A | D2 | 15, 17, **18 (23 Jul 2023)** | 645 / 236 | 24.2% | 56.5% | −32.3 (−38.4 to −25.5) | −30.6 | — |
| Burkina Faso 2022–23, group B | D2 | 15, 17, **19 (25 Sep 2023)** | 604 / 235 | 24.7% | 56.7% | −32.1 (−38.1 to −25.3) | −33.7 | — |
| Uganda 2023–24, group | D2 | 14, 16, **18 (5 Mar 2024)** | 757 / 220 | 61.8% | 54.8% | +7.0 (−0.8 to +14.7) | +8.5 | — |

- **Decision (locked criterion):** the point estimate is above zero in 2 of 2 primary horizons, which is more than half, so H1 is **contradicted**. Including the D2 sensitivity horizons, it is above zero in 3 of 5, still contradicted.
- **Interval and cluster method:** the 95% intervals are cluster bootstraps. The clusters are survey clusters (`grappe`) in Burkina Faso, with 512 clusters in the primary horizon, and districts in Uganda (116). The protocol's order of preference applied, because Uganda's public files have no enumeration-area ID.
- **Missing-data ranges:** the exact ranges in the primary horizons both include zero. In the D2 panels nobody has a missing round, so the ranges collapse to the point estimates.

## H4: rural minus urban, in (rule − random), exploratory

| Horizon | Rural | Urban | Rural minus urban (95% CI) |
|---|---|---|---|
| Burkina Faso 2020–21 | +4.3 | +15.1 | −10.8 (−19.2 to −2.6) |
| Uganda 2020–21 | +2.1 | +8.3 | −6.2 (−13.5 to +2.4) |

The direction matches the hypothesis: the rule does relatively better for rural households. But it is not beneficial for rural households either; it is only less harmful than for urban ones.

## H2: data-driven transfer

Only one ordered pair of usable horizons exists: Uganda 2020–21 → 2022–23.

- **Selection:** August 2020 (round 2), chosen in 100% of training bootstraps.
- **Test round:** August 2022 (round 9, 8 days away).
- **Result:** the frozen choice missed 48.5% against 51.8% at random, a difference of −3.3 (−9.8 to +3.7). Inconclusive.
- **Pandemic-onset comparison:** no testable pair had a flagged training horizon, so the pre-specified comparison cannot be made.

## H3: second-contact warning rule (later positives per 100 re-contacted)

| Horizon | Analysis | Re-contacted | Warning rule | Random | Difference (95% CI) |
|---|---|---|---|---|---|
| Burkina Faso 2020–21 | Primary | 821 | 18.6 | 12.4 | +6.2 (+4.8 to +7.8) |
| Uganda 2020–21 | Primary | 799 | 16.9 | 10.5 | +6.5 (+4.4 to +8.8) |
| Uganda 2022–23 | Primary | 589 | 37.7 | 36.2 | +1.5 (−1.8 to +5.3) |
| Ethiopia 2019–20 | Primary | — | — | — | Untestable: the first round asked only FIES items 6–8 |
| Burkina Faso 2022–23 (two groups) | D2 | 386 / 350 | 34.5 / 34.0 | 29.6 / 31.4 | +4.8 (+2.1 to +7.5) / +2.6 (−0.5 to +5.7) |
| Uganda 2023–24 (two groups) | D2 | 446 / 402 | 18.4 / 22.6 | 18.9 / 19.3 | −0.5 (−2.8 to +1.7) / +3.3 (+1.0 to +5.3) |

**Decision:** positive in 3 of 3 testable primary horizons, so H3 is **supported**. Including D2, it is positive in 6 of 7.

## Post-hoc exploratory explanation (not part of the locked test)

`posthoc_single_round_missed.csv` lists every round's missed share within each usable horizon.

- **2020–21 horizons:** in all three usable ones, the earliest round was the best single contact.
  - Burkina Faso: November 2020, 46.5% missed against 66.0% at random.
  - Ethiopia: April 2020, 42.1% against 63.5%.
  - Uganda: August 2020, 29.9% against 59.0%.
- **Why that matters:** the share answering "yes" fell round by round (in Burkina Faso, from 12.6% in November 2020 to 5.5% in July 2021). A downward trend like that swamps seasonality, and a lean-season rule placed late in the year cannot win.
- **Possible causes:** recovery from the pandemic shock, survey-age effects (panel conditioning), or both. These data cannot separate them.
- **Burkina Faso 2022–23:** the lean-season rounds stood out sharply. July and September 2023 had 28–29% "yes", against about 10% in November 2022 and March 2023. That matches FEWS NET's June–September lean season.
- **Uganda 2023–24:** December 2023 was the best round, not March 2024.
- **Malawi context:** in the Malawi data, the January–March advantage also appeared away from the first round of the horizon (the July–June Aggarwal test; World Bank December 2023 and February–March 2024).

## Deviations from the protocol

| # | Deviation | Reason | Effect |
|---|---|---|---|
| D1 | Items were identified by standard FIES position, with English or French keywords plus the item number in the variable name, not only by an English label containing "hungry" and "not eat" | Stata truncates labels at 80 characters (Uganda rounds 2–9; Nigeria 2021–24 rounds 9–10). Burkina Faso labels are in French. Ethiopia uses its own numbering. | Item 7 was mapped in every round where the module exists; mappings are listed in `item_mapping_and_sources.csv` |
| D2 | Split-sample horizons were re-formed as one panel per response pattern (at least 3 rounds and 100 households) | Burkina Faso (from round 18), Uganda (rounds 13–18) and Ethiopia (rounds 15/17/18) interview alternating sample groups, so no household is complete in those horizons | Reported **only** as sensitivity; the decision uses primary horizons. Including D2 does not change any decision |
| D3 | Tanzania round 9 excluded | The published Stata file is truncated: pandas and pyreadstat both fail and only the first 50 rows can be read. The archive's integrity test passes, so the file was published that way | Tanzania has no usable horizon in either case, because the food-security module went to a subsample (about 1,000 households) and round 12 has no answers. A CSV release could be checked; it would not change the Tanzania verdict |
| D4 | Interview-date sources | Burkina Faso: end-of-record timestamp (`s12q14`). Uganda rounds 13–18: end time in `interview_result.dta`. Nigeria: latest call-attempt date. Others: survey start or interview dates | Round dates are medians, so the choice of source has negligible influence |
| D5 | The pandemic-onset flag was first coded as "first food-security round" and corrected to "round 1 of panels that began in 2020", as the protocol states | Coding error found before results were read | Only Ethiopia 2019–20 is flagged; no H2 pair could use the flag |

## Limitations specific to this test

- **Few testable horizons.** Only 2 primary horizons could be tested for H1. Most panels lacked at least 3 food-security rounds within a 12-month window, or interviewed alternating sample groups.
- **Calendar resolution.** FEWS NET calendars are national or zonal. Burkina Faso and Uganda are heterogeneous, and the rule used one national window per country.
- **Instrument.** These are single FIES items with 30-day recall, not HHS.
- **Weights.** The weighted sensitivity uses cross-sectional weights.
- **Not fully blind.** Published prevalence charts for these countries were seen beforehand (protocol §1). They did not reveal the household-level outcomes analysed here.
