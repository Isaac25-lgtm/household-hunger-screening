"""Locked multi-country protocol: rule logic, item mapping, decision criteria, published outputs."""

import pandas as pd
import pytest
import yaml
from conftest import ROOT

from hunger_screening import multicountry as mc

OUT = ROOT / "data" / "public_aggregates" / "multicountry"
requires_outputs = pytest.mark.skipif(not (OUT / "summary.json").exists(), reason="multi-country outputs not generated")


def test_protocol_parameters_unchanged():
    proto = yaml.safe_load(open(ROOT / "config" / "multicountry_protocol.yaml", encoding="utf-8"))
    assert proto["countries"]["BFA"]["lean_months"] == [6, 7, 8, 9]
    assert proto["countries"]["UGA"]["lean_months"] == [3, 4, 5, 6]
    assert proto["countries"]["TZA"]["lean_months"] == [11, 12]
    assert proto["usable_horizon"] == {"min_candidate_rounds": 3, "min_complete_households": 100}
    assert proto["bootstrap"]["seed"] == 20261028


def test_item_mapping_by_label_then_number():
    labs = {"fi6_noteatfullday": "FI6: Hungry Did Not Eat for a Full Day", "fi7_outoffood": "FI7: ran out of food",
            "fi8_hungrynoteat": "FI8: Hungry but Did Not Eat"}
    m = mc._map_items(labs, list(labs))
    assert m[7] == "fi8_hungrynoteat" and m[8] == "fi6_noteatfullday" and m[6] == "fi7_outoffood"
    trunc = {f"s8q0{k}": f"{k}. During the last 30 days, was there a time when You or others in your househol" for k in range(1, 9)}
    m2 = mc._map_items(trunc, list(trunc))
    assert m2[7] == "s8q07" and m2[8] == "s8q08"
    fr = {"s07q07": "Vous-même ou d'autres membres de votre ménage avez eu faim mais vous n'avez pas mangé"}
    assert mc._map_items(fr, list(fr))[7] == "s07q07"


def test_rule_index_picks_lean_round_closest_to_midpoint():
    spec = {"lean_months": [6, 7, 8, 9], "lean_midpoint": "07-31"}
    dates = [pd.Timestamp(x) for x in ("2020-11-14", "2021-06-03", "2021-07-07", "2021-02-18")]
    assert mc._rule_index(dates, spec) == 2
    assert mc._rule_index([pd.Timestamp("2021-01-10")], spec) is None
    tz = {"lean_months": [11, 12], "lean_midpoint": "11-30"}
    assert mc._rule_index([pd.Timestamp("2023-12-28"), pd.Timestamp("2023-11-02")], tz) == 0


def test_circular_day_distance():
    assert mc._circ_days(pd.Timestamp("2020-12-28"), pd.Timestamp("2022-01-03")) <= 7
    assert mc._circ_days(pd.Timestamp("2020-06-01"), pd.Timestamp("2022-06-01")) <= 1  # leap years shift day-of-year by one


def test_h1_decision_rule():
    d = lambda rows: pd.DataFrame(rows, columns=["diff", "diff_ci_low"])  # noqa: E731
    assert mc._decide_h1(d([(-0.1, -0.2), (-0.05, -0.1), (0.01, -0.02)])) == "supported"
    assert mc._decide_h1(d([(0.1, 0.05), (0.03, -0.04)])) == "contradicted"
    assert mc._decide_h1(d([(-0.1, -0.2), (0.02, -0.01)])) == "mixed"
    assert mc._decide_h1(pd.DataFrame()) == "untestable"


@requires_outputs
def test_published_outputs_consistent_and_identifier_free():
    h1 = pd.read_csv(OUT / "h1_calendar_rule.csv")
    assert ((h1.rule_missed - h1.random_missed - h1["diff"]).abs() < 1e-9).all()
    assert (h1.diff_ci_low <= h1["diff"] + 1e-12).all() and (h1.diff_ci_high >= h1["diff"] - 1e-12).all()
    for f in OUT.glob("*.csv"):
        cols = {c.lower() for c in pd.read_csv(f, nrows=0).columns}
        assert not cols & {"hh", "hhid", "household_id", "y4_hhid", "ea_id", "cluster", "grappe"}, f.name
