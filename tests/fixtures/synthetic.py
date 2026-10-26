"""Entirely synthetic panels for tests. No real household data are used or derived here."""

from __future__ import annotations

import numpy as np
import pandas as pd


def synthetic_sources(seed: int = 0, n_villages: int = 12, hh_per_village: int = 4,
                      p_missing: float = 0.15) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Synthetic phone records (2020-2021, one call per two-month slot) and baseline frame."""
    rng = np.random.default_rng(seed)
    base_rows, phone_rows = [], []
    hid = 1000
    for country, offset in (("Malawi", 0), ("Liberia", 500)):
        for v in range(n_villages):
            vid = offset + v
            for _ in range(hh_per_village):
                hid += 1
                base_rows.append({"country": country, "village_id": vid, "id": hid, "HHS": rng.integers(0, 7),
                                  "female": rng.integers(0, 2), "age": rng.integers(18, 80),
                                  "years_educ": rng.integers(0, 12), "hh_size": rng.integers(1, 10),
                                  "current_partnered": 1, "house_owned": 1, "thatch_roof": rng.integers(0, 2),
                                  "total_expend_mon_usd": rng.gamma(2, 20), "food_expend_usd": rng.gamma(2, 10),
                                  "hhps_ever": 1})
                risk = rng.uniform(0, 0.6)
                parity = rng.integers(0, 2)
                for year in (2020, 2021):
                    for slot in range(1, 7):
                        if rng.uniform() < p_missing:
                            continue
                        month = 2 * slot - 1 + parity
                        day = int(rng.integers(1, 28))
                        hhs = int(rng.choice([0, 1, 2, 3, 4], p=[(1 - risk) * 0.7, (1 - risk) * 0.3,
                                                                  risk * 0.6, risk * 0.3, risk * 0.1]))
                        phone_rows.append({"country": country, "village_id": vid, "id": hid,
                                           "survey_date": pd.Timestamp(year, month, day),
                                           "survey_month": pd.Timestamp(year, month, 1), "surveywave": slot,
                                           "HHS": float(hhs), "i3_1_nofood_4w": float(hhs > 0),
                                           "i3_2_night_4w": float(hhs > 1), "i3_3_wholeday_4w": float(hhs > 3)})
    return pd.DataFrame(phone_rows), pd.DataFrame(base_rows)
