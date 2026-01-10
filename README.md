<!-- See <attachments> above for file contents. You may not need to search or read the file again. -->

# Timetable ICS

Generate an auto-updating iCalendar (ICS) feed for class schedules and publish it via GitHub Pages.

- English README (this file)
- Simplified Chinese: [README.zh-cn.md](README.zh-cn.md)

## Features

- ICS generation with deterministic UIDs.
- Visible window controls: `visible_weeks` and `visible_days` (OR logic).
- Holiday filtering (range and single-day, with optional weekday filters).
- Overrides: full-day reschedule (`use_weekday`) or per-period replacements.
- Supports timetable v1/v2 and `$version` metadata.
- GitHub Actions build + GitHub Pages publishing.

## Quick Start

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Generate ICS

```bash
python scripts/generate_ics.py
```

Output is written to `_site/calendar.ics` (folder auto-created).

3. Subscribe (example)

```
https://<username>.github.io/<repo>/calendar.ics
```

## Data Schema

See [CONFIG.md](CONFIG.md) for complete examples and field descriptions. Key files:

- `data/periods.json`: period times, `start`/`end` (HH:MM)
- `data/subjects.json`: subject ID → name mapping
- `data/timetable.json`: v1 (single list) or v2 (multiple files + date ranges)
- `data/holidays.json`: holidays in old/new formats
- `data/overrides.json`: overrides (either `{use_weekday}` or list of `{period, subject}`)

The sample data in `data/` is fictional and safe to publish. Swap in your own schedules before production use.

## GitHub Actions & GitHub Pages

This repository ships with an automated workflow at `.github/workflows/generate.yml`:

- Triggers on pushes to the `main` branch that touch `data/**`, `scripts/**`, `requirements.txt`, or the workflow file itself.
- Installs dependencies and runs `python scripts/generate_ics.py` to write `_site/calendar.ics`.
- Publishes the `_site/` directory to GitHub Pages using `peaceiris/actions-gh-pages` (by default the `gh-pages` branch).

Notes:

- Commits whose message contains `[SKIP]` will not trigger the workflow.
- The script copies any files under `static/` (for example `static/CNAME`) into `_site/` so they are served by Pages.
- After the first successful run, enable GitHub Pages in the repository settings and point it to the `gh-pages` branch (or the branch configured in the workflow).

## Testing

Use Python’s unittest:

```bash
python -m unittest discover
```

Tests temporarily modify `data/timetable.json` and restore it afterward, and clean `_site/` when needed.

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3). See [LICENSE](LICENSE).
