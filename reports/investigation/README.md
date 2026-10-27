# Contribution-strengthening investigation (October 2026)

Can the household hunger screening study make a materially stronger contribution? Start with the decision memo, then the full report.

| File | Contents |
|---|---|
| [02_DECISION_MEMO.md](02_DECISION_MEMO.md) | Plain-English findings and recommendation |
| [01_FULL_INVESTIGATION_REPORT.md](01_FULL_INVESTIGATION_REPORT.md) | Full scientific report with numerators, denominators, uncertainty and reproduction steps |
| [00_PROTOCOL_AND_EXPOSURE_LOG.md](00_PROTOCOL_AND_EXPOSURE_LOG.md) | What was already seen, and the analysis specification frozen before the new household-level results |
| [03_DATASET_INVENTORY_AND_ACCESS_LEDGER.md](03_DATASET_INVENTORY_AND_ACCESS_LEDGER.md) (+ `.csv`) | Datasets, licences, provenance and access barriers |
| [04_CLOSEST_PRIOR_WORK.md](04_CLOSEST_PRIOR_WORK.md) | Head-to-head comparison with the closest studies |
| [05_NEGATIVE_FAILED_UNSTABLE_BLOCKED_TESTS.md](05_NEGATIVE_FAILED_UNSTABLE_BLOCKED_TESTS.md) | Everything that did not work, was unstable, or was blocked |
| [06_MANUSCRIPT_OPTIONS.md](06_MANUSCRIPT_OPTIONS.md) | Paper structures and carefully worded titles |
| [07_REQUIRED_WORK_BEFORE_SUBMISSION.md](07_REQUIRED_WORK_BEFORE_SUBMISSION.md) | Data access, confirmations, statistical review, ethics |
| [08_LIMITATIONS_AND_UNRESOLVED_CLAIMS.md](08_LIMITATIONS_AND_UNRESOLVED_CLAIMS.md) | Claims register and limitations |
| [09_INVESTIGATION_HANDOFF.md](09_INVESTIGATION_HANDOFF.md) | What changed, what was tested, what remains, and what was pushed |
| [10_LOCKED_PROTOCOL_MULTICOUNTRY_HFPS.md](10_LOCKED_PROTOCOL_MULTICOUNTRY_HFPS.md) | Protocol for the multi-country test, locked before access to household- and item-level outcomes (five countries assessed) |
| [11_MULTICOUNTRY_RESULTS.md](11_MULTICOUNTRY_RESULTS.md) | **Results of the locked test.** The calendar rule was contradicted; the second-contact rule was supported |

## Data sources and citations

Producers, versions and DOIs below are taken from each catalog's metadata (World Bank Microdata Library API, 27 October 2026). Before submission, use the exact citation text given on each catalog page. This repository contains **aggregate results only**. The microdata are not redistributed, linked to other data or used to identify anyone, in line with the World Bank Microdata Library terms of use.

| Survey | Producer | Version (study ID) | Catalog | DOI |
|---|---|---|---|---|
| Malawi High-Frequency Phone Survey 2020–2024 | Malawi National Statistical Office (NSO) | Version 20 (MWI_2020-2024_HFPS_v20_M) | [3766](https://microdata.worldbank.org/catalog/3766) | [10.48529/s2n6-9f47](https://doi.org/10.48529/s2n6-9f47) |
| Burkina Faso High Frequency Phone Survey 2020–2024 | Institut National de la Statistique et de la Démographie (INSD) | Version 23 (BFA_2020-2024_HFPS_v23_M) | [3768](https://microdata.worldbank.org/catalog/3768) | [10.48529/fr7b-at30](https://doi.org/10.48529/fr7b-at30) |
| Ethiopia High Frequency Phone Survey 2020–2024 | World Bank | Version 15 (ETH_2020-2024_HFPS_v15_M) | [3716](https://microdata.worldbank.org/catalog/3716) | [10.48529/th6s-nv42](https://doi.org/10.48529/th6s-nv42) |
| Nigeria COVID-19 National Longitudinal Phone Survey 2020–2021 | National Bureau of Statistics (NBS) | Version 12 (NGA_2020_NLPS_v12_M) | [3712](https://microdata.worldbank.org/catalog/3712) | [10.48529/xeym-xv94](https://doi.org/10.48529/xeym-xv94) |
| Nigeria National Longitudinal Phone Survey 2021–2024 | National Bureau of Statistics (NBS) | Version 10 (NGA_2021-2024_NLPS_v10_M) | [4444](https://microdata.worldbank.org/catalog/4444) | [10.48529/nj3q-v243](https://doi.org/10.48529/nj3q-v243) |
| Uganda High-Frequency Phone Survey 2020–2024 | Uganda Bureau of Statistics (UBOS) | Catalog states "Version 16"; study ID UGA_2020-2024_HFPS_v17_M | [3765](https://microdata.worldbank.org/catalog/3765) | [10.48529/pg7v-3896](https://doi.org/10.48529/pg7v-3896) |
| Tanzania High Frequency Welfare Monitoring Phone Survey 2021–2024 | National Bureau of Statistics | Version 09 (TZA_2021-2024_HFWMPS_v09_M) | [4542](https://microdata.worldbank.org/catalog/4542) | [10.48529/mggv-3b76](https://doi.org/10.48529/mggv-3b76) |
| Aggarwal et al. (2022) supporting data (Liberia, Malawi) | PLOS ONE (CC BY 4.0) | S1 Data | — | [10.1371/journal.pone.0271488](https://doi.org/10.1371/journal.pone.0271488) |

The SHA-256 checksums of the archives analysed are recorded in `data/public_aggregates/investigation/hfps_summary.json` (Malawi) and `data/public_aggregates/multicountry/summary.json` (the other five countries).
