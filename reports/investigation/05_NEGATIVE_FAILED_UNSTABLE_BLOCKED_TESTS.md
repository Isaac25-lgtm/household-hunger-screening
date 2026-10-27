# Negative, failed, unstable and blocked tests

Every result here is kept, and nothing was dropped for being inconvenient. Sources are in `data/public_aggregates/investigation/`.

## Negative results (the hypothesis or rule did not work)

| Test | Result | File |
|---|---|---|
| World Bank: choose a round on 2020, apply the matching round in 2021 | Picked June 2020; the 2021 late May–June round then missed **+12.7 points more than random** (+10.3 to +15.3). For s8q8: +13.5 (+8.2 to +18.0) | `hfps_transfer_tests.csv` |
| World Bank: calendar-matched, group B, 2020–21 → 2023–24 | Picked June; June 2023 missed **+12.6 points more** than random (+8.5 to +16.6). s8q8: +10.0 | same |
| World Bank: calendar-matched, group A | Picked June (near tie in training); June 2023 missed **+9.8 points more** than random (+6.2 to +13.8). s8q8: +12.0 | same |
| December 2020 as a lean-season contact (World Bank) | Barely better than random: −2.4 points (−5.0 to +0.1) | `hfps_single_round.csv` |
| November 2020 (World Bank) | **Worst** round of 2020: +7.9 points (+5.0 to +11.2) | same |
| April 2021 contact (World Bank) | No better than random: −1.5 (rounds 7/9/11) and −0.6 (five rounds) | same |
| Logistic model against a simple rule for the second contact | No gain: 52.3 against 52.9 per 100 re-contacted (s8q7, half budget); 18.4 against 17.1 (s8q8) | `hfps_model_vs_rule.csv` |
| Second-contact rule in the Aggarwal data, other than Malawi 2020 | Intervals include zero (Malawi 2021: 19 households re-contacted; Liberia 2020: 18; Liberia 2021: 27) | `aggarwal_second_contact.csv` |
| Liberia frozen timing (baseline) | Inconclusive: −5.7 (−26.9 to +14.1); the missing-data range already includes zero (−41.0 to +27.7) | `aggarwal_timing_robustness.csv` |

## Fragile or unstable results

| Item | Finding |
|---|---|
| Robustness to response error | Worst-case flips of **8 answers (0.5%)** erase the Aggarwal July–June advantage; **25 (2.5%)** erase the calendar-2021 advantage; **79 (1.7%)** erase the World Bank January advantage (rounds 7/9/11); **46 (0.6%)** erase it across all five 2021 rounds. For World Bank s8q8, missing data alone already reach zero (range −21.3 to +0.9) |
| Selection stability | World Bank group B training picked June in 75% of district resamples, or 52% when trained on group-B households only. Group A training picked June in 53%. Liberia's baseline choice: 62% |
| Size of the timing advantage | Ranges from −11 points (World Bank 2021) to −38 points (Aggarwal 2021). The cohorts, instruments and number of contacts differ, so the sizes cannot be compared directly |
| Who is missed | The Q1 minus Q5 gap excludes zero for s8q7 (−13.2; −23.5 to −4.3) but not for s8q8 (−12.9; −32.1 to +6.0). These are 22 subgroup comparisons without adjustment |

## Failed or corrected steps

| Step | What happened | Resolution |
|---|---|---|
| First version of the exact solver | Started Dinkelbach iteration from one household's option instead of a full feasible world. The maximisation stopped at the start value, and 14 of 20 new tests failed against brute force | Started from a full feasible world (every household at its zero-cost history, with a forced reference positive if needed). All brute-force tests then passed |
| Model against rule at the full budget | All rules chose the same households by construction (budget = number of warning-sign households), so the comparison was uninformative | Added the half-budget comparison, where ranking within the warning-sign group matters |
| Aggarwal second-contact label | Rows were labelled "milder item"; the rule is HHS = 1 | Label corrected |
| Two numbers in my first draft of the report | Wrote 18.2% against 54.6% (Malawi 2020 January–February against random) and a Liberia random value of 70.1%, from rounded displays | Corrected to 17.8% against 55.1% and 69.6% after checking the CSV files |
| Rounds 7→8 interview gaps under 30 days | My figure is 4.3% (65 of 1,508); ChatGPT Work reported 5.6% | Unresolved: the earlier script is unavailable |

## Analyses the data cannot support

- **A blind or preregistered test.** All World Bank rounds were opened during the audit, and 2023–24 round-level rates were printed before the protocol. There are no untouched outcome data in either dataset.
- **Separating the pandemic onset from a first-interview effect** in World Bank round 1, because there is no refreshment sample.
- **Survey-design-correct intervals** for the World Bank panel: no PSU or strata, and no panel weight.
- **An HHS replication** in the World Bank data. Only an HHS-analogue score exists, in two cross-sectional rounds held by different sample groups.
- **Monetary cost or cost-effectiveness**, because no per-contact costs are documented for either survey. Logged call attempts cover completed interviews only.
- **January–March candidates** in the World Bank 2020 data and in the 2023–24 group-B horizon: there were no such rounds.

## Blocked

| Item | Barrier |
|---|---|
| MIRA monthly HHS (CRS/Cornell) | Not public; needs a data-sharing request (not sent) |
| Malawi RFMS | Not public; overlap with MIRA unverified |
| Myanmar MHWS | The Dataverse guestbook needs your identity (not completed) |
| Other LSMS-HFPS countries | Needs your Microdata Library login; deliberately not downloaded so a protocol can be locked first |
| McDonough & Millimet (2024) and Guthoff et al. (2026) full texts | Automated download returned an HTML page or HTTP 403. Only the abstracts were read |
