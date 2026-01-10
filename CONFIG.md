# Configuration Guide

- English (this file)
- Simplified Chinese: [CONFIG.zh-cn.md](CONFIG.zh-cn.md)

This document describes how to configure timetable data.

## Files Overview

All configuration files live under `data/`:

- `periods.json` – period time definitions
- `subjects.json` – subject ID to display name mapping
- `timetable.json` – main timetable config
- `timetables/` – concrete timetable files
- `holidays.json` – holiday definitions
- `overrides.json` – temporary overrides

## periods.json

Define period time ranges.

### Format

```json
{
  "1": { "start": "08:00", "end": "08:45" },
  "2": { "start": "08:55", "end": "09:40" },
  "3": { "start": "10:00", "end": "10:45" }
}
```

### Notes

- Keys are period IDs (strings)
- `start` and `end` are times in `HH:MM` (24-hour)

## subjects.json

Map subject IDs to display names.

### Format

```json
{
  "Math": "Mathematics",
  "English": "English Language",
  "Physics": "Physics"
}
```

### Notes

- Keys: subject IDs (referenced by timetables)
- Values: display names shown in calendar events

## timetable.json

Main timetable configuration. Supports two versions.

### Version 2 (recommended)

Supports multiple timetable files, each with its own date range:

```json
{
  "$version": 2,
  "timetables": [
    {
      "file": "data/timetables/spring2025.json",
      "start": "2025-02-20",
      "end": "2025-06-30",
      "visible_weeks": 2,
      "visible_days": 0,
      "ignore_past_days": false
    },
    {
      "file": "data/timetables/summer2025.json",
      "start": "2025-07-01",
      "end": "2025-07-10",
      "visible_weeks": 1,
      "visible_days": 1,
      "ignore_past_days": true
    }
  ]
}
```

### Version 1 (legacy-compatible)

Define a direct timetable array:

```json
{
  "$version": 1,
  "timetable": [
    { "weekday": 1, "period": "1", "subject": "Math" },
    { "weekday": 2, "period": "1", "subject": "English" }
  ]
}
```

Or use the original bare array format:

```json
[
  { "weekday": 1, "period": 1, "subject": "Math" },
  { "weekday": 6, "period": 1, "subject": "Physics" }
]
```

### Field Details

- `$version`: version (1 or 2)
- `timetables`: array of timetable configs (v2)
  - `file`: path to timetable file
  - `start`: start date (YYYY-MM-DD)
  - `end`: end date (YYYY-MM-DD)
  - `visible_weeks`: number of weeks shown (default 2)
    - 0 = disable week window, rely on `visible_days`
    - 1 = current week only
    - 2 = current + next week, and so on
  - `visible_days`: number of days shown (default 0)
    - 0 = disable day window, rely on `visible_weeks`
    - 1 = today only
    - N = today + (N-1) more days
    - Note: Uses OR logic with `visible_weeks`; satisfying either is enough. If both are 0, the timetable is skipped. Example: `visible_weeks=1` and `visible_days=1` shows the full current week even on Sunday. If you only want Monday preview on Sunday, set `visible_days=2` and `visible_weeks=0`.
  - `ignore_past_days`: whether to skip events before today (default false)
    - true = exclude days before today (whole-day granularity)
    - false = include all events in range
- `timetable`: array (v1)

## timetables/\*.json

Concrete timetable files defining weekly schedules.

### Format

```json
{
  "$version": 1,
  "timetable": [
    { "weekday": 1, "period": "1", "subject": "Math" },
    { "weekday": 1, "period": "2", "subject": "English" },
    { "weekday": 2, "period": "1", "subject": "Physics" },
    { "weekday": 6, "period": "1", "subject": "Music" }
  ]
}
```

### Field Details

- `weekday`: 1=Mon, 2=Tue, ..., 7=Sun
- `period`: period ID (string, must exist in `periods.json`)
- `subject`: subject ID (must exist in `subjects.json`)

## holidays.json

Define holidays; events are not generated on holidays.

### New Format (v1, recommended)

Supports date ranges and filters:

```json
{
  "$version": 1,
  "holidays": [
    {
      "start": "2025-01-01",
      "end": "2025-01-03",
      "comment": "New Year"
    },
    {
      "date": "2025-06-14",
      "comment": "Dragon Boat Festival"
    },
    {
      "start": "2025-07-01",
      "end": "2025-08-31",
      "filter": {
        "weekday": [6, 7]
      },
      "comment": "Summer weekends"
    }
  ]
}
```

### Old Format (legacy-compatible)

Simple date → boolean mapping (`false` means skip):

```json
{
  "2025-01-01": false,
  "2025-12-25": false
}
```

### Field Details

New format supports:

- `date`: single date (YYYY-MM-DD)
- `start` + `end`: date range (YYYY-MM-DD)
- `filter`: optional filters
  - `weekday`: array of weekdays (1-7)
- `comment`: optional note

## overrides.json

Define temporary overrides replacing normal schedules.

### Format

```json
{
  "2025-12-01": { "use_weekday": 1 },
  "2025-12-10": [
    { "period": "2", "subject": "Math" },
    { "period": "3", "subject": "Physics" }
  ],
  "2025-12-15": [{ "period": "1", "subject": "English" }]
}
```

### Field Details

- Keys: dates (YYYY-MM-DD)
- Values: two forms
  - `{"use_weekday": <1-7>}`: full-day reschedule using another weekday’s timetable
  - List of `{period, subject}`: per-period replacements only
  - `use_weekday` applies the source weekday’s full schedule regardless of the target day’s own weekday
  - The two forms are mutually exclusive for the same date

### Notes

- When a date has overrides, the normal timetable for that date is ignored
- Only events defined by overrides are added

## Tips

1. Test locally with `python scripts/generate_ics.py` after changes.
2. Back up the `data/` folder before major edits.
3. Use `YYYY-MM-DD` for all dates.
4. Use `HH:MM` (24-hour) for all times.
5. Ensure all JSON files are saved as UTF-8.

## CI / Deployment

The GitHub Actions workflow at `.github/workflows/generate.yml` wires configuration to automatic publishing:

- On pushes to `main` that modify `data/**`, `scripts/**`, `requirements.txt`, or the workflow file, the job runs.
- The job installs dependencies, executes `python scripts/generate_ics.py`, and writes the resulting ICS file into `_site/calendar.ics`.
- The `_site/` directory becomes the publish root for GitHub Pages via `peaceiris/actions-gh-pages` (by default deployed to the `gh-pages` branch).

Practical notes:

- Files in `static/` (for example `static/CNAME`) are copied into `_site/` during generation so they are also deployed.
- You can skip the workflow for a specific commit by including `[SKIP]` in the commit message.
- After confirming that `_site/calendar.ics` is generated correctly from your configuration, enable GitHub Pages in the repository settings and select the branch used by the workflow (typically `gh-pages`).
