# Novelty and closest prior work

*Search executed 26–27 October 2026. Full ledger: [`literature_ledger.csv`](literature_ledger.csv).*

## 1. How the search was done (and what it could not do)

| Route | What was done | Result |
|---|---|---|
| Crossref REST API | DOI resolution and metadata for every named comparator (9) plus newly found papers | All DOIs resolved (HTTP 200); authors, titles, venues, volumes and pages recorded from Crossref |
| OpenAlex citation graph | All works citing Aggarwal et al. (2022) (`cites:W4290721377`, 46 works) with abstracts screened for screening-frequency, HHS, surveillance, attrition and recall terms | **No citing work reuses the source data for screening frequency or household ascertainment.** Same-project papers: AEJ Applied 2026 (cash-transfer dynamics), WBER 2024 (IPV self-interviewing) |
| Web search (extended) | Survey frequency / single-round misclassification / HHS repeated measurement / Malawi seasonal hunger / high-frequency resilience | Found the closest prior work, **Zhu et al. (2026, *Food Security*)**, plus Na et al. (2017) |
| Full text | Zhu et al. (2026) open-access PDF read; supplement readme and replication do-file for the source study read | — |
| Not accessible | FANTA HHS guide (HTTP 403; verified via secondary sources); PMC (bot check; Europe PMC used instead); Springer HTML (login redirect; PDF used) | Noted in ledger |

**Not claimed:** this is not a systematic review. Google Scholar, SSRN full-text search, NBER and RePEc working-paper full texts, and non-English literature were not exhaustively searched. Grey literature from WFP/FEWS NET monitoring systems (e.g. sentinel-site designs) may contain operational analyses of visit frequency that are not indexed.

## 2. Head-to-head comparison with the closest studies

| | **This study** | **Zhu, Gupta, Doan & Michuda 2026** (*Food Security* 18(5):1509–24) | **Na et al. 2017** (*BMC Public Health* 17:260) | **Livings et al. 2023** (*AJPM* 65(4):657–66) | **McDonough & Millimet 2024** (*AJAE* 106(5):1714–44) |
|---|---|---|---|---|---|
| Setting / data | Rural Malawi (297) and Liberia (206) control households; bimonthly phone panel, 2020–21 | 305 households, Sundarbans, India; weekly financial diaries, 50 weeks | 157 households, Zambia; 6 monthly visits (lean season) | US online panel, 2021 | US PSID |
| Indicator | Household Hunger Scale (experiential, 30-day recall), HHS ≥ 2 | Expenditure-based MEB, food expenditure share, FCS constructed from expenditure | 8-item perception-based HFI scale | Past-week vs past-year food insecurity | Food security status |
| Target | **Ascertainment**: share of ever-positive (reference-positive) households missed when only *m* of 6 windows are screened | **Misclassification** of a single random week vs the household's annual-average class | Within- vs between-household variance | Past-year under-reporting of past-week FI | Transition matrices |
| Method | Exact hypergeometric frontier; village bootstrap; sharp missing-history bounds; shared-budget label-error bounds (exact Dinkelbach + DP); frozen 2020 → 2021 timing test | Monte Carlo single-week draws; lagged recall; multi-indicator combination | Random-effects variance decomposition | Panel comparison | Partial identification under measurement error |
| Missing data | Sharp no-assumption bounds over the full frame | Complete diaries (attrition not bounded) | Not addressed (abstract) | — | Central (measurement error) |
| Out-of-sample timing | Yes (2020 → 2021, frozen) | Seasonal split within one year | No | No | No |
| Headline | Malawi 55% / 32% / 18% missed with 1 / 2 / 3 random screens; Liberia 70% / 47% / 31% | 15–48% misclassified by one round; 6–15% when indicators are combined | Within > between variance; repeated assessment needed | ~1/3 under-reported | Measurement error dominates; persistence in tails |

## 3. Honest novelty verdict

**The core message is not new.** Zhu et al. (2026) already show, with data and Monte Carlo resampling, that one-time surveys misidentify households because food security fluctuates, and that repeated observation is needed. Na et al. (2017) and Nord et al. (2002) made the intermittency point earlier. Livings et al. (2023) document under-reporting by infrequent long-recall questions. Partial identification under misclassification is established (McDonough & Millimet 2024 and the literature they build on). None of the algorithms used here (hypergeometric probabilities, cluster bootstrap, sharp bounds by exhaustive prefix search, Dinkelbach fractional programming, knapsack DP) is new.

**What is incremental and, as far as this search found, not previously reported:**

1. An explicit **household-ascertainment estimand** for repeated short-recall HHS screening of a fixed cohort (ever-positive reference rather than annual-average classification), with a complete **interview-count frontier** (m = 1…6) for two African countries.
2. **Sharp no-assumption identification ranges** over the whole baseline frame, which shows how much the conclusions depend on panel completion (narrow in Malawi, wide in Liberia), and a demonstration that single imputations are not the endpoints because the denominator moves.
3. A **shared-budget label-error sensitivity** tied to the same ascertainment functional, computed exactly with an optimality certificate.
4. A **frozen out-of-year test of calendar timing**. In Malawi a single lean-season window chosen on 2020 data cut 2021 misses from ~60% (random window) to ~22%. In Liberia the 2020 choice did not clearly transfer. This makes the paper about *schedule design* (timing and frequency), which goes beyond Zhu et al.'s frequency-only framing.
5. First reuse of the Aggarwal et al. (2022) public phone panel for a measurement-design question (per OpenAlex citation screening).

**Contrary evidence and risks to novelty.**
- Zhu et al. (2026) appeared in July 2026, and a reviewer will see this study as a variant of it. The manuscript must cite it prominently, state the differences in estimand, indicator, data and methods, and avoid any "first" claim.
- The random-window frontier partly restates combinatorics. Its scientific content comes from the *empirical distribution of K* (intermittency), which an editor may find thin unless the timing and bounds analyses carry the paper.
- Sentinel-site monitoring programmes (e.g. FEWS NET, WFP mVAM) may have unpublished visit-frequency analyses.

**Verdict:** no duplication of the joint study was found, so this is **not a HOLD on novelty grounds**. The contribution is a modest applied measurement paper. Its novelty claim should rest on items 1–4, positioned explicitly as complementary to Zhu et al. (2026).
