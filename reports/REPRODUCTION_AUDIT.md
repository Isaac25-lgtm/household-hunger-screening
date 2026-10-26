# Reproduction audit

**Question:** do the earlier exploratory values (directive §3, dated 26 Oct 2026) reproduce when recomputed independently from the downloaded publisher bytes with new code?

**Answer:** **Yes, 48 of 48 compared quantities reproduce within the prespecified tolerance.** Nothing was tuned towards the earlier numbers. Those values live only in `config/previous_findings.yaml` and are read only by the comparison step in `pipeline.reproduction_table`. Machine-readable table: [`data/public_aggregates/reproduction_comparison.csv`](../data/public_aggregates/reproduction_comparison.csv) (also [`tables/tableS4_reproduction.md`](../tables/tableS4_reproduction.md)).

## Tolerances (set before comparison)

| Quantity type | Tolerance | Reason |
|---|---|---|
| Counts, selected slot | exact | deterministic |
| Point estimates and bounds (reported to 0.1 pp) | 0.05 pp | rounding of the earlier report |
| Bootstrap interval endpoints | 0.6 pp | Monte Carlo error plus unknown earlier seed/implementation |

## Status by claim group

| Group | Status | Notes |
|---|---|---|
| Source archive (9,098,158 bytes; SHA-256 `de2ae59d…66bb`) | **Replicated** | Both match exactly ([`source_provenance.json`](../data/public_aggregates/source_provenance.json)) |
| 4,744 phone records; 503 frame households (297/206); 483 observed households; 252 observed villages | **Replicated** | `integrity_checks.csv` |
| 227 / 67 complete six-window histories; 185 / 34 reference-positive | **Replicated** | exact |
| Missed 55.1 / 31.9 / 18.2 % (Malawi) and 69.6 / 47.5 / 30.7 % (Liberia) | **Replicated** | exact to rounding; exact rationals stored in `frontier.csv` |
| Bootstrap 95% intervals | **Replicated within MC tolerance** | Largest difference 0.50 pp (Liberia m = 3 upper: 37.5 vs 38.0). With 20,000 draws the Liberia m = 3 interval is 23.9–37.5%. Liberia endpoints sit on a coarse lattice (34 positives, 47 villages), so small implementation differences move them by up to ~0.5 pp |
| Missing-history bounds, m = 1 (50.8–59.3; 39.8–78.6) | **Replicated** | Independent exact algorithm, validated by brute force |
| + 5% label budget, m = 1 (39.6–65.0; 25.1–82.5) | **Replicated** | Independent exact Dinkelbach + DP; certificates F(λ*) = 0 |
| Timing: Jan–Feb (Malawi), Mar–Apr (Liberia); 13.6 / 58.1 % (2020); 21.6 / 54.5 % (2021 frozen); 59.8 / 60.2 % (2021 random) | **Replicated** | — |
| Matched cohorts 171 / 40; 20.2 / 61.5 % frozen; 59.8 / 63.5 % random; 13 Liberia reference-positive | **Replicated** | — |
| One household with two records in one designated slot; earliest kept | **Replicated** | Liberia, Mar–Apr 2020. The two records are HHS 1 and HHS 0, so the rule does **not** affect HHS ≥ 2 or ≥ 4 but **does** affect the secondary HHS ≥ 1 analysis for that household (logged) |
| 26 records with HHS ≥ 4 before the slot rule | **Replicated** | — |
| Dates agree with recorded months | **Replicated** | 0 mismatches |
| "Underlying HHS score could not be completely reconstructed" | **Confirmed and sharpened** | The public file contains only the three occurrence items (no frequency follow-ups). The score is consistent with them for all 4,741 records with complete items: yes-count ≤ HHS ≤ 2 × yes-count |

## Changed or newly qualified claims

These are not failures to reproduce. They are interpretive changes from re-examining the evidence.

1. **The random-window frontier is a design benchmark, not an operational schedule.** In Malawi, the fixed single window that is best in 2020 (Jan–Feb) misses 17.8% of the six-window cohort, against 55.1% for a random window. The best fixed two-window schedule misses 6.5% (in-sample). The headline "55% missed" must not be presented as what a sensible programme would experience.
2. **Liberia's timing choice is unstable.** Mar–Apr wins only 62% of 2,000 village-bootstrap re-selections in 2020, and the 2021 frozen-minus-random difference interval spans zero (−26.9 to +14.1 pp). The earlier write-up reported Liberia's timing numbers without this instability.
3. **Liberia's complete-history estimate is weakly identified.** Only 33% of the frame is complete, and the no-assumption range for m = 1 (39.8–78.6%) is about 7× wider than the bootstrap interval (63.9–75.0%).
4. **Severe hunger (HHS ≥ 4) is degenerate.** Every severe-reference household (Malawi 12, Liberia 2) was severe in exactly one window, so that frontier equals (6 − m)/6 and carries no information on intermittency.

## Unverified items

- The earlier bootstrap's seed and percentile definition were not recorded, so exact replicate-level agreement cannot be checked; only interval-level agreement is.
- The earlier "village sampling mechanics" (villages with ≥ 1 complete household vs all frame villages) are unknown. Both variants were run; their interval endpoints differ by at most 0.27 pp (Malawi) and 0.32 pp (Liberia) for m = 1–5 ([`tables/tableS3_bootstrap_stability.md`](../tables/tableS3_bootstrap_stability.md)).
