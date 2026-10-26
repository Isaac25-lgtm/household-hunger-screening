"""Hashing and artifact manifests."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def file_record(path: Path, root: Path) -> dict:
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def environment_record() -> dict:
    import matplotlib
    import numpy
    import pandas
    import yaml

    rec = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "matplotlib": matplotlib.__version__,
        "pyyaml": yaml.__version__,
    }
    for mod in ("streamlit", "plotly", "pytest"):
        try:
            rec[mod] = __import__(mod).__version__
        except Exception:  # optional dependency absent
            rec[mod] = None
    return rec


def write_manifest(paths: list[Path], root: Path, out: Path, extra: dict | None = None) -> dict:
    manifest = {
        "generated_utc": utc_now(),
        "files": [file_record(p, root) for p in sorted(paths) if p.is_file()],
    }
    if extra:
        manifest.update(extra)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
