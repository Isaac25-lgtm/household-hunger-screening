"""Acquire and verify the PLOS ONE S1 Data supplement.

The archive is downloaded from the publisher (or reused if already present), its
byte count and SHA-256 are checked against config/study.yaml, and only the two files
used by this study are extracted. Raw files stay under data/raw/ (gitignored).
"""

from __future__ import annotations

import json
import logging
import urllib.request
import zipfile
from pathlib import Path

from .config import Paths, load_config
from .provenance import sha256_file, utc_now

log = logging.getLogger(__name__)


class SourceVerificationError(RuntimeError):
    pass


def acquire(paths: Paths | None = None, cfg: dict | None = None, allow_download: bool = True) -> dict:
    paths = paths or Paths()
    cfg = cfg or load_config(paths.config)
    src = cfg["source"]
    paths.download.mkdir(parents=True, exist_ok=True)
    zpath = paths.download / "S1_Data.zip"
    record: dict = {"supplement_url": src["supplement_url"], "supplement_doi": src["supplement_doi"]}

    if not zpath.exists():
        if not allow_download:
            raise FileNotFoundError(f"{zpath} missing and download disabled")
        log.info("Downloading %s", src["supplement_url"])
        req = urllib.request.Request(src["supplement_url"], headers={"User-Agent": "hunger-screening/0.1"})
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 (fixed publisher URL)
            data = resp.read()
            record["http_status"] = resp.status
        zpath.write_bytes(data)
        record["retrieved_utc"] = utc_now()
    else:
        record["retrieved_utc"] = _read_existing_retrieval(paths)
        record["http_status"] = "reused local copy"

    record["bytes"] = zpath.stat().st_size
    record["sha256"] = sha256_file(zpath)
    record["bytes_match"] = record["bytes"] == src["expected_bytes"]
    record["sha256_match"] = record["sha256"] == src["expected_sha256"]
    if not (record["bytes_match"] and record["sha256_match"]):
        raise SourceVerificationError(
            f"Archive does not match expected provenance: {record['bytes']} bytes, {record['sha256']}"
        )

    paths.extracted.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zpath) as zf:
        members = [i for i in zf.infolist() if not i.filename.startswith("__MACOSX")]
        record["archive_members"] = [{"name": i.filename, "bytes": i.file_size} for i in members]
        for name in (src["phone_file"], src["baseline_file"]):
            target = paths.extracted / name
            if not target.exists():
                zf.extract(name, paths.extracted)
            record[f"sha256_{name}"] = sha256_file(target)
    return record


def _read_existing_retrieval(paths: Paths) -> str:
    p = paths.download / "retrieval_time.txt"
    return p.read_text().strip() if p.exists() else "unknown (pre-existing local copy)"


def save_record(record: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2), encoding="utf-8")
