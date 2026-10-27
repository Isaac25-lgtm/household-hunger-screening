# Analysis history and evidence classes

*Omoding Isaac (MSc Data Science and Analytics; Ministry of Health, Uganda). Written 27 October 2026 for the revised manuscript package. Times are East Africa Time; commit hashes refer to https://github.com/Isaac25-lgtm/household-hunger-screening. Nothing in this project was prospectively registered in a public registry.*

## Terms used (they are not interchangeable)

| Term | Meaning in this project |
|---|---|
| **Temporal holdout (out-of-time)** | A window or rule is chosen on an earlier period, frozen, and evaluated on a later period. The later data may already have been seen by the investigators. |
| **Prespecification** | Hypotheses, rules and decision criteria written down and committed before the relevant outcomes were computed. |
| **Protocol-locked** | A prespecification committed to version control (with a hash) before the household-level outcomes existed locally. |
| **Complete blinding** | No exposure at all to the evaluated outcomes, including aggregates, before the analysis. **No analysis in this project meets this standard.** |
| **Partial outcome exposure** | Some outcome information (for example published aggregate charts, or round-level prevalences) was seen before the analysis. |
| **Post hoc sensitivity analysis** | An analysis added after results were known, to check robustness or answer a reviewer. |
| **Exploratory** | Hypothesis-generating; selection and evaluation on the same data, or no prespecified decision rule. |

## Chronology

| # | When | Step | Evidence class of what it produced |
|---|---|---|---|
| 1 | Before 26 Oct 2026 | Earlier exploratory analyses of the Aggarwal et al. (2022) public data by the investigators. Results were recorded as numbers only (`config/previous_findings.yaml`). | Exploratory |
| 2 | 26 to 27 Oct 2026 (commits `be33c50` to `fcaa5d2`) | Independent reconstruction and reproduction. Six-window 2020 frequency frontier (Malawi 55.1% missed with one random screen; Liberia 69.6%), village bootstrap, sharp missing-history bounds, label-error envelopes. | Exact and descriptive (the frontier is a design quantity; no selection involved) |
| 3 | Same | Timing-window selection on 2020: January–February (Malawi), March–April (Liberia). | Exploratory, in-sample |
| 4 | Same | Frozen 2020 → 2021 evaluation (2021 data stop in August: four windows). Malawi January–February 21.6% missed (22 of 102) vs 59.8% random. | Out-of-time, **not blind**: the investigators had already seen 2021 outcomes in step 1 |
| 5 | 27 Oct 2026 (`0ec1e13`) | July–June re-evaluation: chosen on July 2019 – June 2020, tested on July 2020 – June 2021, six windows. January–February 38.3% (of 133) vs 59.3% random. | Out-of-time, not blind (2020 and 2021 outcomes had been seen; July–December 2019 had not been analysed before) |
| 6 | 27 Oct 2026 (`0ec1e13`) | World Bank Malawi HFPS investigation. Round-level marginal rates for every round, including 2022 to 2024, were printed during the data audit before household-level analysis (`reports/investigation/00_PROTOCOL_AND_EXPOSURE_LOG.md`). ChatGPT Work had already analysed 2020 to 2021 rounds. | Exploratory and out-of-time, not blind (partial outcome exposure) |
| 7 | 27 Oct 2026, 09:31 (`8d33f4d`) | **Multi-country protocol locked** (hypotheses H1 to H4, decision rules, usability rules, FEWS NET lean months). Protocol SHA-256 `23afabbe…5ba6d`; parameters `a8ba13f0…f7324`. | Prespecification |
| 8 | Before step 7 | Exposure: published aggregate prevalence charts for these countries (Wollburg et al. 2025 Fig. 1; Deisemann et al. 2024 Fig. 2) had been seen during the literature review; no values recorded. | Partial outcome exposure |
| 9 | 27 Oct 2026, about 10:00 | Study owner downloaded the six archives; checksums recorded; metadata-only structural audit (no yes-rates printed) before running the analysis. | — |
| 10 | 27 Oct 2026, 10:21 (`a9dccfa`) | Locked analysis run. Five countries assessed; two (Burkina Faso, Uganda) had eligible primary H1 horizons. H1 contradicted under its rule; H2 inconclusive (one pair); H3 supported directionally (3 of 3 point estimates positive; one interval includes zero); H4 rural advantage in direction (one interval excludes zero). | **Protocol-locked, not fully blind** |
| 11 | Same | Deviations D1 to D5: item mapping by FIES position; split-sample groups as separate panels (sensitivity only); Tanzania round 9 unreadable; date-source differences; pandemic-onset flag coding fix. None changed a decision. | Documented deviations |
| 12 | Same | Post hoc explanation of the H1 failure (2020–21 reported hunger declined round by round). | Post hoc, exploratory |
| 13 | 27 Oct 2026, 14:16 (`037e0a0`) | Externally requested checks: HHS scoring audit; calendar-based (FEWS NET) window sensitivity; frozen best pair; Liberia second-scope bounds; single-window positives; random-error simulation; recall-overlap discordance. | Post hoc sensitivity analyses (calendar-based ones are not blind) |
| 14 | 27 Oct 2026 (this revision) | Paired window comparisons (best observed window vs others); exploratory September–February vs March–August description; matched-budget second-contact table; H2/H4 table. | Post hoc; the season grouping is explicitly exploratory and was suggested after the window results were known |

## Which findings sit in which class

| Finding | Class |
|---|---|
| Frequency frontier and identification ranges (Malawi, Liberia) | Exact design quantity with sampling and identification uncertainty; no selection |
| Intermittency (75% and 94% of ever-positive households positive in 1 to 3 of 6 windows) | Descriptive |
| January–February best in calendar 2020 (Malawi) | Exploratory, in-sample |
| 21.6% (four-window 2021) and 38.3% (six-window July 2020 – June 2021) | Out-of-time, not blind; different reference definitions |
| Best observed window in the full year is November–December; January–February and September–October not separable from it | Post hoc paired comparison |
| September–February windows generally better than March–August | Exploratory post hoc description only |
| Frozen best pair (November–December + January–February), 15.0% vs 36.4% | Out-of-time, not blind |
| World Bank Malawi January / late February–March advantage; failed transfer after the 2020 pandemic-onset round | Exploratory and out-of-time, partial exposure |
| H1 contradicted; H2 inconclusive; H3 supported directionally; H4 direction rural | Protocol-locked, not fully blind |
| D2 split-sample results (Burkina Faso 2022–23 about −32 points; Uganda 2023–24 +7.0) | Sensitivity only (deviation) |
| Robustness to missing histories (3 of 4 comparisons), adversarial tipping points, random-error simulations | Post hoc sensitivity |

## What must not be claimed

- That any analysis was prospectively registered, or fully blind.
- That the timing advantage was confirmed out-of-sample in Malawi by a blind test.
- That H1 failed conclusively across five countries (only two had eligible primary horizons).
- That every H3 comparison was individually significant.
- That January–February is a uniquely best month.
