"""Review responses: a-priori window rule and published review aggregates."""

import pandas as pd
import pytest
from conftest import ROOT

from hunger_screening import review_responses as rr

OUT = ROOT / "data" / "public_aggregates" / "review"
requires_outputs = pytest.mark.skipif(not (OUT / "calendar_lean_season_sensitivity.csv").exists(), reason="review outputs not generated")


def test_apriori_window_from_lean_months():
    six = [1, 2, 3, 4, 5, 6]
    assert rr._calendar_window([12, 1, 2], six) == 1  # Malawi Dec-Feb -> Jan-Feb (two months inside)
    assert rr._calendar_window([6, 7, 8], six) == 4  # Liberia Jun-Aug -> Jul-Aug
    assert rr._calendar_window([12, 1, 2], [4, 5, 6, 1, 2, 3]) == 1  # order of candidates does not change the choice


@requires_outputs
def test_scoring_check_supports_standard_hhs():
    r = pd.read_csv(OUT / "hhs_scoring_check_records.csv").iloc[0]  # first row: standard no-food item
    assert r.score_below_yes_count == 0 and bool(r.excess_never_exceeds_yes_count)
    assert r.score_equals_yes_count + r.score_exceeds_yes_count == r.records_with_score_and_items


@requires_outputs
def test_second_scope_is_inside_or_equal_and_bounds_ordered():
    b = pd.read_csv(OUT / "missing_bounds_second_scope.csv")
    assert (b.lower <= b.upper).all()
    w = b.assign(width=b.upper - b.lower).pivot_table(index=["country", "m"], columns="scope", values="width")
    assert (w["households with >= 1 observed 2020 window"] <= w["all baseline-frame households"] + 1e-12).all()


@requires_outputs
def test_review_outputs_have_no_identifier_columns():
    for f in OUT.glob("*.csv"):
        cols = {c.lower() for c in pd.read_csv(f, nrows=0).columns}
        assert not cols & {"id", "hh", "hhid", "village_id", "household_id", "y4_hhid"}, f.name
