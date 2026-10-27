# TODO and blockers

## Blockers for submission (not for drafting)

- [ ] **Critical.** Re-read the source article's Methods/SI and the phone questionnaire; confirm the alternating-month call schedule and the HHS phone-item wording; consider contacting the source authors.
- [ ] **Critical.** Full-text review of McDonough & Millimet (2024) and a structured search of Google Scholar, SSRN, RePEc/NBER and grey literature (FEWS NET, WFP mVAM sentinel sites) for visit-frequency analyses.
- [ ] **Major.** Fix the manuscript's primary contrast (random frontier vs calendar/fixed schedule) and pre-register it.
- [ ] **Major.** Statistical review of the sharp-bound and shared-budget proofs.
- [ ] **Major.** Ethics determination for secondary analysis of public de-identified data.
- [ ] **Minor.** Confirm author name and affiliation for CITATION.cff and LICENSE.

## Engineering follow-ups (optional)

- [ ] Deploy the dashboard on Streamlit Community Cloud (requires the repository owner to sign in at share.streamlit.io; no secrets needed). Then record the URL and a health check here and in the README.
- [ ] Browser screenshots of the dashboard at phone and desktop widths.
- [ ] Add a type checker (pyright/mypy) to CI.
- [ ] Replicate on a second high-frequency panel (e.g. World Bank HFPS) to address external validity.

## From the contribution-strengthening investigation (27 Oct 2026)

See `reports/investigation/07_REQUIRED_WORK_BEFORE_SUBMISSION.md` for the full list. Owner decisions:

- [ ] Approve a protocol-locked test on other LSMS-HFPS countries (lock the protocol before downloading; needs your login).
- [ ] Decide whether to request MIRA monthly HHS data from CRS/Cornell (nothing sent).
- [ ] Confirm how World Bank HFPS rounds 19–21 sample groups A/B were assigned.
- [ ] Choose the manuscript framing (`reports/investigation/06_MANUSCRIPT_OPTIONS.md`).
- [ ] Push and/or merge `investigation/strengthen-contribution` (currently local only).

## Multi-country test: protocol locked, data download pending (27 Oct 2026)

Protocol: `reports/investigation/10_LOCKED_PROTOCOL_MULTICOUNTRY_HFPS.md` (commit `8d33f4d`, SHA-256 `23afabbe…5ba6d`; parameters `config/multicountry_protocol.yaml`, SHA-256 `a8ba13f0…f7324`).
Scripted login to the Microdata Library is not possible (the login POST returns an empty response, probably bot protection), so please download each **Stata** archive from the "Get Microdata" page in your browser and save it unchanged:

- [ ] Burkina Faso, catalog 3768: `data/raw/multicountry/BFA/`
- [ ] Ethiopia, catalog 3716: `data/raw/multicountry/ETH/`
- [ ] Nigeria 2020–21, catalog 3712: `data/raw/multicountry/NGA2020/`
- [ ] Nigeria 2021–24, catalog 4444: `data/raw/multicountry/NGA2021/`
- [ ] Uganda, catalog 3765: `data/raw/multicountry/UGA/`
- [ ] Tanzania, catalog 4542: `data/raw/multicountry/TZA/`

Do not open the files before the analysis runs. Everything under `data/raw/` is gitignored.
- [x] Multi-country archives downloaded (27 Oct 2026) and analysed under the locked protocol; see `reports/investigation/11_MULTICOUNTRY_RESULTS.md`.
- [ ] Optional: download the Tanzania **CSV** release (catalog 4542) to recover round 9; it cannot change the Tanzania verdict (subsample module) but completes the record.
- [ ] Rotate the World Bank password.
