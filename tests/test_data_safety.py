"""Public outputs must be aggregate-only and the release set free of raw data and secrets."""

import csv
import importlib.util
import json
import subprocess

import pytest


def _load_checker(root):
    spec = importlib.util.spec_from_file_location("crs", root / "scripts" / "check_release_safety.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_gitignore_blocks_private_data(root):
    gi = (root / ".gitignore").read_text()
    for pat in ("data/raw/", "data/interim/", "data/processed_private/", "*.dta", "*.zip", ".env", ".venv/"):
        assert pat in gi


def test_public_aggregates_have_no_identifier_columns(root):
    checker = _load_checker(root)
    pub = root / "data" / "public_aggregates"
    for p in list(pub.rglob("*.csv")) + list((root / "dashboard" / "data").glob("*.csv")):
        if p.name == "data_dictionary.csv":
            continue  # lists variable *names* only, no values
        with open(p, encoding="utf-8") as fh:
            header = {h.strip().lower() for h in next(csv.reader(fh), [])}
        assert not header & checker.ID_COLUMNS, p.name


def test_data_dictionary_has_no_values(root):
    p = root / "data" / "public_aggregates" / "data_dictionary.csv"
    if not p.exists():
        pytest.skip("pipeline outputs not generated")
    with open(p, encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == ["file", "variable", "dtype", "n_rows", "n_missing", "n_distinct", "label", "has_value_labels"]


def test_checker_flags_planted_problems(root, tmp_path, monkeypatch):
    checker = _load_checker(root)
    monkeypatch.setattr(checker, "ROOT", tmp_path)
    (tmp_path / "x.dta").write_bytes(b"0")
    (tmp_path / "ids.csv").write_text("id,value\n1,2\n")
    (tmp_path / "s.md").write_text("token ghp_" + "a" * 36)
    probs = checker.audit(["x.dta", "ids.csv", "s.md"])
    assert len(probs) == 3


def test_release_set_is_clean(root):
    try:
        subprocess.run(["git", "rev-parse"], cwd=root, check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("not a git repository")
    checker = _load_checker(root)
    assert checker.audit(checker.candidate_files()) == []


def test_source_provenance_matches_expected(root):
    p = root / "data" / "public_aggregates" / "source_provenance.json"
    if not p.exists():
        pytest.skip("pipeline outputs not generated")
    rec = json.loads(p.read_text())
    assert rec["sha256_match"] and rec["bytes_match"]
