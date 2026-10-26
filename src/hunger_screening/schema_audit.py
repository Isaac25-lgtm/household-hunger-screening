"""Source schema and integrity audit (aggregate outputs only; no identifiers written)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HHS_ITEMS = ["i3_1_nofood_4w", "i3_2_night_4w", "i3_3_wholeday_4w"]


def data_dictionary(path: Path) -> pd.DataFrame:
    reader = pd.io.stata.StataReader(path)
    with reader:
        df = reader.read(convert_categoricals=False)
        labels = reader.variable_labels()
        value_labels = reader.value_labels()
    rows = []
    for c in df.columns:
        s = df[c]
        rows.append({
            "file": path.name,
            "variable": c,
            "dtype": str(s.dtype),
            "n_rows": len(s),
            "n_missing": int(s.isna().sum()),
            "n_distinct": int(s.nunique()),
            "label": labels.get(c, ""),
            "has_value_labels": c in value_labels,
        })
    return pd.DataFrame(rows)


def integrity_checks(phone_full: pd.DataFrame, baseline_full: pd.DataFrame) -> pd.DataFrame:
    """Each check returns (check, value, expectation, pass)."""
    out = []

    def add(name, value, expect, ok):
        out.append({"check": name, "value": value, "expectation": expect, "pass": bool(ok)})

    add("baseline rows", len(baseline_full), "503", len(baseline_full) == 503)
    for c, n in (("Malawi", 297), ("Liberia", 206)):
        v = int((baseline_full["country"] == c).sum())
        add(f"baseline households {c}", v, str(n), v == n)
    add("baseline id unique", bool(baseline_full["id"].is_unique), "True", baseline_full["id"].is_unique)
    ids_m = set(baseline_full.loc[baseline_full.country == "Malawi", "id"])
    ids_l = set(baseline_full.loc[baseline_full.country == "Liberia", "id"])
    add("id collisions across countries", len(ids_m & ids_l), "0", not (ids_m & ids_l))
    vm = set(baseline_full.loc[baseline_full.country == "Malawi", "village_id"])
    vl = set(baseline_full.loc[baseline_full.country == "Liberia", "village_id"])
    add("village collisions across countries", len(vm & vl), "0", not (vm & vl))
    hh_vil = baseline_full.groupby("id")["village_id"].nunique().max()
    add("households nested in one village", int(hh_vil), "1", hh_vil == 1)

    add("phone records", len(phone_full), "4744 (earlier audit)", len(phone_full) == 4744)
    m = phone_full.merge(baseline_full[["id", "country", "village_id"]], on="id", how="left",
                         suffixes=("", "_bl"), indicator=True)
    unmatched = int((m["_merge"] != "both").sum())
    add("phone records not in baseline frame", unmatched, "0", unmatched == 0)
    add("phone country == baseline country", bool((m.country == m.country_bl).all()), "True",
        (m.country == m.country_bl).all())
    add("phone village == baseline village", bool((m.village_id == m.village_id_bl).all()), "True",
        (m.village_id == m.village_id_bl).all())
    add("phone households observed", phone_full["id"].nunique(), "483 (earlier audit)",
        phone_full["id"].nunique() == 483)
    add("phone villages observed", phone_full["village_id"].nunique(), "252 (earlier audit)",
        phone_full["village_id"].nunique() == 252)
    add("unique submission key", bool(phone_full["key"].is_unique) if "key" in phone_full else None, "True",
        phone_full["key"].is_unique if "key" in phone_full else False)
    same_month = (phone_full["survey_date"].dt.to_period("M") == phone_full["survey_month"].dt.to_period("M"))
    add("survey_date month == survey_month", int((~same_month).sum()), "0 mismatches", same_month.all())
    add("survey_month is first of month", bool((phone_full["survey_month"].dt.day == 1).all()), "True",
        (phone_full["survey_month"].dt.day == 1).all())
    dup_month = int(phone_full.assign(_ym=phone_full["survey_month"].dt.to_period("M"))
                    .duplicated(["country", "id", "_ym"]).sum())
    add("repeated household-month records", dup_month, "0", dup_month == 0)
    h = phone_full["HHS"]
    add("HHS missing records", int(h.isna().sum()), "small", True)
    bad = int((h.notna() & ~(h.between(0, 6) & (h == np.round(h)))).sum())
    add("HHS outside integer 0-6", bad, "0", bad == 0)
    add("HHS >= 4 records (before slot rule)", int((h >= 4).sum()), "26 (earlier audit)", int((h >= 4).sum()) == 26)
    ny = phone_full[HHS_ITEMS].sum(axis=1, min_count=3)
    both = h.notna() & ny.notna()
    consistent = (h >= ny) & (h <= 2 * ny)
    add("HHS consistent with occurrence items (yes-count <= HHS <= 2*yes-count)",
        f"{int((consistent & both).sum())}/{int(both.sum())}", "all", bool((consistent | ~both).all()))
    if "wgt" in phone_full:
        add("analytic weight values", ",".join(str(x) for x in sorted(phone_full["wgt"].unique())), "1", True)
    return pd.DataFrame(out)


def hhs_item_crosstab(phone_full: pd.DataFrame) -> pd.DataFrame:
    ny = phone_full[HHS_ITEMS].sum(axis=1, min_count=3)
    tab = pd.crosstab(ny.rename("occurrence_items_yes"), phone_full["HHS"].rename("HHS"))
    return tab.reset_index()


def monthly_record_counts(phone_full: pd.DataFrame) -> pd.DataFrame:
    t = phone_full.groupby([phone_full["survey_month"].dt.strftime("%Y-%m").rename("month"), "country"]).size()
    return t.unstack("country", fill_value=0).reset_index()
