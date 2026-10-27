# Limitations and unresolved-claims register

## Claims register

| # | Claim | Status | Evidence | What would change the status |
|---|---|---|---|---|
| 1 | Baseline Malawi and Liberia results reproduce from the raw data | **Supported** | Independent script; 48/48 baseline checks | — |
| 2 | The two-month windows match the actual call schedule | **Supported by the dates**; documentation still to confirm | 94% of households keep the same month parity; median gap 61 days | Source methods or authors |
| 3 | In Malawi, a January–March contact misses fewer households positive at any observed contact than a random contact | **Supported descriptively in two panels, six comparisons** | §5.1–5.2 of the full report | A blind test; month-level HHS data |
| 4 | December/November contacts do the same | **Not supported** (inconsistent) | Nov 2020 worst; Dec 2020 ≈ random; Dec 2023 best | — |
| 5 | Choosing the month from one earlier year transfers to later years | **Conditional**: yes after a typical year (Aggarwal), no after a training period starting at the pandemic onset (World Bank) | Transfer tests | More years and countries |
| 6 | A fixed January–March calendar rule beats learning the month from data | **Plausible, not tested blind** | Holds wherever testable | Protocol-locked multi-country test |
| 7 | The timing advantage is robust to missing interviews | **Supported** (exact ranges; primary outcomes) | §5.3 | — |
| 8 | The timing advantage is robust to response error | **Not established**: worst-case error in 0.5–2.5% of answers erases it | §5.3 | Evidence on real error rates; random-error sensitivity |
| 9 | Lean-season screening mainly helps poorer and rural households | **Exploratory** | §5.4; 22 unadjusted comparisons | Pre-specified test in new data |
| 10 | A second contact to warning-sign households beats random re-contact | **Supported in the World Bank panel**; mixed in the Aggarwal data | §5.5 | Replication |
| 11 | Machine learning improves second-contact targeting | **Not supported** (no gain over a count rule) | `hfps_model_vs_rule.csv` | — |
| 12 | The World Bank item s8q7 measures HHS ≥ 2 | **Must not be claimed** | Different wording; HHS-analogue concordance 86–98% in 2024 only | — |
| 13 | National, annual or IPC prevalence | **Must not be claimed** | Reference = observed contacts; complete-case panels | — |
| 14 | Fewer interviews *cause* missed households in practice, or better screening improves assistance or health | **Must not be claimed** | Retrospective removal of observed interviews | A prospective design |
| 15 | Cost-effectiveness | **Must not be claimed** | No per-contact costs | Documented costs |
| 16 | First study of screening timing or frequency | **Must not be claimed** | IndiKit guidance; Zhu et al. 2026; Wollburg et al. 2025; Smith et al. 2026 | — |
| 17 | Results generalise beyond Malawi | **Unknown** | Liberia inconclusive | Multi-country test |

## Limitations

### Measurement
- The two datasets use different instruments: HHS against single FIES items, both with 30-day recall.
- Phone mode in both datasets.
- No validation against a true hunger state.
- Each contact recalls only 30 days, so a 61-day call cycle (Aggarwal) leaves about half of the calendar unobserved.
- World Bank rounds 11 and 12 overlap in recall (99.7% of gaps are under 30 days).

### Reference definition
- "Ever positive" depends on how many contacts the horizon has, and it saturates: 83% of complete World Bank households after ten rounds. Missed shares are therefore horizon-specific.

### Selection
- All analyses use complete-case cohorts. In the Aggarwal data, attrition is associated with baseline traits (baseline report).
- The World Bank sample already excludes the 27% of the IHPS 2019 frame without a phone contact. Weights adjust for attrition only cross-sectionally.

### Design confounding
- World Bank round 1 combines the pandemic onset and the first interview.
- Round number and calendar time cannot be separated in either panel.

### Inference
- No PSU or strata in the World Bank public data. District-cluster intervals are approximate.
- Data-driven selection and in-sample "best" schedules are optimistic.
- No adjustment for multiple comparisons.

### Exposure
- Nothing in this investigation is a blind test (see `00_PROTOCOL_AND_EXPOSURE_LOG.md`).

### External validity
- Two Malawi panels: one of rural trial controls, one a national phone panel of urban and rural households (33% urban in round 1; the IHPS sampling design was not reviewed).
- Liberia is too small to conclude anything about timing.
