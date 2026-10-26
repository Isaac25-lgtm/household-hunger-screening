import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

RAW_PHONE = ROOT / "data" / "raw" / "extracted" / "hhps_analysis_fullsample.dta"

requires_raw = pytest.mark.skipif(not RAW_PHONE.exists(),
                                  reason="private source data not present (expected in CI)")


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT
