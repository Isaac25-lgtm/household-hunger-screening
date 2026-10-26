"""Project paths and study configuration."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Paths:
    root: Path = PROJECT_ROOT

    @property
    def config(self) -> Path:
        return self.root / "config" / "study.yaml"

    @property
    def raw(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def download(self) -> Path:
        return self.raw / "download"

    @property
    def extracted(self) -> Path:
        return self.raw / "extracted"

    @property
    def interim(self) -> Path:
        return self.root / "data" / "interim"

    @property
    def public(self) -> Path:
        return self.root / "data" / "public_aggregates"

    @property
    def tables(self) -> Path:
        return self.root / "tables"

    @property
    def figures(self) -> Path:
        return self.root / "figures"

    @property
    def reports(self) -> Path:
        return self.root / "reports"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def dashboard_data(self) -> Path:
        return self.root / "dashboard" / "data"

    def ensure(self) -> None:
        for p in (self.interim, self.public, self.tables, self.figures / "manuscript",
                  self.figures / "supplementary", self.figures / "README", self.reports,
                  self.logs, self.dashboard_data):
            p.mkdir(parents=True, exist_ok=True)


def load_config(path: Path | None = None) -> dict[str, Any]:
    path = path or Paths().config
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def config_hash(path: Path | None = None) -> str:
    path = path or Paths().config
    return hashlib.sha256(path.read_bytes()).hexdigest()
