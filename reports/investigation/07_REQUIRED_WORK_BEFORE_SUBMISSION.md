# Work required before submission

## Data access (your decision; nothing was requested or sent)

1. **Other LSMS-HFPS countries.** Lock the protocol first (see Option 2 in `06_MANUSCRIPT_OPTIONS.md`), then download with your Microdata Library login.
2. **MIRA monthly HHS.** Optionally, a data-sharing request to CRS/Cornell; Brian Dillon is the corresponding author of Smith et al. If you go ahead, check how RFMS households overlap with MIRA.
3. **Myanmar MHWS.** Optional. It means completing the Dataverse guestbook yourself and checking the HHS variables in each round.

## Confirmations

4. **Aggarwal call schedule.** Confirm the odd/even-month design and the wording of the HHS phone items, from the article's methods and supporting information and, ideally, with the authors. The dates support the design; the documentation still needs checking.
5. **World Bank sample groups.** Find out how households were assigned to groups A and B in rounds 19–21. The basic information document lists the groups but doesn't say how they were assigned.
6. **First round of the World Bank survey.** Look for documentation of round-1 effects (pandemic onset, first-interview conditioning) in World Bank HFPS reports.
7. **Literature.**
   - Full texts of McDonough & Millimet (2024) and Guthoff et al. (2026).
   - Check for a paper version of Deisemann et al. (2024).
   - Check the status of Wollburg et al. before citing it.
   - A structured search of Google Scholar, SSRN, RePEc and NBER, and grey literature (FEWS NET, WFP mVAM, Cadre Harmonisé guidance) on assessment timing.

## Statistical review

8. Independent review of:
   - the exact-range solver (`history_bounds.py`) and its tipping-point search;
   - the decision to report adversarial flips, compared with a non-adversarial (random-error) sensitivity analysis that could be added;
   - the district-cluster bootstrap, given that the public World Bank data have no PSU.
9. **Multiplicity in the subgroup analysis.** Either pre-specify one equity contrast for any new data, or present all 22 comparisons as exploratory.
10. **Cross-check against the panel weights.** Optional. If the World Bank provides longitudinal weights on request, repeat the weighted sensitivity analysis.

## Ethics and governance

11. An ethics determination for secondary analysis of public de-identified data (two sources).
12. Follow the World Bank terms:
    - cite the dataset (doi:10.48529/s2n6-9f47);
    - publish aggregates only;
    - no redistribution;
    - no linking to other data.

## Authorship and repository

13. Confirm the author name and affiliation; `CITATION.cff` and `LICENSE` currently say "Isaac (Isaac25-lgtm)".
14. Decide whether to merge `investigation/strengthen-contribution` into `main`, and whether to publish the dashboard.
