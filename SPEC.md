# SPEC — Borderless Meeting Planner

Streamlit app that helps teams scattered across time zones find a timeslot where
every selected city is inside working hours (09:00–17:00 local time).

## UI (per provided design)

- **Sidebar — Cities**: multiselect over a fixed catalog of 36 cities; selected
  cities appear as removable pills; counter shows "N of 36 cities selected".
- **Main header**: title + subtitle "Find a timeslot where every city is inside
  09:00–17:00 local time".
- **Stats row**: "Cities" (count) and "Overlapping hours (next 7 days)" (float,
  one decimal, e.g. `7.0 h`).
- **Local clocks**: one column per city — name, live `HH:MM:SS` (ticks every
  second), and `↓ <Weekday>, UTC±H` derived from that city's local time.
- **24-hour local view**: legend chips (Outside working hours / Working hours /
  Overlap). Per city: label `"<City> — <Weekday YYYY-MM-DD> local · green =
  overlap"` and a strip of 24 cells labeled 0–23 for that city's current local
  date.
  - gray = outside working hours
  - blue = working hour, but not part of an overlap
  - green = working hour that is inside an overlap window

## Features

1. Add/remove cities from a curated catalog (name + IANA time zone).
2. Show each city's current local time, weekday, and UTC offset — correct across
   DST because offsets are computed per instant, never hardcoded.
3. Compute total overlapping hours over the next 7 days: hours when **all**
   selected cities are simultaneously inside 09:00–17:00 local time.
4. Highlight overlap hours in the 24-hour strips so users can see *when* the
   shared window falls in each city's day.
5. Warn when no overlap exists: if `overlap_hours(...) == 0` for a non-empty
   selection (e.g. Tokyo + London), show a warning naming the selected cities
   and suggesting a different combination.

## Data structures

```python
@dataclass(frozen=True)
class City:
    name: str          # "London"
    tz: str            # IANA key, e.g. "Europe/London"

CITY_CATALOG: list[City]  # 36 entries in cities.py
```

Pure functions in `logic.py` (no Streamlit imports):

| Function | Signature (conceptual) | Returns |
|---|---|---|
| `local_time` | `(city, instant_utc) -> datetime` | wall time in city's zone |
| `utc_offset_label` | `(city, instant_utc) -> str` | `"UTC+1"`, `"UTC-4"`, … |
| `is_working_hour` | `(city, instant_utc) -> bool` | local time in [09:00, 17:00) |
| `overlap_hours` | `(cities, start_utc, end_utc) -> float` | total hours all cities working |
| `overlap_windows` | `(cities, start_utc, end_utc) -> list[(start, end)]` | contiguous overlap ranges (UTC) |
| `no_overlap_warning` | `(cities, start_utc, end_utc) -> str \| None` | warning text if no overlap, else `None` |

Use stdlib `zoneinfo.ZoneInfo` for all conversions. `app.py` holds only UI code.

## Rules

- Working hours = **[09:00, 17:00)** local — start inclusive, end exclusive
  (exactly 8 working hours; 17:00 is *not* a working hour).
- Overlap scan: hour resolution over `[now, now + 7 days)`; a counted hour must
  have **every** city inside its own working hours at that instant.
- With 0 cities selected, overlap = `0.0` and clocks/view sections are hidden.
- With ≥1 selected city and `overlap = 0.0`, the app shows an `st.warning`
  naming the selected cities; the clocks/24-hour sections still render.
- Weekday/date labels always come from the city's own local time.

## Project layout

```
app.py              # Streamlit UI only (not yet implemented)
logic.py            # pure logic (zoneinfo), no streamlit import
cities.py           # CITY_CATALOG: 36 City entries
test_logic.py
test_app.py         # AppTest smoke tests for app.py
requirements.txt    # streamlit, pytest
```

Run: `.venv\Scripts\streamlit run app.py` · Test: `.venv\Scripts\pytest`

## Acceptance criteria (example test cases)

All tests inject a fixed `now` (UTC) so DST can never make them flaky.

1. **London + Bali overlap** — `now = 2026-10-13 00:00 UTC`
   (`Europe/London` = BST UTC+1, `Asia/Makassar` = WITA UTC+8, no DST):
   London works 08:00–16:00 UTC, Bali works 01:00–09:00 UTC → 1 h/day →
   `overlap_hours(...) == 7.0`. *(The UI mock's "5.0 h" is illustrative;
   this SPEC's math is authoritative.)*

2. **Same zone → full week** — London + Dublin, `now = 2026-10-13 00:00 UTC`:
   both work 08:00–16:00 UTC → `56.0`.

3. **No possible overlap** — Tokyo (`Asia/Tokyo`, UTC+9 → works 00:00–08:00 UTC)
   + New York (`America/New_York`, EST UTC-5 in January → works 14:00–22:00 UTC),
   `now = 2026-01-10 00:00 UTC` → `0.0`.

4. **Touching intervals do not overlap** — Tokyo + London, window
   `2026-10-24 00:00 UTC` → `0.0` (Tokyo ends 08:00 UTC where London's
   pre-transition day begins; end-exclusive means zero-length = no overlap).

5. **DST transition changes the overlap** — London + New York,
   `now = 2026-10-23 00:00 UTC` (London falls back Sun 2026-10-25; NY still EDT):
   Oct 23–24 → 3 h/day (`[13,16)` UTC), Oct 25–29 → 4 h/day (`[13,17)` UTC)
   → `26.0`.

6. **Hour boundaries** — with `Europe/London`:
   `2026-10-13 08:00 UTC` (09:00 BST) → working; `16:00 UTC` (17:00 BST) →
   not working; `07:59 UTC` (08:59 BST) → not working.

7. **Offset labels** — London on `2026-10-13` → `"UTC+1"`, on `2026-12-13` →
   `"UTC+0"`; Bali any date → `"UTC+8"`.

8. **Clocks use local weekday** — at `2026-10-13 16:30 UTC`: London shows
   Tuesday 17:30 (UTC+1), Bali shows Wednesday 00:30 (UTC+8) — same instant,
   different calendar day.

9. **Empty selection** — `overlap_hours([], now, now+7d) == 0.0`.

10. **Catalog sanity** — 36 cities; every `tz` resolves via `ZoneInfo`;
    no duplicate names.

11. **No-overlap warning** — Tokyo + London (window from `2026-10-24`) →
    `overlap_hours(...) == 0.0` and `no_overlap_warning(...)` returns text
    naming both cities; the app renders it via `st.warning`. London + Bali and
    an empty selection render no warning (`test_app.py`, AppTest).
