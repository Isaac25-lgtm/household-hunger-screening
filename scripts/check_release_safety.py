"""Release-safety audit for files that would be published (git-tracked + untracked-not-ignored).

Fails (exit code 1) if any candidate file:
  * has a raw-data / archive extension (.dta, .zip, .sav, .parquet, .pkl, ...);
  * lives under data/raw, data/interim, data/processed_private or logs/private;
  * is a CSV/JSON in public folders containing household/village identifier columns;
  * matches a known secret pattern (GitHub tokens, AWS keys, private keys, ...);
  * exceeds the size limit (default 5 MB).
Usage: python scripts/check_release_safety.py [--all-files]
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_EXT = {".dta", ".zip", ".sav", ".parquet", ".feather", ".pkl", ".pickle", ".rds", ".env"}
FORBIDDEN_DIRS = ("data/raw/", "data/interim/", "data/processed_private/", "logs/private/", ".venv/")
ID_COLUMNS = {"id", "id_str", "key", "village_id", "household_id", "hhid", "phone", "gps", "latitude",
              "longitude", "name"}
SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"gho_[A-Za-z0-9]{30,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"sk-[A-Za-z0-9]{32,}"),
]
MAX_BYTES = 5 * 1024 * 1024


def candidate_files(all_files: bool = False) -> list[str]:
    if all_files:
        return [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")
                if p.is_file() and ".git/" not in p.as_posix() and ".venv" not in p.parts]
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line.strip()]


def audit(files: list[str]) -> list[str]:
    problems = []
    for rel in files:
        p = ROOT / rel
        if not p.is_file():
            continue
        low = rel.lower()
        if p.suffix.lower() in FORBIDDEN_EXT and not low.endswith(".env.example"):
            problems.append(f"forbidden file type: {rel}")
        if any(low.startswith(d) for d in FORBIDDEN_DIRS):
            problems.append(f"private directory: {rel}")
        if p.stat().st_size > MAX_BYTES:
            problems.append(f"file larger than {MAX_BYTES} bytes: {rel}")
        if p.suffix.lower() == ".csv" and rel != "data/public_aggregates/data_dictionary.csv":
            with open(p, encoding="utf-8", errors="replace") as fh:
                header = next(csv.reader(fh), [])
            bad = {h.strip().lower() for h in header} & ID_COLUMNS
            if bad:
                problems.append(f"identifier column(s) {sorted(bad)} in {rel}")
        if p.suffix.lower() in {".py", ".md", ".txt", ".yml", ".yaml", ".toml", ".json", ".csv", ".ps1", ".cfg",
                                ".ini", ".html", ".js"} or p.name.startswith(".env"):
            text = p.read_text(encoding="utf-8", errors="replace")
            if rel.endswith("check_release_safety.py"):
                continue
            for pat in SECRET_PATTERNS:
                if pat.search(text):
                    problems.append(f"possible secret ({pat.pattern[:20]}...) in {rel}")
    return problems


def main() -> int:
    files = candidate_files("--all-files" in sys.argv)
    problems = audit(files)
    print(f"Audited {len(files)} candidate files.")
    for prob in problems:
        print("FAIL:", prob)
    if not problems:
        print("PASS: no raw data, identifiers, secrets or oversized files in the release set.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
