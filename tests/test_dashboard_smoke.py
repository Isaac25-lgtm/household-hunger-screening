"""Dashboard boots, every section renders without exceptions, and it reads aggregate files only."""

import ast

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest  # noqa: E402

SECTIONS = ["Overview", "Cohort & data audit", "Screening frontier", "Missing-data bounds",
            "Label-error sensitivity", "Calendar timing", "Methods & formulas", "Limitations & literature",
            "Downloads"]


@pytest.fixture(scope="module")
def app_path(root):
    p = root / "dashboard" / "app.py"
    if not (root / "dashboard" / "data" / "frontier.csv").exists():
        pytest.skip("dashboard aggregates not generated")
    return str(p)


@pytest.mark.parametrize("section", SECTIONS)
def test_section_renders(app_path, section):
    at = AppTest.from_file(app_path, default_timeout=60)
    at.run()
    assert not at.exception
    at.sidebar.radio[0].set_value(section).run()
    assert not at.exception, [e.value for e in at.exception]


def test_interactive_controls(app_path):
    at = AppTest.from_file(app_path, default_timeout=60)
    at.run()
    at.sidebar.radio[0].set_value("Screening frontier").run()
    for t in (1, 4, 2):
        at.radio[0].set_value(t).run()
        assert not at.exception
    at.sidebar.radio[0].set_value("Calendar timing").run()
    at.radio[0].set_value("Liberia").run()
    assert not at.exception
    assert any("22" in w.value for w in at.warning)


def test_overview_states_limits(app_path):
    at = AppTest.from_file(app_path, default_timeout=60)
    at.run()
    html = " ".join(m.value for m in at.markdown)
    assert "not a confidence interval" in html and "not national" in html


def test_empty_data_guard(root, tmp_path):
    """With no aggregate files the app shows a warning instead of crashing."""
    import shutil

    d = tmp_path / "dashboard"
    d.mkdir()
    shutil.copy(root / "dashboard" / "app.py", d / "app.py")
    (d / "data").mkdir()
    at = AppTest.from_file(str(d / "app.py"), default_timeout=60)
    at.run()
    assert not at.exception
    assert at.warning


def test_app_reads_only_dashboard_data(root):
    src = (root / "dashboard" / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    strings = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert not any(s.endswith((".dta", ".zip")) or "data/raw" in s or "interim" in s for s in strings)
