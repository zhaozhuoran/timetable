import json
import os
import shutil
import logging
from typing import Any, Dict, List, Tuple
from ics import Calendar, Event
from datetime import datetime, timedelta

# File paths
PERIODS_FILE = "data/periods.json"
SUBJECTS_FILE = "data/subjects.json"
TIMETABLE_FILE = "data/timetable.json"
HOLIDAYS_FILE = "data/holidays.json"
OVERRIDES_FILE = "data/overrides.json"
OUTPUT_ICS = "_site/calendar.ics"
STATIC_DIR = "static"
# ISO weekday bounds (1=Monday, 7=Sunday)
WEEKDAY_MIN = 1
WEEKDAY_MAX = 7


# Default term date range (for backward compatibility)
# These dates represent Spring 2025 (2025-02-20 to 2025-07-10) used when
# legacy timetable configs do not specify a term range.
# Can be overridden via environment variables DEFAULT_START_DATE / DEFAULT_END_DATE (YYYY-MM-DD).
def get_default_date(env_var: str, fallback_date: datetime) -> datetime:
    """Read date from environment variable or use the fallback value.

    Args:
        env_var: Name of the environment variable.
        fallback_date: Date to use when the variable is missing or invalid.

    Returns:
        datetime: Parsed date or the fallback.

    Note:
        If the variable exists but has invalid format (expected YYYY-MM-DD),
        a warning is logged and the fallback is used.
    """
    date_str = os.environ.get(env_var)
    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logging.warning(
                f"Invalid env var {env_var} (expected YYYY-MM-DD); using default {fallback_date.strftime('%Y-%m-%d')}"
            )
    return fallback_date


DEFAULT_START_DATE = get_default_date("DEFAULT_START_DATE", datetime(2025, 2, 20))
DEFAULT_END_DATE = get_default_date("DEFAULT_END_DATE", datetime(2025, 7, 10))


