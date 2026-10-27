# Limitations and threats to validity

Each item gives the threat, how it affects the results, what was done here, and what could remediate it.

## Internal validity

| # | Threat | Effect on results | Done here | Remediation |
|---|---|---|---|---|
| 1 | **Retrospective thinning ≠ prospective sparse design.** Dropping recorded interviews assumes responses would be identical under a sparser schedule. | Real sparse designs may change recall, salience, panel conditioning and attrition (cf. Bell et al. 2019). The direction is unknown. | Stated as the core interpretive limit; no causal language used. | A randomised frequency experiment in a screening programme. |
| 2 | **Reference ≠ truth.** "Reference-positive" means positive in ≥ 1 of six observed 30-day windows; ~6 of 12 months are unobserved. | Households hungry only in unobserved months are not in the denominator, so the estimand describes ascertainment *relative to the six-window reference*, not to all hunger episodes. | Estimand defined conditionally; "not annual incidence" stated everywhere. | Monthly data (Malawi's 2019–2021 monthly calling of alternating halves does not give per-household monthly data). |
| 3 | **Selection into complete histories.** Malawi 76% and Liberia 33% of the frame are complete; completers differ on several socioeconomic markers. | Complete-case estimates may not represent the frame. | Sharp no-assumption bounds over the frame; IPW sensitivity; balance table. | More covariates or follow-up of non-responders; MNAR sensitivity models with substantive priors. |
| 4 | **Measurement error in HHS.** Self-reported, three items; frequency follow-ups unavailable for checking. | Misclassification around the HHS = 1/2 boundary changes K. | Bounded hypothetical label-error budgets (shared; exact). | Validation substudy (repeat interviews, alternative indicators) to estimate error rates. |
| 5 | **HHS ≥ 2 as an individual screening flag.** HHS was validated for population prevalence in food-insecure settings (FANTA; WFP notes it should not stand alone). | Household-level classification error may exceed what population validation implies. | Secondary thresholds (≥ 1, ≥ 4) reported; language limited to "screening flag". | Cross-validate against FCS/rCSI/FIES in the same data, with care about comparability. |
| 6 | **Duplicate-slot rule.** One household-slot had two records. | Does not affect HHS ≥ 2 or ≥ 4; affects one household for HHS ≥ 1. | Outcome-blind earliest-date rule; effect logged. | — |
| 7 | **Exploration and multiplicity.** Four timing candidates, three thresholds, several schedules. | The in-sample best fixed schedule is optimistic (winner's curse). | Timing frozen on 2020 and tested on 2021; selection stability bootstrapped; fixed-schedule results labelled in-sample. | Pre-registration of the manuscript's primary comparisons. |
| 8 | **Clustered uncertainty with few clusters (Liberia 47 villages, 34 positives).** | Percentile intervals are coarse and may under-cover. | Jackknife, 20,000-draw and all-village variants agree; coarse lattice disclosed. | Report exact or Bayesian hierarchical intervals as a sensitivity; more data. |
| 9 | **Bootstrap ignores frame-level missingness.** | CIs describe complete-case sampling only. | Bounds reported separately; never merged with CIs. | Combined inference (e.g. Imbens–Manski intervals) if desired. |

## External validity

| # | Threat | Effect | Remediation |
|---|---|---|---|
| 10 | **Sample.** Control households of a cash-transfer RCT in selected rural areas; phone-owning respondents. Not nationally representative (weights = 1 confer nothing). | No national or population inference. | Replication in representative panels (e.g. World Bank HFPS, LSMS-ISA). |
| 11 | **Period.** 2020–2021 overlaps COVID-19 market disruptions documented by the source study. | Hunger dynamics (and so the frontier and timing results) may differ in normal years. | Replicate in non-pandemic years. |
| 12 | **Two adjacent years for timing.** | Cannot show a stable seasonal optimum; Malawi's Jan–Feb result is consistent with the known lean season, but its magnitude varied (2020 vs 2021 positive share 66% vs 40%). | Multi-year data; agro-climatic covariates. |
| 13 | **Liberia sparsity.** 34 reference-positive complete households; 13 in the matched timing cohort. | Liberia results are imprecise and weakly identified; timing results are uninformative. | Present Liberia as secondary; avoid pooled claims. |
| 14 | **No cost data.** | No cost-effectiveness or optimal-frequency claim is possible; the frontier gives the *detection* side only. | Collect per-interview costs and value of detection from a programme partner. |

## Claims explicitly excluded

The results are not national hunger prevalence; not an undercount of official statistics or IPC phases; not annual incidence; not malnutrition; not causal effects of survey frequency, cash transfers or COVID-19; and not evidence that any calendar window is universally optimal. Confidence intervals, identification ranges and label-error envelopes are different objects and are never merged.


## Consolidated limitations (revised manuscript package, 27 October 2026)

**Data and samples**
- **Survey mode.** All data come from phone surveys. Selection into phone reachability and phone-mode reporting may bias levels and dynamics.
- **Trial sample.** The control arm of a cash-transfer trial in rural Liberia and Malawi; not nationally representative.
- **Unavailable source fields.**
  - The first HHS item is labelled "skipped a meal" in the source do-file and a table caption, while the analysis variable carries the standard wording. The score matches the standard item, but the questionnaire has not been confirmed with the source authors.
  - The original frequency-response fields are not in the public supplement.
- **Follow-up and selection.**
  - Follow-up is partial, and attrition is particularly severe in Liberia (33% complete histories).
  - Restricting to complete histories causes selection, which is addressed only by bounds and inverse-probability weighting under a missing-at-random assumption.

**Design and reference**
- **Recall coverage.** 30-day recall every two months leaves about half of each year unobserved. "Ever positive" depends on the number of windows and saturates over long horizons.
- **Retrospective design.** Interviews were deleted after the fact; this is not a real reduced-screening experiment. Panel conditioning may differ under real reduced schedules.
- **Time effects.** COVID-era trends, recovery from shocks and survey-age effects cannot be separated from seasonality; round number and calendar time are confounded.

**Uncertainty and measurement**
- **Missing data.** Missing-data conclusions are either assumption-free ranges or rest on stated assumptions (missing at random for inverse-probability weighting).
- **Answer error.** Error scenarios are hypothetical. Discordance between overlapping recall periods is not an error rate.
- **Different instruments.** The HHS (trial) and single FIES items (World Bank) are different instruments and are not pooled.
- **Clustering.** World Bank intervals use district clusters, which is approximate, because there is no PSU or stratum in the public files.

**Evidence base**
- **Few eligible horizons.** Only two eligible primary H1 horizons (Burkina Faso, Uganda); H2 had one testable pair.
- **Prior exposure.** Some published aggregate charts were seen before the protocol was locked, and the Malawi data had been analysed before every out-of-time check.
- **Second contact.**
  - The comparison is against random re-contact, a weak benchmark, because milder symptoms predict later hunger by construction.
  - The rule is tested on observed later rounds, not on a real follow-up programme.
- **No operational costs.** No programme-specific cost data; yield per 100 contacts is not a cost-effectiveness measure.
- **External generalisability** is limited to the settings and years observed.

**Unresolved before submission**
1. Confirmation of the HHS questionnaire and scoring by the original authors.
2. Independent statistical review and an institutional ethics decision.
3. Co-author information, accurate affiliations and institutional permissions.
