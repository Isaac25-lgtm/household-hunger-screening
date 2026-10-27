"""Automated quality control for the manuscript package.

Checks a staged (or extracted) package folder against the canonical aggregate files:
  * main-table cells recomputed independently from data/public_aggregates;
  * observed-count columns are integers;
  * banned or superseded claims, and known wrong roundings, do not appear in documents;
  * no local absolute paths, credentials, identifier columns or private file types;
  * figures are valid PNG / PDF / SVG files and every main figure has all three formats;
  * the manifest matches the files.
Each check returns rows of (check, target, status, detail). Status is PASS or FAIL.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd

TEXT_EXT = {".md", ".csv", ".txt", ".py", ".yaml", ".yml", ".toml", ".json", ".cff", ".ps1", ".cfg", ".ini"}
FORBIDDEN_EXT = {".dta", ".zip", ".sav", ".parquet", ".feather", ".pkl", ".pickle", ".rds", ".env"}
ID_COLUMNS = {"id", "id_str", "key", "village_id", "household_id", "hhid", "phone", "gps", "latitude", "longitude", "name",
              "y4_hhid", "hh", "case_id", "ea_id"}
SECRET_PATTERNS = [re.compile(p) for p in (
    r"ghp_[A-Za-z0-9]{30,}", r"github_pat_[A-Za-z0-9_]{30,}", r"gho_[A-Za-z0-9]{30,}", r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", r"xox[baprs]-[A-Za-z0-9-]{10,}", r"sk-[A-Za-z0-9]{32,}",
    r"(?i)password\s*[:=]\s*\S{4,}")]
LOCAL_PATH = re.compile(r"\b[A-Z]:[\\/]+(?:Users|MY FILES)[\\/]|/(?:home|Users)/[A-Za-z0-9_.-]+/")

# Superseded or banned wording. Allowed only in the files listed (historical records and the audit trail itself).
AUDIT_DOCS = {"CHANGELOG_FROM_PREVIOUS_PACKAGE.md", "FINAL_PACKAGE_AUDIT.md", "NUMERICAL_RECONCILIATION.md",
              "TEST_AND_RELEASE_REPORT.md", "old_to_new_filename_mapping.csv", "qc_checks.csv",
              "previous_package_2026-10-27_manifest.txt", "DEVELOPMENT_LOG.md"}
BANNED = [
    ("superseded label", re.compile(r"(?i)five[- ]country (test|analysis|investigation)"), {"10_LOCKED_PROTOCOL_MULTICOUNTRY_HFPS.md"}),
    ("overclaim", re.compile(r"(?i)surviv\w* any pattern"), set()),
    ("overclaim", re.compile(r"(?i)prespecified and blind"), set()),
    ("overclaim", re.compile(r"(?i)genuinely out-of-sample"), set()),
    ("wording", re.compile(r"(?i)(?<![\"'])\ba[- ]priori\b(?![\"'])"), set()),
    ("wrong rounding", re.compile(r"\+4\.8 to \+7\.8|10\.5 per 100|36\.2 per 100|\+6\.5 \(\+4\.4"), set()),
    ("non-canonical CI", re.compile(r"-46\.5 to -29\.6"), {"REVIEW_RESPONSE.md", "TableS17_window_paired_comparisons.md",
                                                           "TableS17_window_paired_comparisons.csv"}),
]
FULLY_BLIND = re.compile(r"(?i)fully blind")


def _norm(s: str) -> str:
    return s.replace("−", "-").replace("–", "-")


def _row(check, target, ok, detail=""):
    return {"check": check, "target": target, "status": "PASS" if ok else "FAIL", "detail": detail}


def _p1(x):
    return f"{100 * x:.1f}%"


def _d1(x):
    return f"{100 * x:+.1f}"


def _ci(lo, hi):
    return f"{100 * lo:+.1f} to {100 * hi:+.1f}"


# ------------------------------------------------------------------ canonical values
def canonical_values(pub: Path) -> pd.DataFrame:
    """One canonical displayed value per key quantity, with its source and evidence class."""
    rv, mc, inv = pub / "review", pub / "multicountry", pub / "investigation"
    rows = []

    def add(key, quantity, display, unrounded, source, cls):
        rows.append({"quantity_key": key, "quantity": quantity, "display": display, "unrounded": unrounded, "source_file": source,
                     "evidence_class": cls})

    f = pd.read_csv(pub / "frontier.csv")
    for c in ("Malawi", "Liberia"):
        r = f[(f.country == c) & (f.m == 1) & (f.threshold == 2)].iloc[0]
        add(f"frontier_{c}_m1", f"{c}: missed with one random screen of six (2020)", _p1(r.missed_fraction),
            r.missed_fraction, "frontier.csv", "Exact design quantity")
        add(f"frontier_{c}_m1_ci", f"{c}: 95% village bootstrap CI", f"{100 * r.ci_low:.1f} to {100 * r.ci_high:.1f}%",
            f"{r.ci_low};{r.ci_high}", "frontier.csv", "Sampling uncertainty")
    mb = pd.read_csv(pub / "missing_bounds.csv")
    for c in ("Malawi", "Liberia"):
        r = mb[(mb.country == c) & (mb.m == 1)].iloc[0]
        add(f"frame_range_{c}_m1", f"{c}: full-frame identification range, one screen", f"{100 * r.lower:.1f} to {100 * r.upper:.1f}%",
            f"{r.lower};{r.upper}", "missing_bounds.csv", "Identification range (not a CI)")
    cal = pd.read_csv(rv / "calendar_lean_season_sensitivity.csv")
    r = cal[(cal.country == "Malawi") & cal.horizon.str.startswith("Jul 2020")].iloc[0]
    add("lead_missed", "Jul 2020 - Jun 2021: Jan-Feb missed", _p1(r.window_missed), r.window_missed, "review/calendar_lean_season_sensitivity.csv",
        "Out-of-time, not blind")
    add("lead_random", "Jul 2020 - Jun 2021: random missed", _p1(r.random_missed), r.random_missed, "same", "Out-of-time, not blind")
    add("lead_diff", "Jul 2020 - Jun 2021: difference (pp)", _d1(r["diff"]), r["diff"], "same", "Out-of-time, not blind")
    add("lead_ci", "Jul 2020 - Jun 2021: 95% CI (pp)", _ci(r.diff_ci_low, r.diff_ci_high), f"{r.diff_ci_low};{r.diff_ci_high}", "same",
        "Out-of-time, not blind")
    add("lead_n", "Jul 2020 - Jun 2021: reference positives", str(int(r.n_reference_positive)), r.n_reference_positive, "same", "Count")
    tv = pd.read_csv(pub / "timing_validation.csv")
    t = tv[(tv.country == "Malawi") & (tv.cohort == "2021 complete four-slot cohort")].iloc[0]
    add("jan_aug_2021_missed", "Jan - Aug 2021: Jan-Feb missed", _p1(t.missed_frozen), t.missed_frozen, "timing_validation.csv", "Out-of-time, not blind")
    add("jan_aug_2021_diff", "Jan - Aug 2021: difference (pp)", _d1(t.missed_frozen - t.missed_random_one_slot),
        t.missed_frozen - t.missed_random_one_slot, "timing_validation.csv", "Out-of-time, not blind")
    add("jan_aug_2021_ci", "Jan - Aug 2021: 95% CI (pp), canonical", _ci(t.diff_ci_low, t.diff_ci_high), f"{t.diff_ci_low};{t.diff_ci_high}",
        "timing_validation.csv", "Out-of-time, not blind")
    w = pd.read_csv(rv / "window_paired_comparisons.csv")
    lead = w[w.horizon == "Jul 2020 - Jun 2021 (six windows)"]
    b = lead[lead.is_best_observed].iloc[0]
    add("lead_best_window", "Jul 2020 - Jun 2021: best observed window", f"{b.window} {_p1(b.missed)}", b.missed,
        "review/window_paired_comparisons.csv", "Post hoc paired comparison")
    fp = pd.read_csv(rv / "frozen_best_pair.csv").iloc[0]
    add("frozen_pair", "Frozen best pair, missed vs random pair", f"{_p1(fp.test_missed_frozen_pair)} vs {_p1(fp.test_missed_random_pair)}",
        f"{fp.test_missed_frozen_pair};{fp.test_missed_random_pair}", "review/frozen_best_pair.csv", "Out-of-time, not blind")
    h1 = pd.read_csv(mc / "h1_calendar_rule.csv")
    for c in ("BFA", "UGA"):
        r = h1[(h1.country == c) & (h1.horizon_start_year == 2020)].iloc[0]
        add(f"h1_{c}", f"H1 {c} 2020-21: rule minus random (pp) and 95% CI", f"{_d1(r['diff'])} ({_ci(r.diff_ci_low, r.diff_ci_high)})",
            r["diff"], "multicountry/h1_calendar_rule.csv", "Protocol-locked, not fully blind")
    h3 = pd.read_csv(mc / "h3_second_contact.csv")
    for _, r in h3[h3.analysis.str.startswith("primary") & h3.difference.notna()].iterrows():
        add(f"h3_{r.country}_{r.horizon_start_year}", f"H3 {r.country} {r.horizon_start_year}: per 100 re-contacted, rule vs random; difference (CI)",
            f"{r.warning_per_100:.1f} vs {r.random_per_100:.1f}; {r.difference:+.1f} ({r.ci_low:+.1f} to {r.ci_high:+.1f})",
            r.difference, "multicountry/h3_second_contact.csv", "Protocol-locked, not fully blind")
    hh = pd.read_csv(rv / "h2_h4_results.csv")
    for _, r in hh[hh.eligible & hh.status.str.startswith("prespecified")].iterrows():
        add(f"{r.hypothesis.split()[0].lower()}_{r.country}", f"{r.hypothesis} {r.country} {r.horizons}",
            f"{r.estimate_pp:+.1f} ({r.ci_low_pp:+.1f} to {r.ci_high_pp:+.1f})", r.estimate_pp, "review/h2_h4_results.csv",
            "Protocol-locked, not fully blind")
    rob = pd.concat([pd.read_csv(inv / "aggarwal_timing_robustness.csv"), pd.read_csv(inv / "hfps_decision_robustness.csv")])
    rob = rob[(rob.alpha == 0) & ~rob.analysis.str.contains("Liberia|7/8/9/11/12")]
    for _, r in rob.iterrows():
        tag = r.analysis + ("" if pd.isna(r.get("item")) else f" {r['item']}")
        add(f"tipping_{len(rows)}", f"Tipping point: {tag}", f"{int(r.tipping_budget_to_reach_zero)}/{int(r.observed_screens)}",
            r.tipping_budget_share_of_observed_screens, "investigation/*_robustness.csv", "Post hoc sensitivity")
    add("ranges_excluding_zero", "Missing-history ranges excluding zero (lead comparisons)", f"{int((rob.upper < 0).sum())} of {len(rob)}",
        (rob.upper < 0).sum(), "investigation/*_robustness.csv", "Post hoc sensitivity")
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ main tables
def _cell(df, col, **match):
    m = pd.Series(True, index=df.index)
    for k, v in match.items():
        m &= df[k].astype(str) == str(v)
    sub = df.loc[m, col]
    return None if sub.empty else str(sub.iloc[0])


def check_main_tables(tables: Path, pub: Path) -> list[dict]:
    """Recompute key cells of the main tables directly from the aggregate files (independent of the table code)."""
    out = []
    rd = {n: pd.read_csv(p, dtype=str, keep_default_na=False) for n, p in
          ((p.stem, p) for p in tables.glob("Table*.csv"))}
    t1, t2, t3, t4 = (next((v for k, v in rd.items() if k.startswith(f"Table{i}_")), None) for i in (1, 2, 3, 4))
    for name, t in (("Table1", t1), ("Table2", t2), ("Table3", t3), ("Table4", t4)):
        out.append(_row("main table present", name, t is not None))
    if t1 is not None:
        for c in ("Malawi", "Liberia"):
            ok = t1[c].str.fullmatch(r"\d+").all()
            out.append(_row("integer counts", f"Table1 {c}", ok, "" if ok else "non-integer cell"))
    if t2 is not None:
        f = pd.read_csv(pub / "frontier.csv")
        f = f[(f.threshold == 2) & f.m.isin([1, 2, 3])]
        for _, r in f.iterrows():
            got = _cell(t2[t2.Panel.str.startswith("A.")], "Missed share or range", Country=r.country, **{"Screens retained of 6": int(r.m)})
            out.append(_row("cell matches source", f"Table2 A {r.country} m={int(r.m)}", got == _p1(r.missed_fraction),
                            f"table {got}; source {_p1(r.missed_fraction)}"))
        mb = pd.read_csv(pub / "missing_bounds.csv")
        for _, r in mb[mb.m.isin([1, 2, 3])].iterrows():
            exp = f"{100 * r.lower:.1f} to {100 * r.upper:.1f}%"
            got = _cell(t2[t2.Panel.str.startswith("B.")], "Missed share or range", Country=r.country, **{"Screens retained of 6": int(r.m)})
            out.append(_row("cell matches source", f"Table2 B {r.country} m={int(r.m)}", got == exp, f"table {got}; source {exp}"))
        b_lab = t2[t2.Panel.str.startswith("B.")].Panel.str.contains("not a CI").all()
        out.append(_row("label", "Table2 panel B labelled 'not a CI'", bool(b_lab)))
        for c in ("Households",):
            ok = t2[c].str.fullmatch(r"\d+").all()
            out.append(_row("integer counts", f"Table2 {c}", ok))
    if t3 is not None:
        cv = canonical_values(pub).set_index("quantity_key").display
        lead = t3.iloc[0]
        for col, key in (("Window missed", "lead_missed"), ("Random missed", "lead_random"), ("Difference (pp)", "lead_diff"),
                         ("95% CI (pp)", "lead_ci"), ("Reference-positive households", "lead_n")):
            out.append(_row("cell matches source", f"Table3 lead row {col}", lead[col] == cv[key], f"table {lead[col]}; source {cv[key]}"))
        out.append(_row("lead row", "Table3 first row is Jul 2020 - Jun 2021", lead["Analysis period"].startswith("Jul 2020 - Jun 2021")))
        r21 = t3[t3["Analysis period"].str.startswith("Jan - Aug 2021")].iloc[0]
        out.append(_row("cell matches source", "Table3 Jan-Aug 2021 CI (canonical)", r21["95% CI (pp)"] == cv["jan_aug_2021_ci"],
                        f"table {r21['95% CI (pp)']}; source {cv['jan_aug_2021_ci']}"))
        out.append(_row("label", "Table3 World Bank panel present and marked not HHS",
                        bool(t3.Panel.str.contains("World Bank").any() and t3.Panel.str.contains("not the HHS").any())))
        out.append(_row("label", "Table3 failed transfers shown", bool((t3.Note == "Failed transfer").any())))
        for c in ("Complete households", "Reference-positive households"):
            out.append(_row("integer counts", f"Table3 {c}", bool(t3[c].str.fullmatch(r"\d+").all())))
    if t4 is not None:
        h1 = pd.read_csv(pub / "multicountry" / "h1_calendar_rule.csv")
        for _, r in h1[h1.analysis.str.startswith("primary")].iterrows():
            row = t4[(t4.Hypothesis == "H1 calendar rule") & (t4["Contact chosen"] == r.rule_round)]
            got = None if row.empty else row.iloc[0]["Difference"]
            exp = _d1(r["diff"]) + " pp"
            out.append(_row("cell matches source", f"Table4 H1 {r.country}", got == exp, f"table {got}; source {exp}"))
        h3 = pd.read_csv(pub / "multicountry" / "h3_second_contact.csv").dropna(subset=["difference"])
        for _, r in h3.iterrows():
            row = t4[(t4.Hypothesis == "H3 second-contact rule") & (t4.Denominator == f"{int(r.recontact_budget)} re-contacted")]
            got = None if row.empty else row.iloc[0]["95% CI"]
            exp = f"{r.ci_low:+.1f} to {r.ci_high:+.1f} per 100"
            out.append(_row("cell matches source", f"Table4 H3 {r.country} {r.horizon_start_year} ({int(r.recontact_budget)})", got == exp,
                            f"table {got}; source {exp}"))
        out.append(_row("label", "Table4 eligibility rows for Ethiopia, Nigeria, Tanzania",
                        all(t4["Country and horizon"].str.contains(c).any() for c in ("Ethiopia", "Nigeria", "Tanzania"))))
    return out


# ------------------------------------------------------------------ text, privacy, files
def _is_doc(rel: str) -> bool:
    """Documents whose wording is checked (prose and tables). Code is excluded: it may contain patterns as data."""
    if rel.startswith("06_code_snapshot/"):
        return rel.endswith(".md") and "/tests/" not in rel and "/src/" not in rel and "/scripts/" not in rel
    return rel.endswith((".md", ".csv", ".txt"))


def check_text(stage: Path) -> list[dict]:
    out, hits = [], []
    for p in sorted(stage.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in TEXT_EXT:
            continue
        rel = p.relative_to(stage).as_posix()
        text = p.read_text(encoding="utf-8", errors="replace")
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                hits.append(("credential pattern", rel, pat.pattern))
        if LOCAL_PATH.search(text):
            hits.append(("local absolute path", rel, LOCAL_PATH.search(text).group(0)))
        if not _is_doc(rel) or p.name in AUDIT_DOCS or rel.startswith("03_results_data/"):
            continue
        norm = _norm(text)
        for kind, pat, allow in BANNED:
            if p.name in allow:
                continue
            m = pat.search(norm)
            if m:
                hits.append((kind, rel, m.group(0)))
        for line in norm.splitlines():
            if FULLY_BLIND.search(line) and not re.search(r"(?i)(not|or|nor|no analysis[^.]*)\s+(?:\w+\s+)?fully blind|complete blinding", line):
                hits.append(("overclaim", rel, line.strip()[:120]))
    out.append(_row("banned wording, credentials and local paths", "all text files", not hits,
                     "; ".join(f"{k}: {r}: {m}" for k, r, m in hits[:20])))
    return out, hits


def check_files(stage: Path) -> list[dict]:
    out = []
    bad_ext = [p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file() and p.suffix.lower() in FORBIDDEN_EXT]
    out.append(_row("no private file types", "all files", not bad_ext, ", ".join(bad_ext[:10])))
    bad_dir = [p.relative_to(stage).as_posix() for p in stage.rglob("*")
               if p.is_file() and ({"raw", "interim", "processed_private"} & set(p.relative_to(stage).parts))]
    out.append(_row("no raw or interim folders", "all files", not bad_dir, ", ".join(bad_dir[:10])))
    id_hits = []
    for p in stage.rglob("*.csv"):
        if p.stat().st_size == 0:
            continue
        try:
            cols = {c.strip().lower() for c in pd.read_csv(p, nrows=0).columns}
        except Exception as e:  # noqa: BLE001
            id_hits.append(f"{p.name}: unreadable ({e})")
            continue
        if cols & ID_COLUMNS:
            id_hits.append(f"{p.relative_to(stage).as_posix()}: {sorted(cols & ID_COLUMNS)}")
    out.append(_row("no identifier columns; CSVs readable", "all CSV files", not id_hits, "; ".join(id_hits[:10])))
    bad_fig = []
    for p in (stage / "01_figures").rglob("*"):
        if not p.is_file():
            continue
        head = p.read_bytes()[:512]
        ok = {".png": head.startswith(b"\x89PNG\r\n\x1a\n"), ".pdf": head.startswith(b"%PDF-"),
              ".svg": b"<svg" in p.read_bytes()[:4096]}.get(p.suffix.lower(), False)
        if not ok:
            bad_fig.append(p.name)
    out.append(_row("figures are valid PNG/PDF/SVG", "01_figures", not bad_fig, ", ".join(bad_fig)))
    mains = sorted({p.stem for p in (stage / "01_figures" / "main").glob("*")})
    missing = [f"{s}{e}" for s in mains for e in (".png", ".pdf", ".svg") if not (stage / "01_figures" / "main" / f"{s}{e}").exists()]
    out.append(_row("main figures in three formats", f"{len(mains)} main figures", not missing and len(mains) == 6, ", ".join(missing)))
    return out


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_manifest(stage: Path, manifest: str = "MANIFEST.sha256") -> list[dict]:
    m = stage / manifest
    if not m.exists():
        return [_row("manifest matches files", manifest, False, "manifest missing")]
    listed = {}
    for line in m.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            h, rel = line.split("  ", 1)
            listed[rel] = h
    files = {p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file() and p.name != manifest}
    missing, extra = sorted(set(listed) - files), sorted(files - set(listed))
    wrong = [r for r in sorted(set(listed) & files) if sha256(stage / r) != listed[r]]
    ok = not (missing or extra or wrong)
    return [_row("manifest matches files", f"{len(listed)} entries", ok,
                 f"missing {missing[:5]}; unlisted {extra[:5]}; hash mismatch {wrong[:5]}" if not ok else "")]


def run_all(stage: Path, pub: Path, with_manifest: bool = True) -> pd.DataFrame:
    rows = check_main_tables(stage / "02_tables" / "main", pub)
    text_rows, _ = check_text(stage)
    rows += text_rows + check_files(stage)
    if with_manifest:
        rows += check_manifest(stage)
    return pd.DataFrame(rows)
