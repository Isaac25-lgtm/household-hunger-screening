"""Manuscript tables, package quality control and deterministic packaging."""

import importlib.util
import re
import zipfile

import pandas as pd
import pytest
from conftest import ROOT

from hunger_screening import manuscript_tables as mt
from hunger_screening import package_qc as qc

PUB = ROOT / "data" / "public_aggregates"
requires_outputs = pytest.mark.skipif(not (PUB / "review" / "window_paired_comparisons.csv").exists(),
                                      reason="review outputs not generated")


def _builder():
    spec = importlib.util.spec_from_file_location("build_manuscript_package", ROOT / "scripts" / "build_manuscript_package.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_rounding_helpers_round_from_unrounded_values():
    assert mt.p1(0.38345864661654133) == "38.3%"
    assert mt.d1(0.38345864661654133 - 0.5927318295739348) == "-20.9"  # difference before rounding
    assert mt.ci1(-0.27519, -0.13646) == "-27.5 to -13.6"
    assert mt.p1(float("nan")) == ""


def test_integer_count_check():
    assert mt.count_columns_are_integers(pd.DataFrame({"n": [297, 206]}), ["n"])
    assert not mt.count_columns_are_integers(pd.DataFrame({"n": ["297.0"]}), ["n"])


@requires_outputs
def test_main_tables_lead_rows_and_labels(tmp_path):
    mt.build(PUB, tmp_path / "main", tmp_path / "supp")
    t3 = pd.read_csv(tmp_path / "main" / "table3_timing_two_malawi_panels.csv", dtype=str, keep_default_na=False)
    lead = t3.iloc[0]
    assert lead["Analysis period"].startswith("Jul 2020 - Jun 2021")
    assert (lead["Reference-positive households"], lead["Window missed"], lead["Random missed"], lead["Difference (pp)"]) == \
        ("133", "38.3%", "59.3%", "-20.9")
    assert t3.Panel.str.contains("not the HHS").any() and (t3.Note == "Failed transfer").any()
    t2 = pd.read_csv(tmp_path / "main" / "table2_frequency_frontier_and_identification.csv", dtype=str)
    assert t2[t2.Panel.str.startswith("B.")].Panel.str.contains("not a CI").all()
    t4 = pd.read_csv(tmp_path / "main" / "table4_protocol_locked_multicountry_tests.csv", dtype=str, keep_default_na=False)
    assert "two with eligible primary" in (tmp_path / "main" / "table4_protocol_locked_multicountry_tests.md").read_text(encoding="utf-8")
    assert {"Ethiopia", "Nigeria (both panels)", "Tanzania"} <= set(t4["Country and horizon"])
    h3 = t4[(t4.Hypothesis == "H3 second-contact rule") & t4.Status.str.startswith("Primary") & (t4.Difference != "-")]
    assert len(h3) == 3 and (h3.Reading == "inconclusive").sum() == 1  # one interval includes zero


@requires_outputs
def test_supplementary_tables_have_no_missing_value_text(tmp_path):
    made = mt.supplementary(PUB, tmp_path) + mt.build(PUB, tmp_path / "main", tmp_path)
    assert {"tableS15_h2_h4_prespecified_results", "tableS17_window_paired_comparisons"} <= set(made)
    for p in tmp_path.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        assert not re.search(r"\|\s*(nan|<NA>|None)\s*\|", text), p.name


@requires_outputs
def test_canonical_values_match_documented_headlines():
    cv = qc.canonical_values(PUB).set_index("quantity_key").display
    assert cv["lead_missed"] == "38.3%" and cv["lead_random"] == "59.3%" and cv["lead_diff"] == "-20.9"
    assert cv["jan_aug_2021_ci"] == "-46.9 to -29.2"
    assert cv["ranges_excluding_zero"] == "3 of 4"
    assert cv["h3_UGA_2020"].startswith("16.9 vs 10.4; +6.4 (+4.4 to +8.8)")


def _stage(tmp_path):
    s = tmp_path / "stage"
    (s / "01_figures" / "main").mkdir(parents=True)
    (s / "04_methods_results_reports").mkdir(parents=True)
    return s


def test_text_check_flags_banned_wording_and_paths(tmp_path):
    s = _stage(tmp_path)
    doc = s / "04_methods_results_reports" / "x.md"
    doc.write_text("The analysis is protocol-locked, not fully blind.\n", encoding="utf-8")
    assert qc.check_text(s)[0][0]["status"] == "PASS"
    for bad in ("Results of the five-country test.", "Comparisons survive any pattern of missing interviews.",
                "The window was chosen a priori.", "This analysis was fully blind.", "+6.5 (+4.4 to +8.8)",
                "see " + "C:" + "\\Users\\someone\\file.csv"):
        doc.write_text(bad + "\n", encoding="utf-8")
        assert qc.check_text(s)[0][0]["status"] == "FAIL", bad


def test_text_check_allows_locked_protocol_wording(tmp_path):
    s = _stage(tmp_path)
    (s / "04_methods_results_reports" / "10_LOCKED_PROTOCOL_MULTICOUNTRY_HFPS.md").write_text("five-country test\n", encoding="utf-8")
    assert qc.check_text(s)[0][0]["status"] == "PASS"


def test_file_checks_flag_private_types_and_invalid_figures(tmp_path):
    s = _stage(tmp_path)
    (s / "01_figures" / "main" / "Figure1.png").write_bytes(b"not a png")
    (s / "03_results_data").mkdir()
    (s / "03_results_data" / "x.dta").write_bytes(b"")
    pd.DataFrame({"hhid": [1]}).to_csv(s / "03_results_data" / "y.csv", index=False)
    res = {r["check"]: r["status"] for r in qc.check_files(s)}
    assert res["no private file types"] == "FAIL"
    assert res["figures are valid PNG/PDF/SVG"] == "FAIL"
    assert res["no identifier columns; CSVs readable"] == "FAIL"


def test_manifest_detects_tampering(tmp_path):
    s = _stage(tmp_path)
    f = s / "04_methods_results_reports" / "a.md"
    f.write_text("a\n", encoding="utf-8")
    (s / "MANIFEST.sha256").write_text(f"# x\n{qc.sha256(f)}  04_methods_results_reports/a.md\n", encoding="utf-8")
    assert qc.check_manifest(s)[0]["status"] == "PASS"
    f.write_text("b\n", encoding="utf-8")
    assert qc.check_manifest(s)[0]["status"] == "FAIL"


def test_zip_is_deterministic(tmp_path):
    b = _builder()
    s = _stage(tmp_path)
    (s / "04_methods_results_reports" / "a.md").write_text("a\n", encoding="utf-8")
    (s / "01_figures" / "main" / "b.txt").write_text("b\n", encoding="utf-8")
    z1, z2 = tmp_path / "1.zip", tmp_path / "2.zip"
    b.deterministic_zip(s, z1)
    (s / "04_methods_results_reports" / "a.md").touch()  # a new modification time must not change the archive
    b.deterministic_zip(s, z2)
    assert z1.read_bytes() == z2.read_bytes()
    with zipfile.ZipFile(z1) as z:
        assert z.testzip() is None
        assert all(i.date_time == b.ZIP_TIME for i in z.infolist())
