"""Calendar month -> designated two-month slot mapping and the outcome-blind duplicate rule."""

import numpy as np
import pandas as pd

from hunger_screening.build_panels import SLOT_LABELS, assign_slots, deduplicate, slot_matrix, valid_hhs


def test_month_to_slot():
    df = pd.DataFrame({"survey_month": pd.to_datetime([f"2020-{m:02d}-01" for m in range(1, 13)])})
    out = assign_slots(df)
    assert out["slot"].tolist() == [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6]
    assert SLOT_LABELS[out["slot"].iloc[2]] == "Mar-Apr"


def _dup_frame(h_early, h_late):
    return pd.DataFrame({
        "country": ["L", "L", "L"], "village_id": [1, 1, 1], "id": [7, 7, 7],
        "survey_date": pd.to_datetime(["2020-04-27", "2020-03-01", "2020-05-02"]),
        "survey_month": pd.to_datetime(["2020-04-01", "2020-03-01", "2020-05-01"]),
        "HHS": [h_late, h_early, 2.0],
    })


def test_duplicate_rule_keeps_earliest_regardless_of_outcome():
    for a, b in ((0.0, 3.0), (3.0, 0.0)):
        kept, info = deduplicate(assign_slots(_dup_frame(a, b)))
        slot2 = kept[(kept.slot == 2)]
        assert len(slot2) == 1
        assert slot2["survey_date"].iloc[0] == pd.Timestamp("2020-03-01")
        assert slot2["HHS"].iloc[0] == a
        assert info.household_slots_with_multiple == 1 and info.records_dropped == 1


def test_valid_hhs_and_matrix_reindexes_frame():
    phone = assign_slots(pd.DataFrame({
        "country": ["M", "M"], "village_id": [1, 1], "id": [1, 1],
        "survey_date": pd.to_datetime(["2020-01-05", "2020-03-05"]),
        "survey_month": pd.to_datetime(["2020-01-01", "2020-03-01"]),
        "HHS": [2.0, 9.0],
    }))
    phone = valid_hhs(phone)
    assert np.isnan(phone["HHS"].iloc[1])
    frame = pd.DataFrame({"country": ["M", "M"], "village_id": [1, 2], "id": [1, 2]})
    mat = slot_matrix(phone, frame, 2020, list(range(1, 7)))
    assert mat.shape == (2, 6)
    assert mat.loc[("M", 1, 1), 1] == 2.0
    assert mat.loc[("M", 2, 2)].isna().all()       # never-observed frame household retained
