from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

WORK_START_HOUR = 9
WORK_END_HOUR = 17


@dataclass(frozen=True)
class City:
    name: str
    tz: str

    @property
    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.tz)


def local_time(city: City, instant_utc: datetime) -> datetime:
    return instant_utc.astimezone(city.zone)


def utc_offset_label(city: City, instant_utc: datetime) -> str:
    offset = local_time(city, instant_utc).utcoffset() or timedelta(0)
    total_minutes = int(offset.total_seconds()) // 60
    sign = "+" if total_minutes >= 0 else "-"
    hours, minutes = divmod(abs(total_minutes), 60)
    if minutes:
        return f"UTC{sign}{hours}:{minutes:02d}"
    return f"UTC{sign}{hours}"


def is_working_hour(city: City, instant_utc: datetime) -> bool:
    hour = local_time(city, instant_utc).hour
    return WORK_START_HOUR <= hour < WORK_END_HOUR


def overlap_hours(
    cities: list[City], start_utc: datetime, end_utc: datetime
) -> float:
    return float(len(_working_instants(cities, start_utc, end_utc)))


def overlap_windows(
    cities: list[City], start_utc: datetime, end_utc: datetime
) -> list[tuple[datetime, datetime]]:
    windows: list[list[datetime]] = []
    for instant in _working_instants(cities, start_utc, end_utc):
        end_of_hour = instant + timedelta(hours=1)
        if windows and instant == windows[-1][1]:
            windows[-1][1] = end_of_hour
        else:
            windows.append([instant, end_of_hour])
    return [(start, end) for start, end in windows]


def no_overlap_warning(
    cities: list[City], start_utc: datetime, end_utc: datetime
) -> str | None:
    if not cities or overlap_hours(cities, start_utc, end_utc) > 0:
        return None
    days = max(1, round((end_utc - start_utc).total_seconds() / 86400))
    names = ", ".join(city.name for city in cities)
    return (
        f"No overlapping working hours for {names} in the next {days} days. "
        "Try removing a city or picking a different combination."
    )


def _working_instants(
    cities: list[City], start_utc: datetime, end_utc: datetime
) -> list[datetime]:
    if not cities:
        return []
    instants = []
    instant = start_utc
    while instant < end_utc:
        if all(is_working_hour(city, instant) for city in cities):
            instants.append(instant)
        instant += timedelta(hours=1)
    return instants
