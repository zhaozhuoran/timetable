# Timetable

Generate an auto-updating iCalendar (ICS) feed for class schedules and publish it via GitHub Pages.

- English README (this file)
- Simplified Chinese: [README.zh-cn.md](README.zh-cn.md)

## Features

- ICS generation with deterministic UIDs
- Visible window controls: `visible_weeks` and `visible_days` (OR logic)
- Holiday filtering: supports date ranges, single dates, and weekday filters
- Overrides: full-day reschedule (`use_weekday`) or per-period replacements
- GitHub Actions workflow and GitHub Pages deployment

## Quick Start (GitHub Action + GitHub Pages)

1. Modify JSON files in `data/` to configure your timetable. See "Data Structure" below for details.

2. Enable GitHub Actions workflow

After enabling, the ICS file will be automatically generated and published when you modify code or timetable data.

The workflow also runs automatically every morning at 6 AM.

3. Enable GitHub Pages in repository settings, select `gh-pages` branch as the publish source

4. Subscribe in your calendar

```
https://<username>.github.io/<repo>/calendar.ics
```

Example:

```
https://zhaozhuoran.github.io/timetable/calendar.ics
```

## Data Structure

See [CONFIG.md](CONFIG.md) for complete JSON examples and field descriptions. Key files:

- `data/periods.json`: period times
- `data/subjects.json`: subject ID to display name mapping
- `data/timetable.json`: main timetable config
- `data/holidays.json`: holiday definitions
- `data/overrides.json`: temporary override config
- `data/timetables/*.json`: concrete timetable files

Replace the example files in `data/` with your actual configuration before production use.

## GitHub Actions & GitHub Pages

This repository ships with an automated workflow at `.github/workflows/generate.yml`:

- Triggers on pushes to the `main` branch that touch `data/**`, `scripts/**`, `requirements.txt`, or the workflow file itself.
- Installs dependencies and runs `python scripts/generate_ics.py` to write `_site/calendar.ics`.
- Publishes the `_site/` directory to GitHub Pages using `peaceiris/actions-gh-pages` (by default the `gh-pages` branch).

Notes:

- Commits whose message contains `[SKIP]` will not trigger the workflow.
- The script copies any files under `static/` (for example `static/CNAME`) into `_site/` so they are served by Pages.
- After the first successful run, enable GitHub Pages in the repository settings and point it to the `gh-pages` branch (or the branch configured in the workflow).

## LICENSE

This project is licensed under the GNU General Public License v3.0 (GPLv3). See [LICENSE](LICENSE).
