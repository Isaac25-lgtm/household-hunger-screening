# Data quality and cohort flow

## 1. Source and provenance

| Item | Value |
|---|---|
| Article | Aggarwal S, Jeong D, Kumar N, Park DS, Robinson J, Spearot A (2022). *COVID-19 market disruptions and food security: Evidence from households in rural Liberia and Malawi.* PLOS ONE 17(8): e0271488. doi:10.1371/journal.pone.0271488 |
| Supplement | S1 Data, doi:10.1371/journal.pone.0271488.s021 |
| Retrieved | 2026-10-26 20:27 UTC from the publisher URL (HTTP 200, redirected to the PLOS Google Cloud Storage corpus) |
| Archive | 9,098,158 bytes; SHA-256 `de2ae59d6190d70722b3aac33a9363e23ebea907ca639f7224bca2d9b11b66bb` (matches the earlier record exactly) |
| Members used | `hhps_analysis_fullsample.dta` (phone interviews), `baseline_analysis_fullsample.dta` (baseline phone frame). The archive has 14 data/doc members plus `__MACOSX` resource forks (ignored) |
| Licence | PLOS ONE content and supporting information: CC BY 4.0. Redistribution would be legal with attribution, but record-level files are **not** committed (directive policy; the identifiers are pseudonymous but household-level) |
| Local inputs | No source files existed in the researcher's local source folder (it held only an unrelated project). The earlier dossier, report and evidence ZIP named in the directive were **not found**, so all evidence was regenerated |

The supplement's `readme.docx` and `replication_dofile.do` were read. The do-file's attrition section states the design assumption that "roughly half are to be called for each calendar month" (Malawi 297 control households, Liberia wave-2 206). This supports one designated interview per household per two-month window.

## 2. Schema and integrity checks (22/22 pass)

From [`integrity_checks.csv`](../data/public_aggregates/integrity_checks.csv):

- Baseline frame: 503 rows (Malawi 297, Liberia 206); `id` unique; **no** household-ID or village-ID collisions across countries; every household nested in one village.
- Phone file: 4,744 records, all matched to the frame; country and village agree with baseline for every record; `key` (submission ID) unique; 483 households and 252 villages observed.
- Dates: `survey_date` falls in the month of `survey_month` for every record; no repeated household-month.
- HHS: 1 missing value (Malawi); no out-of-range or non-integer values; 26 records with HHS ≥ 4.
- Analytic weight `wgt` = 1 for all records (no design weighting; this confers no representativeness).

**HHS reconstruction.** Only the three occurrence items (`i3_1_nofood_4w`, `i3_2_night_4w`, `i3_3_wholeday_4w`) are present; the frequency follow-ups are not. Under FANTA coding (rarely/sometimes = 1, often = 2), any valid score satisfies yes-count ≤ HHS ≤ 2 × yes-count, and **all 4,741 records with complete items satisfy it** ([`hhs_item_crosstab.csv`](../data/public_aggregates/hhs_item_crosstab.csv)). The source-provided score is used. HHS = 0 coincides exactly with zero affirmative items. The phone items are worded "past 4 weeks", consistent with the 30-day HHS recall.

**Variables and coding.** `pandas.read_stata(convert_categoricals=False)` was used. The full variable dictionary (names, labels, types, missingness; no values) is in [`data_dictionary.csv`](../data/public_aggregates/data_dictionary.csv). No negative or special missing codes were found in the HHS variables. Stata missing values are read as NaN.

## 3. Design reconstruction

- Phone fieldwork: Malawi Jul 2019 – Aug 2021; Liberia Jan 2020 – Oct 2021 ([`monthly_record_counts.csv`](../data/public_aggregates/monthly_record_counts.csv)).
- Designated window ("slot") *s* of a year = calendar months 2s−1 and 2s. Six windows in 2020; four (Jan–Aug) are observed in both 2020 and 2021 for both countries.
- **Duplicate rule (outcome-blind):** one household-slot (Liberia, Mar–Apr 2020) had two records. The earliest dated record was kept. A record with valid HHS is preferred over one with missing HHS (this uses missingness, never the value; it did not bind here).

## 4. Cohort flow

| Step | Malawi | Liberia |
|---|---:|---:|
| Baseline phone-frame households | 297 | 206 |
| Baseline phone-frame villages | 150 | 104 |
| Phone interview records (all months) | 3,408 | 1,336 |
| Records with valid HHS | 3,407 | 1,336 |
| Households with ≥ 1 phone record | 297 | 186 |
| Records after one-per-slot rule | 3,407 | 1,335 |
| 2020 designated-slot screens with valid HHS | 1,655 | 818 |
| Households with ≥ 1 valid 2020 screen | 294 | 182 |
| **Households with all six valid 2020 screens** | **227 (76%)** | **67 (33%)** |
| Villages with ≥ 1 complete household | 140 | 47 |
| **Complete households reference-positive (HHS ≥ 2)** | **185** | **34** |
| *Timing design:* complete in Jan–Aug 2020 / 2021 / both | 249 / 197 / 171 | 89 / 60 / 40 |

See Figure 1 and [`cohort_flow.csv`](../data/public_aggregates/cohort_flow.csv). Twenty Liberia frame households never appear in the phone file (`hhps_ever = 0` in baseline).

## 5. Missingness and attrition

- Window-level follow-up in 2020: Malawi 89–96%, Liberia 58–74%. Liberia declines to 46–57% in 2021 (Figure 8).
- Malawi: 70 households have at least one missing 2020 window (3 have none observed). Liberia: 139 (24 have none observed).
- **Who completes?** ([`tableS1_attrition_balance.md`](../tables/tableS1_attrition_balance.md); OLS on a completeness indicator, CR1 village-clustered SEs; descriptive.)
  - Liberia: complete households have fewer female respondents (−15.6 pp, SE 7.2), older respondents (+5.2 y, SE 2.4) and fewer thatch roofs (−12.5 pp, SE 6.2). Baseline HHS ≥ 2 is not clearly different (+7.7 pp, SE 6.7).
  - Malawi: completers have fewer thatch roofs (−18.6 pp, SE 6.9) and higher expenditure (+0.27 log points, SE 0.13). Baseline HHS ≥ 2 is essentially equal (+0.6 pp, SE 6.9).
  - With 14 tests, about one nominal |z| > 2 is expected by chance; four or five were observed, which suggests real but modest selection on socioeconomic markers, not clearly on baseline hunger.
- Consequences: (i) complete-history results describe a selected subset, especially in Liberia; (ii) the assumption-free bounds (Table 3) are the honest summary for the frame; (iii) an IPW estimate under MAR-given-baseline is almost identical to the complete-case estimate (Malawi 54.9% vs 55.1%; Liberia 70.3% vs 69.6%). That means only that *observed* baseline covariates do not explain selection on 2020 hunger histories, not that selection is ignorable.