def load_json(filepath: str) -> Any:
    """Load and parse a JSON file."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    return data


def check_holiday_match(
    holiday: Dict[str, Any], day_str: str, current_date: datetime, weekday: int
) -> bool:
    """Check if a holiday entry matches the given date."""
    # Check if date matches
    if "date" in holiday:
        # Single date
        if holiday["date"] != day_str:
            return False
    elif "start" in holiday and "end" in holiday:
        # Date range
        start_date = datetime.strptime(holiday["start"], "%Y-%m-%d").date()
        end_date = datetime.strptime(holiday["end"], "%Y-%m-%d").date()
        if start_date > end_date:
            logging.warning(
                f"Malformed holiday entry (start date after end date): {holiday}"
            )
            return False
        if not (start_date <= current_date.date() <= end_date):
            return False
    else:
        # Malformed holiday entry - missing date or start/end
        logging.warning(
            f"Malformed holiday entry (missing date or start/end): {holiday}"
        )
        return False

    # Check filters if present
    if "filter" in holiday:
        filter_config = holiday["filter"]
        # Check weekday filter if present
        if "weekday" in filter_config:
            allowed_weekdays = filter_config["weekday"]
            if not isinstance(allowed_weekdays, list):
                allowed_weekdays = [allowed_weekdays]
            if weekday not in allowed_weekdays:
                return False

    # All conditions satisfied, it's a holiday
    return True


def is_holiday(current_date: datetime, holidays_data: Any) -> bool:
    """Return True if the date is a holiday (supports new/old formats)."""
    day_str = current_date.strftime("%Y-%m-%d")
    weekday = current_date.isoweekday()  # 1=Mon, 7=Sun

    # Handle new format: {"holidays": [...]}
    if isinstance(holidays_data, dict) and "holidays" in holidays_data:
        holidays_list = holidays_data["holidays"]
        if not isinstance(holidays_list, list):
            return False

        for holiday in holidays_list:
            if check_holiday_match(holiday, day_str, current_date, weekday):
                return True
        return False

    # Handle old format: {"YYYY-MM-DD": false}
    if isinstance(holidays_data, dict):
        return day_str in holidays_data and not holidays_data[day_str]

    # Handle list format: [...]
    if isinstance(holidays_data, list):
        for holiday in holidays_data:
            if check_holiday_match(holiday, day_str, current_date, weekday):
                return True

    return False


def get_timetable_list(timetable_data: Any) -> List[Dict[str, Any]]:
    """Extract timetable list from data (supports old/new formats)."""
    # Handle new timetable format: {"timetable": [...]}
    if isinstance(timetable_data, dict) and "timetable" in timetable_data:
        return timetable_data["timetable"]
    # Handle old format: [...]
    return timetable_data


def load_timetable_configs(
    timetable_main: Any,
) -> List[Tuple[List[Dict[str, Any]], datetime, datetime, int, int, bool]]:
    configs: List[Tuple[List[Dict[str, Any]], datetime, datetime, int, int, bool]] = []

    # Check version
    version = (
        timetable_main.get("$version", 1) if isinstance(timetable_main, dict) else 1
    )

    if (
        version == 2
        and isinstance(timetable_main, dict)
        and "timetables" in timetable_main
    ):
        # Version 2: Multiple timetable files with date ranges
        for config in timetable_main["timetables"]:
            timetable_file = config["file"]
            start_date = datetime.strptime(config["start"], "%Y-%m-%d")
            end_date = datetime.strptime(config["end"], "%Y-%m-%d")
            visible_weeks = config.get("visible_weeks", 2)  # Default to 2 weeks
            visible_days = config.get("visible_days", 0)  # Default to 0 days
            ignore_past_days = config.get("ignore_past_days", False)  # Default to False

            # Validate that start date comes before end date
            if start_date > end_date:
                raise ValueError(
                    f"Invalid date range in {timetable_file}: start date {config['start']} is after end date {config['end']}"
                )

            # Load the timetable file
            timetable_data = load_json(timetable_file)
            timetable_list = get_timetable_list(timetable_data)

            configs.append(
                (
                    timetable_list,
                    start_date,
                    end_date,
                    visible_weeks,
                    visible_days,
                    ignore_past_days,
                )
            )

        # Check for overlapping date ranges
        for i, (_, start1, end1, _, _, _) in enumerate(configs):
            for j, (_, start2, end2, _, _, _) in enumerate(configs[i + 1 :], i + 1):
                if start1 <= end2 and start2 <= end1:
                    logging.warning(
                        f"Overlapping date ranges detected between timetable {i} ({start1.date()} to {end1.date()}) and {j} ({start2.date()} to {end2.date()})"
                    )
    else:
        # Version 1: Single timetable with hardcoded dates
        timetable_list = get_timetable_list(timetable_main)
        # Use default dates for backward compatibility
        configs.append(
            (timetable_list, DEFAULT_START_DATE, DEFAULT_END_DATE, 2, 0, False)
        )  # Default to 2 weeks, 0 days, ignore_past_days=False

    return configs


def add_event(
    cal: Calendar,
    periods: Dict[str, Dict[str, str]],
    subjects: Dict[str, str],
    period_id: Any,
    subject_id: Any,
    current_date: datetime,
    day_str: str,
    context: str,
) -> bool:
    """Create and add a single timetable event to the calendar."""
    period_key = str(period_id)
    subject_key = str(subject_id)
    if period_key not in periods:
        logging.warning(
            f"Period {period_key} not found in {context} for {day_str}, skipping"
        )
        return False
    period = periods[period_key]
    e = Event()
    subject_name = subjects.get(subject_key, None)
    if subject_name is None:
        logging.warning(
            f"Subject {subject_key} not found in subjects.json for {context} on {day_str}"
        )
        subject_name = subject_key
    e.name = subject_name
    e.begin = datetime.combine(
        current_date.date(), datetime.strptime(period["start"], "%H:%M").time()
    )
    e.end = datetime.combine(
        current_date.date(), datetime.strptime(period["end"], "%H:%M").time()
    )
    e.uid = f"{day_str}-{period_key}-{subject_id}@yearcakes.timetable.school.ics"
    cal.events.add(e)
    return True


def main() -> None:
    """Entry point to generate the ICS file."""
    periods: Dict[str, Dict[str, str]] = load_json(PERIODS_FILE)
    subjects: Dict[str, str] = load_json(SUBJECTS_FILE)
    timetable_data = load_json(TIMETABLE_FILE)
    holidays = load_json(HOLIDAYS_FILE)
    overrides = load_json(OVERRIDES_FILE)

    # Filter out $version field from periods, subjects, holidays, and overrides
    if isinstance(periods, dict):
        periods = {k: v for k, v in periods.items() if k != "$version"}
    if isinstance(subjects, dict):
        subjects = {k: v for k, v in subjects.items() if k != "$version"}
    if isinstance(holidays, dict):
        holidays = {k: v for k, v in holidays.items() if k != "$version"}
    if isinstance(overrides, dict):
        overrides = {k: v for k, v in overrides.items() if k != "$version"}

    # Load timetable configurations (supports both v1 and v2)
    timetable_configs = load_timetable_configs(timetable_data)

    cal = Calendar()

    # Process each timetable configuration
    for (
        timetable,
        start_date,
        end_date,
        visible_weeks,
        visible_days,
        ignore_past_days,
    ) in timetable_configs:
        # Calculate the current week's Monday using local time
        now = datetime.now()
        current_week_monday = now - timedelta(days=now.weekday())
        current_week_monday = current_week_monday.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Get today's date (midnight)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        weeks_enabled = visible_weeks > 0
        days_enabled = visible_days > 0

        # If both visibility constraints are disabled, skip this timetable
        if not weeks_enabled and not days_enabled:
            continue

        # Calculate the effective end date based on visible_weeks and visible_days
        # Use OR logic: satisfy either visible_weeks or visible_days
        # visible_weeks = 1 means current week only (Monday to Sunday)
        # visible_weeks = 2 means current week + next week, etc.
        # End on Sunday of the last week: Monday + (weeks * 7) - 1
        weeks_end_date = (
            current_week_monday + timedelta(days=visible_weeks * 7 - 1)
            if weeks_enabled
            else None
        )

        # visible_days = 0 means disabled
        # visible_days = 1 means today only
        # visible_days = N means today + (N-1) more days
        days_end_date = (
            today + timedelta(days=visible_days - 1) if days_enabled else None
        )

        if weeks_end_date is not None and days_end_date is not None:
            calculated_end_date = max(weeks_end_date, days_end_date)
        elif weeks_end_date is not None:
            calculated_end_date = weeks_end_date
        else:
            calculated_end_date = days_end_date

        # Use the minimum of configured end_date and calculated end_date
        effective_end_date = min(end_date, calculated_end_date)

        # Use the maximum of configured start_date and the relevant start anchor
        start_anchor = current_week_monday if weeks_enabled else today
        effective_start_date = max(start_date, start_anchor)

        # If ignore_past_days is enabled, also ensure we don't include dates before today
        if ignore_past_days:
            effective_start_date = max(effective_start_date, today)

        # Skip this timetable config if the effective range is invalid,
        # unless there is an explicit override for the configured start date.
        if effective_start_date > effective_end_date:
            start_day_str = start_date.strftime("%Y-%m-%d")
            if isinstance(overrides, dict) and start_day_str in overrides:
                current = start_date
                effective_end_date = start_date
            else:
                continue

        delta = timedelta(days=1)
        current = effective_start_date

        while current <= effective_end_date:
            day_str = current.strftime("%Y-%m-%d")
            weekday = current.isoweekday()  # 1=Mon, 7=Sun

            # Skip holidays
            if is_holiday(current, holidays):
                current += delta
                continue

            # Overrides for the current date
            if day_str in overrides:
                override_entry = overrides[day_str]
                # Full-day reschedule: use another weekday's timetable
                if isinstance(override_entry, dict) and "use_weekday" in override_entry:
                    try:
                        source_weekday = int(override_entry["use_weekday"])
                    except (TypeError, ValueError):
                        logging.warning(
                            f"Invalid use_weekday value in override for {day_str}, skipping"
                        )
                        current += delta
                        continue
                    if source_weekday < WEEKDAY_MIN or source_weekday > WEEKDAY_MAX:
                        logging.warning(
                            f"use_weekday must be between {WEEKDAY_MIN} and {WEEKDAY_MAX} in override for {day_str}, skipping"
                        )
                        current += delta
                        continue
                    added = 0
                    for item in timetable:
                        if item["weekday"] == source_weekday:
                            if add_event(
                                cal,
                                periods,
                                subjects,
                                item["period"],
                                item["subject"],
                                current,
                                day_str,
                                "reschedule",
                            ):
                                added += 1
                    if added == 0:
                        logging.warning(
                            f"No timetable entries found for weekday {source_weekday} in reschedule for {day_str}"
                        )
                    current += delta
                    continue

                # Per-period overrides
                if isinstance(override_entry, list):
                    for o in override_entry:
                        add_event(
                            cal,
                            periods,
                            subjects,
                            o["period"],
                            o["subject"],
                            current,
                            day_str,
                            "override",
                        )
                    current += delta
                    continue

                logging.warning(f"Invalid override format for {day_str}, skipping")
                current += delta
                continue

            # Normal timetable entries
            for item in timetable:
                if item["weekday"] == weekday:
                    add_event(
                        cal,
                        periods,
                        subjects,
                        item["period"],
                        item["subject"],
                        current,
                        day_str,
                        "timetable",
                    )

            current += delta

    # Output ICS
    output_dir = os.path.dirname(OUTPUT_ICS)
    os.makedirs(output_dir, exist_ok=True)
    ics_content = cal.serialize()

    # Convert UTC times to floating time (local time) by removing the 'Z' suffix
    # This makes the ICS file use local timestamps instead of UTC
    lines = ics_content.splitlines()
    converted_lines: List[str] = []
    for line in lines:
        if line.startswith("DTSTART:") or line.startswith("DTEND:"):
            # Remove 'Z' suffix to convert from UTC to floating time
            if line.endswith("Z"):
                line = line[:-1]
        converted_lines.append(line)
    ics_content = "\r\n".join(converted_lines)

    with open(OUTPUT_ICS, "w", encoding="utf-8") as f:
        f.write(ics_content)

    # Copy static assets (e.g., CNAME) into output directory
    if os.path.isdir(STATIC_DIR):
        for item in os.listdir(STATIC_DIR):
            src_path = os.path.join(STATIC_DIR, item)
            dest_path = os.path.join(output_dir, item)
            if os.path.isfile(src_path):
                try:
                    shutil.copy2(src_path, dest_path)
                except (OSError, shutil.Error) as e:
                    logging.warning(
                        "Failed to copy static asset '%s' to '%s': %s",
                        src_path,
                        dest_path,
                        e,
                    )

    print(f"ICS file generated: {OUTPUT_ICS}")


if __name__ == "__main__":
    # Configure logging only when running as a script
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    main()
