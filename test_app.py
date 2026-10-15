from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).with_name("app.py")


def make_app() -> AppTest:
    return AppTest.from_file(str(APP), default_timeout=30)


def test_warning_shows_when_no_overlap():
    at = make_app()
    at.run()
    at.multiselect[0].set_value(["Tokyo", "London"]).run()
    assert not at.exception
    warnings = [element.value for element in at.warning]
    assert len(warnings) == 1
    assert "Tokyo" in warnings[0]
    assert "London" in warnings[0]


def test_no_warning_when_overlap_exists():
    at = make_app()
    at.run()
    at.multiselect[0].set_value(["London", "Bali"]).run()
    assert not at.exception
    assert [element.value for element in at.warning] == []


def test_no_warning_for_empty_selection():
    at = make_app()
    at.run()
    at.multiselect[0].set_value([]).run()
    assert not at.exception
    assert [element.value for element in at.warning] == []
    assert len(at.info) == 1
