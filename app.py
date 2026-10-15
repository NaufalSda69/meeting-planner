from datetime import datetime, time, timedelta, timezone

import streamlit as st

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

st.set_page_config(page_title="Borderless Meeting Planner", layout="wide")

COLORS = {
    "outside": ("#f0f2f6", "#a3a8b8"),
    "working": ("#d6e4ff", "#1c2733"),
    "overlap": ("#2eb086", "#ffffff"),
}


def chip(label: str, state: str) -> str:
    bg, fg = COLORS[state]
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 10px;'
        f'border-radius:4px;font-size:0.78rem;margin-right:8px;">{label}</span>'
    )


def hour_cell(hour: int, state: str) -> str:
    bg, fg = COLORS[state]
    return (
        f'<div style="flex:1;min-width:0;padding:6px 0;text-align:center;'
        f"background:{bg};color:{fg};font-size:0.72rem;border-radius:4px;"
        f'margin:2px 1px;">{hour}</div>'
    )


@st.fragment(run_every=timedelta(seconds=1))
def render_clocks(cities: list[City]) -> None:
    now_utc = datetime.now(timezone.utc)
    for start in range(0, len(cities), 4):
        cols = st.columns(4)
        for col, city in zip(cols, cities[start : start + 4]):
            with col:
                local = local_time(city, now_utc)
                st.markdown(f"**{city.name}**")
                st.markdown(f"### {local.strftime('%H:%M:%S')}")
                st.caption(
                    f"\u2193 {local.strftime('%A')}, "
                    f"{utc_offset_label(city, now_utc)}"
                )


with st.sidebar:
    st.subheader("Cities")
    selected_names = st.multiselect(
        "Add or remove cities",
        options=[city.name for city in CITY_CATALOG],
        default=["London", "Bali"],
    )
    st.caption(f"{len(selected_names)} of {len(CITY_CATALOG)} cities selected")

st.title("Borderless Meeting Planner")
st.caption("Find a timeslot where every city is inside 09:00\u201317:00 local time")

catalog = {city.name: city for city in CITY_CATALOG}
cities = [catalog[name] for name in selected_names]

now = datetime.now(timezone.utc)
window_start = now.replace(minute=0, second=0, microsecond=0)
window_end = window_start + timedelta(days=7)

metric_cols = st.columns([1, 1, 6])
metric_cols[0].metric("Cities", len(cities))
metric_cols[1].metric(
    "Overlapping hours (next 7 days)",
    f"{overlap_hours(cities, window_start, window_end):.1f} h",
)

if not cities:
    st.info("Add at least one city from the sidebar to see clocks and overlap.")
    st.stop()

warning = no_overlap_warning(cities, window_start, window_end)
if warning:
    st.warning(warning)

windows = overlap_windows(cities, window_start, window_end)

st.subheader("Local clocks")
render_clocks(cities)

st.subheader("24-hour local view")
st.markdown(
    chip("Outside working hours", "outside")
    + chip("Working hours", "working")
    + chip("Overlap", "overlap"),
    unsafe_allow_html=True,
)

for city in cities:
    local_now = local_time(city, now)
    st.markdown(
        f"**{city.name}** \u2014 {local_now.strftime('%a %Y-%m-%d')} local "
        "\u00b7 green = overlap"
    )
    cells = []
    for hour in range(24):
        instant = datetime.combine(local_now.date(), time(hour), tzinfo=city.zone)
        if not is_working_hour(city, instant):
            state = "outside"
        elif any(
            instant < window_end_ and instant + timedelta(hours=1) > window_start_
            for window_start_, window_end_ in windows
        ):
            state = "overlap"
        else:
            state = "working"
        cells.append(hour_cell(hour, state))
    st.markdown(
        f'<div style="display:flex;width:100%;">{"".join(cells)}</div>',
        unsafe_allow_html=True,
    )
