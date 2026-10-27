# Manuscript outline and writing map: *Food Security* (Springer Nature)

*This is a writing map, not the manuscript.*

## Journal requirements

Checked 27 October 2026 from the journal's submission guidelines (https://link.springer.com/journal/12571/submission-guidelines). Re-check before submission.

**Structure and length**
- Research article of about 8,000 words, excluding abstract, keywords, references, figures and tables.
- Sections: Title, Abstract, Keywords, Introduction, Materials and Methods, Results, Discussion, References, Figures, Tables, author bios and author photos. Results and Discussion must be separate.
- No more than three levels of headings. Footnotes are discouraged.

**Title, abstract and keywords**
- Title under 25 words and at most 200 characters. The proposed title has 14 words.
- Running head of at most 60 characters.
- Abstract of 150 to 250 words in one paragraph: quantitative, with no citations and no undefined abbreviations.
- 4 to 6 keywords.

**Statements and Declarations** (before the references)
- Competing interests, funding, ethics approval or exemption, consent, data, material and code availability, author contributions.
- LLMs cannot be authors, and their use must be documented.

**Author material and references**
- Author bios of 50 to 150 words each, plus photos (authors may decline photos).
- At least 4 suggested reviewers, from institutions other than the authors' and from at least two countries.
- APA 7th edition references with DOI links.

**Figures**
- Width 84 mm (one column) or 174 mm (full width), height at most 234 mm.
- Captions go in the text file, beginning "**Fig. n**".

**Proposed title:** *Missed Household Hunger Under Infrequent Screening: Timing, Uncertainty, and Evidence from African Longitudinal Surveys*

**Proposed running head:** *Missed household hunger under infrequent screening* (50 characters)

**Keyword ideas:** household hunger scale; food insecurity monitoring; survey frequency; screening design; partial identification; phone surveys.

## Introduction

1. **The problem.** Programmes screen fixed cohorts infrequently, and household hunger is intermittent.
2. **Existing monitoring approaches.** Cross-sectional surveys, sentinel sites, high-frequency phone surveys, FEWS NET calendars.
3. **What earlier work established.**
   - Single surveys misclassify households (Zhu et al. 2026).
   - "Ever food insecure" far exceeds point prevalence (Wollburg, Markhof and Jolliffe 2025, conference draft).
   - Monitoring frequency for targeting is an open question (Smith et al. 2026).
   - Measurement error can dominate dynamics (McDonough and Millimet 2024).
   - Lean-season data collection is recommended in field guidance.
4. **The gap.** No study quantifies the exact household ascertainment loss under thinned schedules for a 30-day experiential indicator, separates sampling, identification and answer-error uncertainty, and tests whether timing rules transfer across years and countries under a locked protocol.
5. **Objectives.**
   - *Primary:* the exact frequency frontier and timing at matched contact budgets.
   - *Secondary:* out-of-time and external checks, the protocol-locked multi-country hypotheses (H1 to H4), and the second-contact rule.

## Materials and Methods

Source for most items: `METHOD_SELECTION_AND_MODELS.md`.

- **Study design and data provenance.** Aggarwal et al. (2022) supplement; World Bank HFPS; checksums.
- **Populations.** Control households of the trial; national phone panels. Representativeness limits.
- **Measurement.**
  - *HHS:* standard scoring checked; the frequency answers are not public (`REVIEW_RESPONSE.md` section 1).
  - *FIES items:* item 7 "hungry but did not eat" and item 8 "whole day without eating", with 30-day recall. Not equivalent to the HHS and never pooled with it.
- **Observation schedule.**
  - Trial: alternating-month calls, giving two-month windows.
  - World Bank: monthly to sparse rounds, with split samples from 2022.
- **Reference-positive outcome** and its saturation over long horizons.
- **Primary exact estimand.** The hypergeometric derivation of the missed share.
- **Frequency and timing contrasts** at matched contact budgets.
- **Uncertainty.**
  - Cluster bootstrap: villages for the trial; districts for the World Bank survey, which is approximate.
  - Sharp identification bounds for missing interviews.
  - Answer-error sensitivity: adversarial tipping points and random-flip simulations, with hypothetical rates labelled as such.
- **Training and evaluation history** (`ANALYSIS_HISTORY_AND_EVIDENCE_CLASSES.md`).
- **Locked multi-country protocol.**
  - Hypotheses, decision rules and usability rules.
  - Eligibility: five countries assessed, two with eligible primary H1 horizons.
  - Deviations D1 to D5.
- **Second-contact decision rules**, and the logistic regression benchmark at matched budgets.
- **Multiple testing.** H1 was the only confirmatory hypothesis. Subgroup and window comparisons are descriptive or exploratory, and no adjustment is claimed.
- **Software and reproducibility.** Python 3.12, pinned environment, deterministic outputs, brute-force-validated solvers, public repository.
- **Ethics.** Secondary analysis of public de-identified data; institutional determination pending.
- **AI use.** Documented as the journal requires (draft in the README).

## Results

**Primary**
- Table 2 and Fig. 2: frequency frontier with identification ranges beside it.
- Fig. 3: intermittency.
- Table 3 panel A and Fig. 4: timing at matched budgets.
  - Lead with July 2020 – June 2021.
  - Then the four-window 2021 analysis, kept separate.
  - Report the best observed window and the paired comparisons (Table S17).

**Secondary**
- Table 3 panel B: World Bank Malawi, including the failed 2020 → 2021 transfer.
- Liberia.
- Fig. 5 and Table 4: protocol-locked H1 and H3. Table S15: H2 and H4.
- Table S16: second-contact benchmarks.

**Sensitivity**
- Fig. 6: missing histories, adversarial and random answer error.
- Table S5: second-scope bounds.
- Table S6: persistent-only positives.
- Tables S1 and S2: attrition and IPW.
- Thresholds (Fig. S11).
- D2 horizons.
- Table S18: exploratory season grouping.

## Discussion

- **Principal findings,** stated with their evidence class.
- **Novelty against the closest work** (`investigation/04_CLOSEST_PRIOR_WORK.md`). Do not claim novelty for intermittency or single-survey misclassification.
- **The negative calendar-transfer finding.** Two eligible horizons; possible pandemic recovery and survey-age effects.
- **Implications for schedule design.** Timing matters but is context-dependent; check against local recent data.
- **The second contact.** A modest, transparent rule; random re-contact is a weak benchmark; no cost data.
- **Limitations** (`LIMITATIONS_AND_THREATS.md`, consolidated section).
- **Generalisability and future validation.** Monthly HHS sentinel data (MIRA); prospective schedule trials.

## Statements and Declarations

- **Ethics:** pending an institutional decision.
- **Funding:** to be completed.
- **Competing interests:** to be completed.
- **Author contributions:** to be completed when co-researchers are added.
- **Data availability:**
  - Aggarwal et al. (2022) supplement, CC BY 4.0.
  - World Bank Microdata Library catalogs 3766, 3768, 3716, 3712, 4444, 3765 and 4542 (DOIs in `DATA_CITATIONS.md`). Microdata are not redistributed.
- **Code availability:** the GitHub repository and the release commit.
- **AI-use disclosure.**
- **Affiliation:** Ministry of Health, Uganda (confirm the permission requirements).
