"""Reconstruct the baseline phone frame and designated two-month screening panels.

Design facts used here (verified in schema_audit and the source replication do-file):
  * baseline_analysis_fullsample.dta holds the 503 control households selected for the
    household phone survey (Malawi 297, Liberia 206); this is the analysis frame.
  * hhps_analysis_fullsample.dta holds the phone interviews. Respondents were called on
    alternating months, so each household has one designated interview per two-month
    window. Window ("slot") s of a year covers calendar months 2s-1 and 2s.
  * Each interview's HHS refers to the preceding ~4 weeks; months between windows are
    not observed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

SLOT_LABELS = {1: "Jan-Feb", 2: "Mar-Apr", 3: "May-Jun", 4: "Jul-Aug", 5: "Sep-Oct", 6: "Nov-Dec"}
KEY = ["country", "village_id", "id"]

PHONE_COLS = [
    "country", "village_id", "id", "survey_date", "survey_month", "surveywave", "HHS",
    "i3_1_nofood_4w", "i3_2_night_4w", "i3_3_wholeday_4w",
]
BASELINE_COLS = [
    "country", "village_id", "id", "HHS", "female", "age", "years_educ", "hh_size",
    "current_partnered", "house_owned", "thatch_roof", "total_expend_mon_usd",
    "food_expend_usd", "hhps_ever",
]


def read_stata(path: Path, columns: list[str]) -> pd.DataFrame:
    df = pd.read_stata(path, convert_categoricals=False, columns=columns)
    return df


def load_sources(extracted: Path, phone_file: str, baseline_file: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    phone = read_stata(extracted / phone_file, PHONE_COLS)
    baseline = read_stata(extracted / baseline_file, BASELINE_COLS)
    phone["id"] = phone["id"].astype(int)
    baseline["id"] = baseline["id"].astype(int)
    phone["village_id"] = phone["village_id"].astype(int)
    baseline["village_id"] = baseline["village_id"].astype(int)
    return phone, baseline


def valid_hhs(phone: pd.DataFrame) -> pd.DataFrame:
    """Set out-of-range or non-integer HHS to missing (counts logged by schema_audit)."""
    out = phone.copy()
    h = out["HHS"]
    bad = h.notna() & ~(h.between(0, 6) & (h == np.round(h)))
    out.loc[bad, "HHS"] = np.nan
    return out


def assign_slots(phone: pd.DataFrame) -> pd.DataFrame:
    out = phone.copy()
    out["year"] = out["survey_month"].dt.year.astype(int)
    out["month"] = out["survey_month"].dt.month.astype(int)
    out["slot"] = ((out["month"] - 1) // 2 + 1).astype(int)
    return out


@dataclass
class DedupInfo:
    household_slots_with_multiple: int
    records_dropped: int
    binary_outcome_differs: dict[int, int] = field(default_factory=dict)


def deduplicate(phone: pd.DataFrame, thresholds: tuple[int, ...] = (1, 2, 4)) -> tuple[pd.DataFrame, DedupInfo]:
    """Keep the earliest dated record per household-year-slot (outcome-blind rule).

    Records with missing HHS are dropped *before* de-duplication only if another
    record in the same slot has a valid HHS; this never uses the HHS value itself.
    """
    grp = ["country", "id", "year", "slot"]
    sizes = phone.groupby(grp)["survey_date"].transform("size")
    multi = phone[sizes > 1]
    differs = {}
    for t in thresholds:
        b = (multi["HHS"] >= t).astype(float).where(multi["HHS"].notna())
        differs[t] = int(b.groupby([multi[g] for g in grp]).nunique().gt(1).sum()) if len(multi) else 0
    ordered = phone.assign(_has=phone["HHS"].notna()).sort_values(grp + ["_has", "survey_date"],
                                                                  ascending=[True] * 4 + [False, True])
    kept = ordered.drop_duplicates(grp, keep="first").drop(columns="_has")
    info = DedupInfo(
        household_slots_with_multiple=int(multi.groupby(grp).ngroups) if len(multi) else 0,
        records_dropped=int(len(phone) - len(kept)),
        binary_outcome_differs=differs,
    )
    return kept.sort_values(["country", "id", "survey_date"]).reset_index(drop=True), info


def slot_matrix(phone: pd.DataFrame, frame: pd.DataFrame, year: int, slots: list[int]) -> pd.DataFrame:
    """HHS by designated slot for every frame household (NaN = no valid screen)."""
    sub = phone[(phone["year"] == year) & phone["slot"].isin(slots) & phone["HHS"].notna()]
    wide = sub.pivot_table(index="id", columns="slot", values="HHS", aggfunc="first")
    wide = wide.reindex(columns=slots)
    idx = frame.set_index("id")[["country", "village_id"]]
    mat = idx.join(wide, how="left")
    mat = mat.reset_index().set_index(KEY).sort_index()
    mat.columns = [int(c) for c in mat.columns]
    mat.attrs["year"] = year
    mat.attrs["slots"] = list(slots)
    return mat


def binarize(mat: pd.DataFrame, threshold: int) -> pd.DataFrame:
    out = (mat >= threshold).astype(float).where(mat.notna())
    out.attrs.update(mat.attrs)
    out.attrs["threshold"] = threshold
    return out


def observed_counts(binary: pd.DataFrame) -> pd.DataFrame:
    """Per household: observed positives k, missing windows r, observed windows n_obs."""
    k = binary.sum(axis=1, skipna=True).astype(int)
    r = binary.isna().sum(axis=1).astype(int)
    return pd.DataFrame({"k": k, "r": r, "n_obs": binary.shape[1] - r}, index=binary.index)


def complete_k(binary: pd.DataFrame) -> pd.Series:
    """Positive counts K for households observed in every slot."""
    comp = binary.dropna()
    return comp.sum(axis=1).astype(int)


def cohort_flow(phone_raw: pd.DataFrame, phone_valid: pd.DataFrame, phone_dedup: pd.DataFrame,
                frame: pd.DataFrame, bin2020: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c in sorted(frame["country"].unique(), reverse=True):
        pr = phone_raw[phone_raw["country"] == c]
        pv = phone_valid[(phone_valid["country"] == c) & phone_valid["HHS"].notna()]
        pdd = phone_dedup[(phone_dedup["country"] == c) & phone_dedup["HHS"].notna()]
        b = bin2020.xs(c, level="country")
        comp = b.dropna()
        k = comp.sum(axis=1)
        p20 = pdd[pdd["year"] == 2020]
        steps = [
            ("Baseline phone-frame households", frame[frame["country"] == c]["id"].nunique(), "households"),
            ("Baseline phone-frame villages", frame[frame["country"] == c]["village_id"].nunique(), "villages"),
            ("Phone interview records (all months)", len(pr), "records"),
            ("Records with valid HHS (0-6)", len(pv), "records"),
            ("Households with >=1 phone record", pr["id"].nunique(), "households"),
            ("Records after one-per-slot rule (all years)", len(pdd), "records"),
            ("2020 designated-slot screens with valid HHS", len(p20), "records"),
            ("Households with >=1 valid 2020 screen", p20["id"].nunique(), "households"),
            ("Households with all 6 valid 2020 screens", len(comp), "households"),
            ("Villages with >=1 complete 2020 household",
             comp.index.get_level_values("village_id").nunique(), "villages"),
            ("Complete households reference-positive (HHS>=2 in >=1 slot)", int((k > 0).sum()), "households"),
        ]
        for i, (step, n, unit) in enumerate(steps):
            rows.append({"country": c, "order": i + 1, "step": step, "count": int(n), "unit": unit})
    return pd.DataFrame(rows)
