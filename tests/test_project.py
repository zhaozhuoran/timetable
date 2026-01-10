import unittest
import json
import os
import sys
import re
import subprocess
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MIN_VISIBLE_DAYS = 7
# Index used with datetime.date.weekday() where Monday=0 and Sunday=6
SUNDAY_INDEX = 6
# ISO weekday used with datetime.date.isoweekday() where Monday=1 and Sunday=7
MONDAY_WEEKDAY = 1


class TestDataFiles(unittest.TestCase):
    """Test that all required data files exist and have valid structure"""
    
    def filter_version_field(self, data):
        """Helper method to filter out $version field from dict data.
        
        Args:
            data: The data to filter, should be a dict
            
        Returns:
            Filtered dict without $version field
            
        Raises:
            TypeError: If data is not a dict
        """
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if k != "$version"}
        else:
            raise TypeError(f"Expected dict but got {type(data).__name__}")
    
    def test_periods_json_exists(self):
        """Test that periods.json exists and is valid JSON"""
        self.assertTrue(os.path.exists("data/periods.json"))
        with open("data/periods.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)
        self.assertGreater(len(data), 0)
        
    def test_periods_json_structure(self):
        """Test that periods.json has correct structure"""
        with open("data/periods.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        # Skip $version field if present
        # Try-catch ensures test is self-contained and validates data is dict
        try:
            data = self.filter_version_field(data)
        except TypeError as e:
            self.fail(str(e))
        for period_id, period_data in data.items():
            self.assertIn("start", period_data)
            self.assertIn("end", period_data)
            # Validate time format
            datetime.strptime(period_data["start"], "%H:%M")
            datetime.strptime(period_data["end"], "%H:%M")
    
    def test_subjects_json_exists(self):
        """Test that subjects.json exists and is valid JSON"""
        self.assertTrue(os.path.exists("data/subjects.json"))
        with open("data/subjects.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)
        self.assertGreater(len(data), 0)
    
    def test_timetable_json_exists(self):
        """Test that timetable.json exists and is valid JSON"""
        self.assertTrue(os.path.exists("data/timetable.json"))
        with open("data/timetable.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        # Support old format (list), v1 format (dict with "timetable" key), and v2 format (dict with "timetables" key)
        if isinstance(data, dict):
            version = data.get("$version", 1)
            if version == 2:
                self.assertIn("timetables", data)
                self.assertIsInstance(data["timetables"], list)
            else:
                self.assertIn("timetable", data)
                self.assertIsInstance(data["timetable"], list)
        else:
            self.assertIsInstance(data, list)
    
    def test_timetable_json_structure(self):
        """Test that timetable.json has correct structure"""
        with open("data/timetable.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Check version
        version = data.get("$version", 1) if isinstance(data, dict) else 1
        
        if version == 2:
            # Version 2: Validate timetables array
            self.assertIn("timetables", data)
            timetables = data["timetables"]
            self.assertIsInstance(timetables, list)
            self.assertGreater(len(timetables), 0)
            
            for timetable_config in timetables:
                # Each config should have file, start, and end
                self.assertIn("file", timetable_config)
                self.assertIn("start", timetable_config)
                self.assertIn("end", timetable_config)
                
                # Validate date format
                start_dt = datetime.strptime(timetable_config["start"], "%Y-%m-%d")
                end_dt = datetime.strptime(timetable_config["end"], "%Y-%m-%d")
                
                # Validate that start date is before or equal to end date
                self.assertLessEqual(start_dt, end_dt, 
                    f"Start date must be before or equal to end date in {timetable_config}")
                
                # Validate referenced file exists and has correct structure
                timetable_file = timetable_config["file"]
                self.assertTrue(os.path.exists(timetable_file), f"Referenced timetable file not found: {timetable_file}")
                
                with open(timetable_file, "r", encoding="utf-8") as f:
                    timetable_data = json.load(f)
                
                # Get timetable list from referenced file
                if isinstance(timetable_data, dict) and "timetable" in timetable_data:
                    timetable_list = timetable_data["timetable"]
                else:
                    timetable_list = timetable_data
                
                # Validate timetable entries
                for item in timetable_list:
                    self.assertIn("weekday", item)
                    self.assertIn("period", item)
                    self.assertIn("subject", item)
                    self.assertGreaterEqual(item["weekday"], 1)
                    self.assertLessEqual(item["weekday"], 7)
                    # period can be either int or string
                    self.assertTrue(isinstance(item["period"], (int, str)))
        else:
            # Version 1: Validate timetable array directly or under "timetable" key
            if isinstance(data, dict):
                if "$version" in data:
                    try:
                        data = self.filter_version_field(data)
                    except TypeError as e:
                        self.fail(str(e))
                timetable = data["timetable"]
            else:
                timetable = data
            
            for item in timetable:
                self.assertIn("weekday", item)
                self.assertIn("period", item)
                self.assertIn("subject", item)
                self.assertGreaterEqual(item["weekday"], 1)
                self.assertLessEqual(item["weekday"], 7)
                # period can be either int or string
                self.assertTrue(isinstance(item["period"], (int, str)))
    
    def test_holidays_json_exists(self):
        """Test that holidays.json exists and is valid JSON"""
        self.assertTrue(os.path.exists("data/holidays.json"))
        with open("data/holidays.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)
    
    def test_holidays_json_structure(self):
        """Test that holidays.json has correct date format"""
        with open("data/holidays.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        # Support both old format (date: bool mapping) and new format (dict with "holidays" list)
        if isinstance(data, dict):
            # Skip $version field if present
            try:
                data = self.filter_version_field(data)
            except TypeError as e:
                self.fail(str(e))
            if "holidays" in data:
                # New format: validate list of holiday objects
                holidays_list = data["holidays"]
                self.assertIsInstance(holidays_list, list)
                for holiday in holidays_list:
                    # Each holiday should have either "date" or "start"/"end"
                    if "date" in holiday:
                        datetime.strptime(holiday["date"], "%Y-%m-%d")
                    elif "start" in holiday and "end" in holiday:
                        start_dt = datetime.strptime(holiday["start"], "%Y-%m-%d")
                        end_dt = datetime.strptime(holiday["end"], "%Y-%m-%d")
                        # Validate that start is before or equal to end
                        self.assertLessEqual(start_dt, end_dt, 
                            f"Holiday start date must be before or equal to end date: {holiday}")
                    else:
                        self.fail(f"Holiday entry must have either 'date' or both 'start' and 'end': {holiday}")
                    # comment and filter are optional
            else:
                # Old format: dict with date: bool
                for date_str, value in data.items():
                    # Validate date format YYYY-MM-DD
                    datetime.strptime(date_str, "%Y-%m-%d")
                    self.assertIsInstance(value, bool)
    
    def test_overrides_json_exists(self):
        """Test that overrides.json exists and is valid JSON"""
        self.assertTrue(os.path.exists("data/overrides.json"))
        with open("data/overrides.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)
    
    def test_overrides_json_structure(self):
        """Test that overrides.json has correct structure"""
        with open("data/overrides.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        # Skip $version field if present
        # Try-catch ensures test is self-contained and validates data is dict
        try:
            data = self.filter_version_field(data)
        except TypeError as e:
            self.fail(str(e))
        for date_str, overrides in data.items():
            # Validate date format YYYY-MM-DD
            datetime.strptime(date_str, "%Y-%m-%d")
            # Allow full-day reschedule or per-period list
            if isinstance(overrides, dict):
                self.assertIn("use_weekday", overrides)
                use_weekday = overrides["use_weekday"]
                self.assertIsInstance(use_weekday, (int, str))
                if isinstance(use_weekday, str):
                    try:
                        int(use_weekday)
                    except (TypeError, ValueError):
                        self.fail(f"use_weekday must be an integer or a numeric string, got {use_weekday!r}")
            else:
                self.assertIsInstance(overrides, list)
                for override in overrides:
                    self.assertIn("period", override)
                    self.assertIn("subject", override)


class TestScriptFiles(unittest.TestCase):
    """Test that script files exist and are valid"""
    
    def test_generate_ics_script_exists(self):
        """Test that generate_ics.py exists"""
        self.assertTrue(os.path.exists("scripts/generate_ics.py"))
    
    def test_generate_ics_script_syntax(self):
        """Test that generate_ics.py has valid Python syntax"""
        with open("scripts/generate_ics.py", "r", encoding="utf-8") as f:
            code = f.read()
        try:
            compile(code, "scripts/generate_ics.py", "exec")
        except SyntaxError as e:
            self.fail(f"Syntax error in generate_ics.py: {e}")


class TestWorkflowFiles(unittest.TestCase):
    """Test that workflow files exist"""
    
    def test_generate_workflow_exists(self):
        """Test that generate.yml exists"""
        self.assertTrue(os.path.exists(".github/workflows/generate.yml"))


class TestICSGeneration(unittest.TestCase):
    """Test ICS file generation"""
    
    def setUp(self):
        """Prepare timetable config to always include current week events"""
        if os.path.exists("data/timetable.json"):
            shutil.copy("data/timetable.json", "data/timetable.json.backup")
            with open("data/timetable.json", "r", encoding="utf-8") as f:
                timetable_config = json.load(f)
            if isinstance(timetable_config, dict) and "timetables" in timetable_config:
                for config in timetable_config["timetables"]:
                    config["ignore_past_days"] = False
                    # Set minimum visible_days to reduce chance of empty calendars when holidays overlap test dates
                    config["visible_days"] = max(config.get("visible_days", 0), MIN_VISIBLE_DAYS)
            with open("data/timetable.json", "w", encoding="utf-8") as f:
                json.dump(timetable_config, f, indent=2, ensure_ascii=False)
        if os.path.exists("_site"):
            shutil.rmtree("_site")
    
    def tearDown(self):
        """Restore timetable config and clean generated files"""
        if os.path.exists("data/timetable.json.backup"):
            shutil.move("data/timetable.json.backup", "data/timetable.json")
        if os.path.exists("_site"):
            shutil.rmtree("_site")
    
    def test_ics_file_generated(self):
        """Test that ICS file can be generated"""
        # Run the generation script
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        self.assertTrue(os.path.exists("_site/calendar.ics"))
    
    def test_ics_file_content(self):
        """Test that ICS file has valid content"""
        # Ensure ICS file is generated
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        
        self.assertTrue(os.path.exists("_site/calendar.ics"))
        with open("_site/calendar.ics", "r", encoding="utf-8") as f:
            content = f.read()
        # Check for ICS format markers
        self.assertIn("BEGIN:VCALENDAR", content)
        self.assertIn("END:VCALENDAR", content)
        self.assertIn("BEGIN:VEVENT", content)
        self.assertIn("END:VEVENT", content)
    
    def test_static_cname_copied(self):
        """Test that static CNAME file is copied to output"""
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")

        cname_path = os.path.join("_site", "CNAME")
        self.assertTrue(os.path.exists(cname_path), "CNAME file was not copied to _site")
        with open(os.path.join("static", "CNAME"), "r", encoding="utf-8") as f:
            expected_cname = f.read().strip()
        with open(cname_path, "r", encoding="utf-8") as f:
            cname_content = f.read().strip()
        self.assertEqual(cname_content, expected_cname)
    
    def test_ics_deterministic_uids(self):
        """Test that ICS file uses deterministic UIDs in the correct format"""
        # Ensure ICS file is generated
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        
        self.assertTrue(os.path.exists("_site/calendar.ics"))
        with open("_site/calendar.ics", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that UIDs follow the pattern YYYY-MM-DD-<period>-<subject>@yearcakes.timetable.school.ics
        uid_pattern = r'UID:(\d{4}-\d{2}-\d{2}-\d+-[a-zA-Z]+@yearcakes\.timetable\.school\.ics)'
        uids = re.findall(uid_pattern, content)
        
        # Should have UIDs in the file
        self.assertGreater(len(uids), 0, "No UIDs found in ICS file")
        
        # Verify all UIDs are unique
        self.assertEqual(len(uids), len(set(uids)), "Found duplicate UIDs")
        
        # Check that all UIDs match the expected pattern
        for uid in uids:
            parts = uid.split('@')
            self.assertEqual(len(parts), 2, f"Invalid UID format: {uid}")
            self.assertEqual(parts[1], "yearcakes.timetable.school.ics", f"Invalid domain in UID: {uid}")
            
            # Check date-period-subject part
            date_period_subject = parts[0]
            date_parts = date_period_subject.split('-')
            self.assertEqual(len(date_parts), 5, f"Invalid date-period-subject format: {date_period_subject}")
            
            # Validate date format (YYYY-MM-DD)
            year, month, day = date_parts[0], date_parts[1], date_parts[2]
            self.assertEqual(len(year), 4, f"Invalid year in UID: {year}")
            self.assertEqual(len(month), 2, f"Invalid month in UID: {month}")
            self.assertEqual(len(day), 2, f"Invalid day in UID: {day}")
            
            # Validate period is numeric
            period = date_parts[3]
            self.assertTrue(period.isdigit(), f"Period should be numeric: {period}")
        
        # Verify no random UIDs (they would contain UUID v4 format in any case)
        # Check catches UUIDs in both uppercase and lowercase hex digit format
        random_uid_pattern = r'UID:[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}'
        random_uids = re.findall(random_uid_pattern, content)
        self.assertEqual(len(random_uids), 0, f"Found {len(random_uids)} random UIDs, should be 0")
    
    def test_ics_floating_time_format(self):
        """Test that ICS file uses floating time (no UTC 'Z' suffix)"""
        # Run the generation script
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        
        # Read the generated ICS file
        self.assertTrue(os.path.exists("_site/calendar.ics"))
        with open("_site/calendar.ics", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that no DTSTART or DTEND lines end with 'Z'
        for line in content.splitlines():
            if line.startswith('DTSTART:') or line.startswith('DTEND:'):
                self.assertFalse(line.strip().endswith('Z'), 
                    f"Found UTC time (ending with Z): {line}")
                # Also verify that times are in the expected format (YYYYMMDDTHHMMSS)
                prefix = 'DTSTART:' if line.startswith('DTSTART:') else 'DTEND:'
                time_value = line.replace(prefix, '').strip()
                # Should be in format like 20250221T080000
                self.assertRegex(time_value, r'^\d{8}T\d{6}$', 
                    f"Invalid floating time format: {time_value}")


class TestIgnorePastDays(unittest.TestCase):
    """Test ignore_past_days functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a backup of the original timetable.json
        if os.path.exists("data/timetable.json"):
            shutil.copy("data/timetable.json", "data/timetable.json.backup")
    
    def tearDown(self):
        """Restore original timetable.json"""
        if os.path.exists("data/timetable.json.backup"):
            shutil.move("data/timetable.json.backup", "data/timetable.json")
        # Clean up test ICS file
        if os.path.exists("_site/calendar.ics"):
            os.remove("_site/calendar.ics")
    
    def test_ignore_past_days_false(self):
        """Test that ignore_past_days=false includes past events"""
        # Create a test timetable config with ignore_past_days=false
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        past_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        future_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        
        test_config = {
            "$version": 2,
            "timetables": [
                {
                    "file": "data/timetables/timetable-G2-S1.json",
                    "start": past_date,
                    "end": future_date,
                    "visible_weeks": 2,
                    "ignore_past_days": False
                }
            ]
        }
        
        # Write test config
        with open("data/timetable.json", "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=2)
        
        # Run the generation script
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        
        # Check that ICS file contains events (may include past dates)
        self.assertTrue(os.path.exists("_site/calendar.ics"))
        with open("_site/calendar.ics", "r", encoding="utf-8") as f:
            content = f.read()
        # Should have at least some events
        self.assertIn("BEGIN:VEVENT", content)
    
    def test_ignore_past_days_true(self):
        """Test that ignore_past_days=true excludes events before today"""
        # Create a test timetable config with ignore_past_days=true
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        past_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        future_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        
        test_config = {
            "$version": 2,
            "timetables": [
                {
                    "file": "data/timetables/timetable-G2-S1.json",
                    "start": past_date,
                    "end": future_date,
                    "visible_weeks": 2,
                    "ignore_past_days": True
                }
            ]
        }
        
        # Write test config
        with open("data/timetable.json", "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=2)
        
        # Run the generation script
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        
        # Check that ICS file exists
        self.assertTrue(os.path.exists("_site/calendar.ics"))
        with open("_site/calendar.ics", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract all event dates from the ICS file
        dtstart_pattern = r'DTSTART:(\d{8})T\d{6}'
        event_dates = re.findall(dtstart_pattern, content)
        
        # Parse today's date
        today_str = today.strftime("%Y%m%d")
        
        # All events should be today or later
        for event_date in event_dates:
            self.assertGreaterEqual(event_date, today_str, 
                f"Found event before today: {event_date} < {today_str}")
    
    def test_ignore_past_days_respects_timezone(self):
        """ignore_past_days should use local date (timezone-aware)"""
        if not hasattr(time, "tzset"):
            self.skipTest("tzset not available on this platform")
        
        original_tz = os.environ.get("TZ")
        test_tz = "Pacific/Kiritimati"  # UTC+14 to simulate being ahead of UTC
        
        try:
            os.environ["TZ"] = test_tz
            time.tzset()
            
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            past_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            future_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
            
            test_config = {
                "$version": 2,
                "timetables": [
                    {
                        "file": "data/timetables/timetable-G2-S1.json",
                        "start": past_date,
                        "end": future_date,
                        "visible_weeks": 2,
                        "ignore_past_days": True
                    }
                ]
            }
            
            with open("data/timetable.json", "w", encoding="utf-8") as f:
                json.dump(test_config, f, indent=2)
            
            env = os.environ.copy()
            env["TZ"] = test_tz
            result = subprocess.run(
                ["python", "scripts/generate_ics.py"],
                capture_output=True,
                text=True,
                env=env
            )
            self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
            
            self.assertTrue(os.path.exists("_site/calendar.ics"))
            with open("_site/calendar.ics", "r", encoding="utf-8") as f:
                content = f.read()
            
            dtstart_pattern = r'DTSTART:(\d{8})T\d{6}'
            event_dates = re.findall(dtstart_pattern, content)
            
            self.assertGreater(len(event_dates), 0, "Expected events to be generated")
            
            today_str = today.strftime("%Y%m%d")
            for event_date in event_dates:
                self.assertGreaterEqual(event_date, today_str, 
                    f"Found event before local today: {event_date} < {today_str}")
        finally:
            if original_tz is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = original_tz
            time.tzset()
    
    def test_ignore_past_days_default(self):
        """Test that ignore_past_days defaults to false when not specified"""
        # Create a test timetable config without ignore_past_days
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        past_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        future_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        
        test_config = {
            "$version": 2,
            "timetables": [
                {
                    "file": "data/timetables/timetable-G2-S1.json",
                    "start": past_date,
                    "end": future_date,
                    "visible_weeks": 2
                    # ignore_past_days not specified, should default to False
                }
            ]
        }
        
        # Write test config
        with open("data/timetable.json", "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=2)
        
        # Run the generation script
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        
        # Should generate ICS file successfully
        self.assertTrue(os.path.exists("_site/calendar.ics"))


class TestFullDayOverride(unittest.TestCase):
    """Test full-day reschedule override using use_weekday"""
    
    def setUp(self):
        if os.path.exists("data/timetable.json"):
            shutil.copy("data/timetable.json", "data/timetable.json.backup")
        if os.path.exists("data/overrides.json"):
            shutil.copy("data/overrides.json", "data/overrides.json.backup")
    
    def tearDown(self):
        if os.path.exists("data/timetable.json.backup"):
            shutil.move("data/timetable.json.backup", "data/timetable.json")
        if os.path.exists("data/overrides.json.backup"):
            shutil.move("data/overrides.json.backup", "data/overrides.json")
        if os.path.exists("_site"):
            shutil.rmtree("_site")
    
    def test_use_weekday_reschedules_entire_day(self):
        """A specific date should be replaced by another weekday's timetable."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # datetime.weekday(): Monday=0 ... Sunday=6
        days_until_sunday = SUNDAY_INDEX - today.weekday()
        if days_until_sunday <= 0:
            days_until_sunday += 7  # ensure the target date is in the future
        target_date_dt = today + timedelta(days=days_until_sunday)
        target_date = target_date_dt.strftime("%Y-%m-%d")
        visible_days = days_until_sunday + 1
        
        test_config = {
            "$version": 2,
            "timetables": [
                {
                    "file": "data/timetables/timetable-G2-S1.json",
                    "start": target_date,
                    "end": target_date,
                    "visible_weeks": 0,
                    "visible_days": visible_days,
                    "ignore_past_days": False
                }
            ]
        }
        
        with open("data/timetable.json", "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=2, ensure_ascii=False)
        
        reschedule_weekday = MONDAY_WEEKDAY
        overrides_data = {
            "$version": 1,
            target_date: {"use_weekday": reschedule_weekday}
        }
        with open("data/overrides.json", "w", encoding="utf-8") as f:
            json.dump(overrides_data, f, indent=2, ensure_ascii=False)
        
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        
        self.assertTrue(os.path.exists("_site/calendar.ics"))
        with open("_site/calendar.ics", "r", encoding="utf-8") as f:
            content = f.read()
        
        target_date_compact = target_date_dt.strftime("%Y%m%d")
        dtstart_pattern = rf'DTSTART:{target_date_compact}T\d{{6}}'
        events_for_target = re.findall(dtstart_pattern, content)
        
        with open("data/timetables/timetable-G2-S1.json", "r", encoding="utf-8") as timetable_file:
            timetable_data = json.load(timetable_file)
        expected_count = len([item for item in timetable_data["timetable"] if item["weekday"] == reschedule_weekday])
        self.assertEqual(
            len(events_for_target),
            expected_count,
            f"Rescheduled day should contain weekday {reschedule_weekday} timetable entries",
        )

    def test_use_weekday_out_of_bounds(self):
        """use_weekday outside 1-7 should emit warning and skip"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        target_date = (today + timedelta(days=2)).strftime("%Y-%m-%d")
        test_config = {
            "$version": 2,
            "timetables": [
                {
                    "file": "data/timetables/timetable-G2-S1.json",
                    "start": target_date,
                    "end": target_date,
                    "visible_weeks": 1,
                    "visible_days": 2,
                    "ignore_past_days": False
                }
            ]
        }
        with open("data/timetable.json", "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=2, ensure_ascii=False)
        overrides_data = {
            "$version": 1,
            target_date: {"use_weekday": 0}
        }
        with open("data/overrides.json", "w", encoding="utf-8") as f:
            json.dump(overrides_data, f, indent=2, ensure_ascii=False)
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        self.assertIn("use_weekday must be between", result.stdout + result.stderr)

    def test_use_weekday_invalid_type(self):
        """Non-numeric use_weekday should emit warning and skip"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        target_date = (today + timedelta(days=2)).strftime("%Y-%m-%d")
        test_config = {
            "$version": 2,
            "timetables": [
                {
                    "file": "data/timetables/timetable-G2-S1.json",
                    "start": target_date,
                    "end": target_date,
                    "visible_weeks": 1,
                    "visible_days": 2,
                    "ignore_past_days": False
                }
            ]
        }
        with open("data/timetable.json", "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=2, ensure_ascii=False)
        overrides_data = {
            "$version": 1,
            target_date: {"use_weekday": "invalid"}
        }
        with open("data/overrides.json", "w", encoding="utf-8") as f:
            json.dump(overrides_data, f, indent=2, ensure_ascii=False)
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        self.assertIn("Invalid use_weekday value", result.stdout + result.stderr)

    def test_use_weekday_numeric_string(self):
        """Numeric string use_weekday should be accepted"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        target_date = (today + timedelta(days=2)).strftime("%Y-%m-%d")
        test_config = {
            "$version": 2,
            "timetables": [
                {
                    "file": "data/timetables/timetable-G2-S1.json",
                    "start": target_date,
                    "end": target_date,
                    "visible_weeks": 1,
                    "visible_days": 2,
                    "ignore_past_days": False
                }
            ]
        }
        with open("data/timetable.json", "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=2, ensure_ascii=False)
        overrides_data = {
            "$version": 1,
            target_date: {"use_weekday": "1"}
        }
        with open("data/overrides.json", "w", encoding="utf-8") as f:
            json.dump(overrides_data, f, indent=2, ensure_ascii=False)
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        self.assertIn("BEGIN:VEVENT", Path("_site/calendar.ics").read_text(encoding="utf-8"))

    def test_use_weekday_no_entries_warning(self):
        """Warn when reschedule weekday has no timetable entries"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        target_date = (today + timedelta(days=2)).strftime("%Y-%m-%d")
        test_config = {
            "$version": 2,
            "timetables": [
                {
                    "file": "data/timetables/timetable-G2-S1.json",
                    "start": target_date,
                    "end": target_date,
                    "visible_weeks": 1,
                    "visible_days": 2,
                    "ignore_past_days": False
                }
            ]
        }
        with open("data/timetable.json", "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=2, ensure_ascii=False)
        overrides_data = {
            "$version": 1,
            target_date: {"use_weekday": 7}  # timetable has no Sunday entries
        }
        with open("data/overrides.json", "w", encoding="utf-8") as f:
            json.dump(overrides_data, f, indent=2, ensure_ascii=False)
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        self.assertIn("No timetable entries found for weekday", result.stdout + result.stderr)


class TestVisibleDays(unittest.TestCase):
    """Test visible_days functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a backup of the original timetable.json
        if os.path.exists("data/timetable.json"):
            shutil.copy("data/timetable.json", "data/timetable.json.backup")
    
    def tearDown(self):
        """Restore original timetable.json"""
        if os.path.exists("data/timetable.json.backup"):
            shutil.move("data/timetable.json.backup", "data/timetable.json")
        # Clean up test ICS file
        if os.path.exists("_site/calendar.ics"):
            os.remove("_site/calendar.ics")
    
    def test_visible_days_default(self):
        """Test that visible_days defaults to 0 when not specified"""
        # Create a test timetable config without visible_days
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        past_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        future_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
        
        test_config = {
            "$version": 2,
            "timetables": [
                {
                    "file": "data/timetables/timetable-G2-S1.json",
                    "start": past_date,
                    "end": future_date,
                    "visible_weeks": 1
                    # visible_days not specified, should default to 0
                }
            ]
        }
        
        # Write test config
        with open("data/timetable.json", "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=2)
        
        # Run the generation script
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        
        # Should generate ICS file successfully
        self.assertTrue(os.path.exists("_site/calendar.ics"))
    
    def test_visible_days_with_value(self):
        """Test that visible_days works with a specific value"""
        # Create a test timetable config with visible_days=1
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        past_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        future_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
        # Ensure we include at least one weekday even when tests run on weekends
        visible_days_value = 1 if today.isoweekday() <= 5 else 14
        
        test_config = {
            "$version": 2,
            "timetables": [
                {
                    "file": "data/timetables/timetable-G2-S1.json",
                    "start": past_date,
                    "end": future_date,
                    "visible_weeks": 1,
                    "visible_days": visible_days_value,
                    "ignore_past_days": False
                }
            ]
        }
        
        # Write test config
        with open("data/timetable.json", "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=2)
        
        # Run the generation script
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        
        # Check that ICS file exists
        self.assertTrue(os.path.exists("_site/calendar.ics"))
        with open("_site/calendar.ics", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Should have events in the file
        self.assertIn("BEGIN:VEVENT", content)
    
    def test_visible_days_or_logic(self):
        """Test that visible_days and visible_weeks use OR logic"""
        # Create a test where visible_days extends beyond visible_weeks
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        past_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        
        test_config = {
            "$version": 2,
            "timetables": [
                {
                    "file": "data/timetables/timetable-G2-S1.json",
                    "start": past_date,
                    "end": future_date,
                    "visible_weeks": 1,  # Only current week
                    "visible_days": 10,  # But 10 days from today
                    "ignore_past_days": True
                }
            ]
        }
        
        # Write test config
        with open("data/timetable.json", "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=2)
        
        # Run the generation script
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        
        # Check that ICS file exists
        self.assertTrue(os.path.exists("_site/calendar.ics"))
        with open("_site/calendar.ics", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract all event dates from the ICS file
        dtstart_pattern = r'DTSTART:(\d{8})T\d{6}'
        event_dates = re.findall(dtstart_pattern, content)
        
        # Calculate expected date range
        # With OR logic, should include either visible_weeks OR visible_days range
        # visible_days=10 means today + (visible_days - 1) more days = today + 9 more days
        visible_days = 10
        max_date = (today + timedelta(days=visible_days - 1)).strftime("%Y%m%d")
        today_str = today.strftime("%Y%m%d")
        
        # All events should be within the range
        for event_date in event_dates:
            self.assertGreaterEqual(event_date, today_str, 
                f"Found event before today: {event_date} < {today_str}")
            self.assertLessEqual(event_date, max_date, 
                f"Found event beyond expected range: {event_date} > {max_date}")
    
    def test_visible_params_disabled_when_zero(self):
        """Test that setting both visible_weeks and visible_days to 0 skips the timetable"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        future_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
        
        test_config = {
            "$version": 2,
            "timetables": [
                {
                    "file": "data/timetables/timetable-G2-S1.json",
                    "start": today.strftime("%Y-%m-%d"),
                    "end": future_date,
                    "visible_weeks": 0,
                    "visible_days": 0
                }
            ]
        }
        
        with open("data/timetable.json", "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=2)
        
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        
        self.assertTrue(os.path.exists("_site/calendar.ics"))
        with open("_site/calendar.ics", "r", encoding="utf-8") as f:
            content = f.read()
        
        self.assertNotIn("BEGIN:VEVENT", content, "Timetable should be skipped when both visibility options are disabled")
    
    def test_visible_weeks_disabled_days_applied(self):
        """Test that visible_days still works when visible_weeks is disabled"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        past_date = (today - timedelta(days=3)).strftime("%Y-%m-%d")
        future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        
        visible_days = 7
        
        test_config = {
            "$version": 2,
            "timetables": [
                {
                    "file": "data/timetables/timetable-G2-S1.json",
                    "start": past_date,
                    "end": future_date,
                    "visible_weeks": 0,
                    "visible_days": visible_days
                }
            ]
        }
        
        with open("data/timetable.json", "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=2)
        
        result = subprocess.run(
            ["python", "scripts/generate_ics.py"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        
        self.assertTrue(os.path.exists("_site/calendar.ics"))
        with open("_site/calendar.ics", "r", encoding="utf-8") as f:
            content = f.read()
        
        dtstart_pattern = r'DTSTART:(\d{8})T\d{6}'
        event_dates = re.findall(dtstart_pattern, content)
        
        today_str = today.strftime("%Y%m%d")
        max_date = (today + timedelta(days=visible_days - 1)).strftime("%Y%m%d")
        
        self.assertGreater(len(event_dates), 0, "Expected events when visible_days is enabled")
        
        for event_date in event_dates:
            self.assertGreaterEqual(event_date, today_str, 
                f"Found event before today: {event_date} < {today_str}")
            self.assertLessEqual(event_date, max_date, 
                f"Found event beyond visible_days range: {event_date} > {max_date}")


if __name__ == "__main__":
    # Change to repository root directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    unittest.main()
