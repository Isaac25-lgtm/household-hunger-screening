"""The 2020-selected timing rule must not depend on 2021 outcomes."""

import dataclasses

import numpy as np
import pandas as pd
import pytest

from hunger_screening.timing_validation import (
    FrozenRule,
    LeakageError,
    candidate_table,
    evaluate_rule,
    select_slot,
)


def mat(rows, year):
    idx = pd.MultiIndex.from_arrays([["X"] * len(rows), [i // 2 for i in range(len(rows))], range(len(rows))],
                                    names=["country", "village_id", "id"])
    df = pd.DataFrame(rows, index=idx, columns=[1, 2, 3, 4], dtype=float)
    df.attrs["year"] = year
    return df


TRAIN = mat([[1, 0, 0, 0], [1, 1, 0, 0], [0, 1, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]], 2020)


def test_selection_rejects_test_year_data():
    test = mat([[1, 0, 0, 0]], 2021)
    with pytest.raises(LeakageError):
        select_slot(test, 2020, 2)


def test_selection_invariant_to_test_data():
    rule = select_slot(TRAIN, 2020, 2)
    assert rule.slot == 1 and np.isclose(rule.train_missed, 1 / 4)
    for seed in range(5):
        rng = np.random.default_rng(seed)
        _ = mat(rng.integers(0, 2, size=(6, 4)).tolist(), 2021)
        assert select_slot(TRAIN, 2020, 2) == rule


def test_rule_is_frozen():
    rule = select_slot(TRAIN, 2020, 2)
    with pytest.raises(dataclasses.FrozenInstanceError):
        rule.slot = 3  # type: ignore[misc]


def test_tie_break_earliest():
    t = mat([[1, 1, 0, 0], [1, 1, 0, 0]], 2020)
    assert select_slot(t, 2020, 2).slot == 1
    t2 = mat([[0, 1, 1, 0], [0, 1, 1, 0]], 2020)
    assert select_slot(t2, 2020, 2).slot == 2


def test_evaluation_and_random_benchmark():
    rule = FrozenRule(2, 2020, 2, "earliest", 0.0, 1)
    test = mat([[1, 0, 0, 0], [0, 1, 1, 0], [0, 0, 0, 0], [np.nan, 1, 0, 0]], 2021)
    ev = evaluate_rule(rule, test)
    assert ev["n_complete"] == 3 and ev["n_reference_positive"] == 2
    assert np.isclose(ev["missed_frozen"], 0.5)
    assert np.isclose(ev["missed_random_one_slot"], (3 / 4 + 2 / 4) / 2)


def test_candidate_table_lists_all_slots():
    ct = candidate_table(TRAIN)
    assert list(ct.slot) == [1, 2, 3, 4]
    assert np.isclose(ct.attrs["random_one_slot"], np.mean([3 / 4, 2 / 4, 3 / 4, 2 / 4]))
