# Locked protocol: multi-country test of single-contact timing rules (LSMS high-frequency phone surveys)

*Locked 27 October 2026, before any microdata from these surveys were downloaded. The committed file's SHA-256 is recorded in the commit that follows it. Machine-readable parameters are in `config/multicountry_protocol.yaml`; the analysis code must read only from that file. Any deviation from this protocol is reported in a "Deviations" section of the results report, which is written afterwards.*

## 1. Prior exposure

- **Microdata:** none downloaded or opened for Burkina Faso, Ethiopia, Nigeria, Tanzania or Uganda.
- **Round fieldwork dates:** read from the public catalogue metadata (World Bank Microdata Library API). They contain no outcomes.
- **Published aggregate figures seen** during the literature review:
  - Wollburg, Markhof and Jolliffe (2025), Figure 1: round-level and year-level shares of households with moderate-or-severe FIES food insecurity for these countries, shown as a chart.
  - Deisemann et al. (2024), Figure 2: round-level FIES prevalence for Burkina Faso and Malawi, shown as a chart.
  - I recorded no values from either figure. Both show a different, Rasch-based measure, not the single items used here.
- **Household-level and item-level outcomes:** unseen.
- **Malawi:** excluded from this test, because it was analysed extensively before.

## 2. Data

| Country | Catalogue | Study ID |
|---|---|---|
| Burkina Faso | 3768 | BFA_2020-2024_HFPS_v23_M |
| Ethiopia | 3716 | ETH_2020-2024_HFPS_v15_M |
| Nigeria | 3712 | NGA_2020_NLPS_v12_M (2020–21) |
| Nigeria | 4444 | NGA_2021-2024_NLPS_v10_M (2021–24); a separate panel, analysed separately |
| Uganda | 3765 | UGA_2020-2024_HFPS_v17_M |
| Tanzania | 4542 | TZA_2021-2024_HFWMPS_v09_M |

- **Version and integrity:** the version downloaded is recorded with a SHA-256 checksum for every archive.
- **Outcome items:**
  - *Primary:* the FIES item "hungry but did not eat", identified by a variable label containing "hungry" and "not eat".
  - *Secondary:* "went without eating for a whole day".
  - Yes/no codes are taken from the value labels. All other values count as missing.
- **Structural audit before any analysis:** file lists, variable names and labels, value labels, interview dates, household-ID uniqueness, merges, sample groups and non-missing counts only. No yes-rates are printed before the analysis script runs.

## 3. Definitions (identical to the Malawi analyses unless stated)

- **Round date:** the median interview date of the round's food-security records. Rounds without the primary item are not candidates.
- **Horizon:** a 12-month screening year, one per country, with the start month fixed in advance (table below). Candidate rounds are those whose round date falls inside it.
  - A horizon is **usable** if it has at least 3 candidate rounds and at least 100 households observed (non-missing) at every candidate round (the complete cohort).
  - The **pandemic-onset flag** marks any horizon containing the country's first 2020 survey round.
- **Reference-positive household:** positive in at least one candidate round of the horizon. A household is "missed" by a schedule if it is negative at every retained round.
- **Random benchmark:** the exact hypergeometric miss probability for one round chosen uniformly at random.
- **Calendar rule:** pick the candidate round whose date falls inside the country's FEWS NET typical-year lean months. If several qualify, pick the one closest to the lean-season midpoint; if none qualifies, the rule is untestable in that horizon. In Nigeria the rule is applied per household by geopolitical zone: north = North-Central, North-East and North-West; south = the three southern zones. If no zone variable exists, Nigeria is untestable for H1.

| Country | Lean months (FEWS NET typical-year calendar, viewed 27 Oct 2026) | Midpoint | Horizon start month |
|---|---|---|---|
| Burkina Faso | Jun–Sep | 31 Jul | October |
| Nigeria, north | Jul–Sep | 15 Aug | October |
| Nigeria, south | May–Jul | 15 Jun | October |
| Uganda | Mar–Jun (both rainfall zones) | 30 Apr | July |
| Tanzania | Nov–Dec (overlap of unimodal Nov–Feb and bimodal Oct–Dec) | 30 Nov | March |
| Ethiopia | Not applicable: no single national lean season (zones range Jan–Sep). H1 is not tested | — | October (for H2 and H3 only) |

## 4. Hypotheses and decision criteria

- **H1, calendar rule (primary).** In each usable horizon where the rule is testable, compare the missed share of the rule's round with random retention.
  - **Supported:** the point estimate is below zero in at least two-thirds of testable horizons, and no horizon has a 95% interval entirely above zero.
  - **Contradicted:** the point estimate is above zero in more than half of testable horizons, or at least two horizons have intervals entirely above zero.
  - **Mixed:** anything else.
  - There is no pooled estimate (horizons within a country share households). Every horizon is reported.
- **H2, data-driven transfer (secondary).** For every ordered pair (earlier usable horizon → later usable horizon) within a panel:
  - Select the round with the lowest missed share in the earlier horizon (earliest date on ties).
  - Freeze it, then evaluate the later-horizon round whose day of the year is closest to it, within 45 days circularly. If no round is that close, the pair is untestable.
  - Report each pair against random and against the calendar rule.
  - Descriptive hypothesis: pairs whose training horizon carries the pandemic-onset flag do worse against random than pairs whose training horizon does not.
  - The selection-stability bootstrap is as in the Malawi analyses.
- **H3, second-contact rule (secondary).** In each usable horizon:
  - The first contact is the earliest candidate round; the later contacts are the remaining candidate rounds.
  - The warning sign is "yes" to any of FIES items 1–6 at the first contact.
  - The budget equals the number of warning-sign negatives.
  - Compare the later positives found per 100 re-contacted under the warning-sign rule and under random re-contact.
  - **Supported:** the difference is positive in at least two-thirds of usable horizons.
- **H4, equity (single pre-specified contrast; exploratory).** In each horizon where H1 is testable and a rural/urban indicator exists, compare (rule − random) between rural and urban households.
  - Hypothesis: the advantage is larger, i.e. more negative, for rural households.
  - Report the paired bootstrap interval of the rural-minus-urban difference.
  - No other subgroup analyses are reported as part of this protocol.

## 5. Inference

- **Bootstrap:** percentile bootstrap, 2,000 draws, seed 20261028.
- **Clusters:** the finest geographic unit available below the nation, in order of preference: enumeration area or cluster ID; then district (admin 2); then region (admin 1). The unit used is recorded.
- **Weights:** unweighted primary analysis. A sensitivity analysis uses the cross-sectional weight of the horizon's last round, labelled as not a panel weight.
- **Missing-data ranges:** exact ranges and the tipping-point budget (`history_bounds.py`) for H1 wherever it is testable.
- **Multiplicity:** no correction. H1 is the only confirmatory hypothesis.

## 6. Things this protocol cannot fix

- **Not blind:** the published prevalence charts listed in §1 were seen.
- **Instrument:** FIES single items, not HHS.
- **Calendars:** FEWS NET calendars are national or zonal syntheses and may not match each survey year.
- **Round 1:** in several countries the first round also coincides with the pandemic onset.
