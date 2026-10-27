# Manuscript options

> **Revision note (27 October 2026, revised manuscript package).** Some statements in this historical report were corrected in place. The current, authoritative summary is `reports/ALL_FINDINGS.md`; the analysis history and evidence classes are in `reports/ANALYSIS_HISTORY_AND_EVIDENCE_CLASSES.md`. Changes are listed in the package's `07_quality_control/CHANGELOG_FROM_PREVIOUS_PACKAGE.md`.

Fit describes the type of journal each option suits. It is not a probability of acceptance, and nothing here guarantees publication.

## Option 1 (recommended now): two Malawi panels, timing at a fixed contact budget

**Working titles:**
- *When to ask: timing and frequency of household hunger screening in two Malawi panels*
- *One well-timed contact: lean-season screening and missed household hunger in two Malawi panels*
- *Missed household hunger under infrequent screening: timing, frequency and transfer across two Malawi panels*

**Core claim (revised).** In two independent Malawi panels with different instruments, contacts between September and February generally identified more of the households reporting hunger at any observed contact than contacts at random or between March and August. No single month is established as best. Choosing the month from one earlier year failed when that year began at an atypical moment. In three of four timing comparisons the exact missing-history identification range excludes zero; all could be erased by small amounts of worst-case answer error, but not by random error at hypothetical rates up to 20%. **Current working title:** *Missed Household Hunger Under Infrequent Screening: Timing, Uncertainty, and Evidence from African Longitudinal Surveys*.

**Structure:**
1. **Introduction.** Screening budgets; existing timing advice (IndiKit HFIAS guidance); evidence that single surveys miss households (Zhu et al. 2026; Wollburg et al. 2025); the open monitoring-frequency question (Smith et al. 2026).
2. **Data.**
   - Aggarwal Malawi phone panel: HHS, two-month windows, July 2019 – August 2021.
   - World Bank HFPS Malawi: FIES items 7 and 8, 15 rounds.
   - Measurement table: wording, recall, scope; why the two are not pooled.
3. **Estimands.** Missed share; identified per 100 households and per 100 contacts; exact random benchmark; reference horizons and saturation.
4. **Results.**
   - (a) Timing within years (Figure I1).
   - (b) Frequency frontier (baseline Figure 2).
   - (c) Transfer tests (Figure I2), with full disclosure of what was seen before.
   - (d) Exact robustness and tipping points (Figure I3).
   - (e) Contacts and yield; second-contact rule (Figure I5).
   - (f) Who is missed, exploratory (Figure I4).
5. **Discussion.** A January–March calendar rule against learning the month from data. Tension with variance-decomposition evidence (Deisemann et al. 2024). Response-error fragility. No programme-delivery claims.
6. **Supplement.** Liberia; s8q8; weighted sensitivity; household bootstrap; HHS-analogue concordance; solver validation; exposure log.

**Fit:** *Food Security* (Zhu et al. appeared there), *Global Food Security*, *Public Health Nutrition*, *PLOS ONE*, *Food and Nutrition Bulletin*.

## Option 2 (stretch): add a protocol-locked multi-country test

Same as Option 1, plus a confirmatory section. Write and date a protocol **before** downloading other LSMS-HFPS countries, fixing:
- candidate months from FEWS NET seasonal calendars for each country;
- items, cohorts, the comparison against random and a calendar rule, and the decision rules.

Then report every country whatever the outcome. If the same-instrument question matters, add MIRA monthly HHS data under a data-sharing agreement.

**Fit:** *Food Policy*, *Global Food Security*. This is realistic only if the locked test is clean and the result is interpretable either way.

## Option 3 (fallback): methods note

*Exact identification ranges for screening-schedule contrasts under missing interviews and response error.* Built around `history_bounds.py`, with both datasets as applications.

**Fit:** a methods or measurement venue (for example *Journal of Survey Statistics and Methodology*, or a methods section in *Food Security*). The audience is narrower.

## Titles and phrases to avoid

- "First", "novel finding that food insecurity fluctuates".
- "Optimal schedule", "best month".
- "National prevalence"; IPC phases.
- "Causes", "prevents hunger", "cost-effective".
- "HHS" for the World Bank items.
- "Validated" or "confirmed" for the 2023–24 tests: they are calendar-matched re-specifications, not blind tests.
