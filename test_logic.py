from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from cities import CITY_CATALOG
from logic import (
    City,
    is_working_hour,
    local_time,
    no_overlap_warning,
    overlap_hours,
    overlap_windows,
    utc_offset_label,
)

UTC = timezone.utc

LONDON = City("London", "Europe/London")
BALI = City("Bali", "Asia/Makassar")
DUBLIN = City("Dublin", "Europe/Dublin")
TOKYO = City("Tokyo", "Asia/Tokyo")
NEW_YORK = City("New York", "America/New_York")


def utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=UTC)


def test_london_bali_overlap_next_seven_days():
    now = utc(2026, 10, 13)
    assert overlap_hours([LONDON, BALI], now, now + timedelta(days=7)) == 7.0


def test_same_zone_gives_full_week():
    now = utc(2026, 10, 13)
    assert overlap_hours([LONDON, DUBLIN], now, now + timedelta(days=7)) == 56.0


def test_tokyo_new_york_no_overlap_in_january():
    now = utc(2026, 1, 10)
    assert overlap_hours([TOKYO, NEW_YORK], now, now + timedelta(days=7)) == 0.0


def test_touching_intervals_do_not_overlap():
    now = utc(2026, 10, 24)
    assert overlap_hours([TOKYO, LONDON], now, now + timedelta(days=7)) == 0.0


def test_dst_transition_changes_overlap():
    now = utc(2026, 10, 23)
    assert overlap_hours([LONDON, NEW_YORK], now, now + timedelta(days=7)) == 26.0
    windows = overlap_windows([LONDON, NEW_YORK], now, now + timedelta(days=7))
    assert windows[0] == (utc(2026, 10, 23, 13), utc(2026, 10, 23, 16))
    assert windows[2] == (utc(2026, 10, 25, 13), utc(2026, 10, 25, 17))


def test_hour_boundaries():
    assert is_working_hour(LONDON, utc(2026, 10, 13, 8, 0)) is True
    assert is_working_hour(LONDON, utc(2026, 10, 13, 16, 0)) is False
    assert is_working_hour(LONDON, utc(2026, 10, 13, 7, 59)) is False


def test_utc_offset_labels():
    assert utc_offset_label(LONDON, utc(2026, 10, 13)) == "UTC+1"
    assert utc_offset_label(LONDON, utc(2026, 12, 13)) == "UTC+0"
    assert utc_offset_label(BALI, utc(2026, 10, 13)) == "UTC+8"


def test_clocks_use_local_weekday():
    instant = utc(2026, 10, 13, 16, 30)
    london = local_time(LONDON, instant)
    bali = local_time(BALI, instant)
    assert london.strftime("%A %H:%M") == "Tuesday 17:30"
    assert bali.strftime("%A %H:%M") == "Wednesday 00:30"


def test_empty_selection_has_zero_overlap():
    now = utc(2026, 10, 13)
    assert overlap_hours([], now, now + timedelta(days=7)) == 0.0


def test_no_overlap_warning_for_tokyo_and_london():
    now = utc(2026, 10, 24)
    warning = no_overlap_warning([TOKYO, LONDON], now, now + timedelta(days=7))
    assert warning is not None
    assert "Tokyo" in warning
    assert "London" in warning


def test_no_overlap_warning_absent_when_overlap_exists():
    now = utc(2026, 10, 13)
    assert no_overlap_warning([LONDON, BALI], now, now + timedelta(days=7)) is None


def test_no_overlap_warning_absent_for_empty_selection():
    now = utc(2026, 10, 13)
    assert no_overlap_warning([], now, now + timedelta(days=7)) is None


def test_catalog_sanity():
    assert len(CITY_CATALOG) == 36
    names = [city.name for city in CITY_CATALOG]
    assert len(names) == len(set(names))
    for city in CITY_CATALOG:
        assert ZoneInfo(city.tz) is not None
