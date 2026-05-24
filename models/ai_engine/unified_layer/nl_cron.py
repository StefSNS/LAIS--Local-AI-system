"""
Natural Language Cron Parser - Converts natural language to cron expressions.
Based on Hermes Agent's cron scheduling system.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum


class Frequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    HOURLY = "hourly"
    MINUTELY = "minutely"
    ONCE = "once"


DAY_MAP = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}

MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}


class NLCronParser:
    """
    Converts natural language scheduling to cron expressions.
    Examples:
        - "every day at 9am" -> "0 9 * * *"
        - "every monday at 3pm" -> "0 15 * * 1"
        - "every hour" -> "0 * * * *"
        - "every 30 minutes" -> "*/30 * * * *"
        - "weekly on friday evening" -> "0 18 * * 5"
    """

    def __init__(self):
        self.patterns = [
            self._parse_every_n_minutes,
            self._parse_every_n_hours,
            self._parse_every_day,
            self._parse_every_weekday,
            self._parse_every_month,
            self._parse_once_at,
            self._parse_nl_expression,
        ]

    def parse(self, nl_text: str) -> Dict[str, Any]:
        """
        Parse natural language into schedule details.

        Returns:
            Dict with: cron, frequency, next_run, description
        """
        nl = nl_text.lower().strip()

        for parser in self.patterns:
            result = parser(nl)
            if result:
                return result

        return {"success": False, "error": f"Could not parse: {nl_text}"}

    def _parse_every_n_minutes(self, nl: str) -> Optional[Dict[str, Any]]:
        """Parse 'every N minutes'."""
        match = re.search(r"every (\d+) minute", nl)
        if match:
            minutes = int(match.group(1))
            if minutes < 1 or minutes > 59:
                return None
            cron = f"*/{minutes} * * * *"
            return {
                "success": True,
                "cron": cron,
                "frequency": "minutely",
                "interval_minutes": minutes,
                "description": f"Every {minutes} minutes",
                "next_run": self._calc_next_run(cron),
            }
        return None

    def _parse_every_n_hours(self, nl: str) -> Optional[Dict[str, Any]]:
        """Parse 'every N hours'."""
        match = re.search(r"every (\d+) hour", nl)
        if match:
            hours = int(match.group(1))
            if hours < 1 or hours > 23:
                return None
            cron = f"0 */{hours} * * *"
            return {
                "success": True,
                "cron": cron,
                "frequency": "hourly",
                "interval_hours": hours,
                "description": f"Every {hours} hours",
                "next_run": self._calc_next_run(cron),
            }
        return None

    def _parse_every_day(self, nl: str) -> Optional[Dict[str, Any]]:
        """Parse 'every day at X' or 'daily at X'."""
        patterns = [
            (r"every day at (\d{1,2})(?::(\d{2}))?\s*(am|pm)?", True),
            (r"daily at (\d{1,2})(?::(\d{2}))?\s*(am|pm)?", True),
            (r"every morning at (\d{1,2})(?::(\d{2}))?", False),
            (r"every evening at (\d{1,2})(?::(\d{2}))?", False),
            (r"every night at (\d{1,2})(?::(\d{2}))?", False),
        ]

        for pattern, _ in patterns:
            match = re.search(pattern, nl)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                period = match.group(3) if len(match.groups()) > 2 else None

                if period == "pm" and hour != 12:
                    hour += 12
                elif period == "am" and hour == 12:
                    hour = 0

                if "morning" in nl and hour < 12:
                    hour = max(hour, 6)
                if ("evening" in nl or "night" in nl) and hour < 12:
                    hour = max(hour, 18)

                cron = f"{minute} {hour} * * *"
                time_str = f"{hour:02d}:{minute:02d}"
                return {
                    "success": True,
                    "cron": cron,
                    "frequency": "daily",
                    "time": time_str,
                    "description": f"Daily at {time_str}",
                    "next_run": self._calc_next_run(cron),
                }
        return None

    def _parse_every_weekday(self, nl: str) -> Optional[Dict[str, Any]]:
        """Parse 'every Monday at X' or 'weekly on X'."""
        for day_name, day_num in DAY_MAP.items():
            if day_name in nl:
                time_match = re.search(r"at (\d{1,2})(?::(\d{2}))?\s*(am|pm)?", nl)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    period = time_match.group(3)

                    if period == "pm" and hour != 12:
                        hour += 12
                    elif period == "am" and hour == 12:
                        hour = 0

                    cron = f"{minute} {hour} * * {day_num}"
                else:
                    hour_match = re.search(r"(morning|afternoon|evening)", nl)
                    if hour_match:
                        if hour_match.group(1) == "morning":
                            hour, minute = 9, 0
                        elif hour_match.group(1) == "afternoon":
                            hour, minute = 15, 0
                        else:
                            hour, minute = 18, 0
                    else:
                        hour, minute = 9, 0

                    cron = f"{minute} {hour} * * {day_num}"

                day_display = day_name.capitalize()
                return {
                    "success": True,
                    "cron": cron,
                    "frequency": "weekly",
                    "day": day_display,
                    "time": f"{hour:02d}:{minute:02d}",
                    "description": f"Every {day_display} at {hour:02d}:{minute:02d}",
                    "next_run": self._calc_next_run(cron),
                }
        return None

    def _parse_every_month(self, nl: str) -> Optional[Dict[str, Any]]:
        """Parse 'every month on the Nth' or 'monthly on Nth'."""
        match = re.search(r"(?:every month|monthly) on (?:the )?(\d{1,2})(?:st|nd|rd|th)?", nl)
        if match:
            day = int(match.group(1))
            if day > 28:
                day = 28

            time_match = re.search(r"at (\d{1,2})(?::(\d{2}))?", nl)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
            else:
                hour, minute = 9, 0

            cron = f"{minute} {hour} {day} * *"
            return {
                "success": True,
                "cron": cron,
                "frequency": "monthly",
                "day": day,
                "time": f"{hour:02d}:{minute:02d}",
                "description": f"Monthly on day {day} at {hour:02d}:{minute:02d}",
                "next_run": self._calc_next_run(cron),
            }
        return None

    def _parse_once_at(self, nl: str) -> Optional[Dict[str, Any]]:
        """Parse 'once at X' or 'at X'."""
        match = re.search(r"(?:once |at )?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", nl)
        if match and ("once" in nl or "at " in nl[:6]):
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            period = match.group(3)

            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0

            now = datetime.now()
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)

            return {
                "success": True,
                "cron": f"{minute} {hour} * * *",
                "frequency": "once",
                "time": f"{hour:02d}:{minute:02d}",
                "description": f"Once at {hour:02d}:{minute:02d}",
                "next_run": next_run.isoformat(),
            }
        return None

    def _parse_nl_expression(self, nl: str) -> Optional[Dict[str, Any]]:
        """Parse common natural language patterns."""
        patterns = {
            "every hour": "0 * * * *",
            "hourly": "0 * * * *",
            "every minute": "* * * * *",
            "minutely": "* * * * *",
            "every day": "0 9 * * *",
            "daily": "0 9 * * *",
            "every weekday": "0 9 * * 1-5",
            "weekdays": "0 9 * * 1-5",
            "every weekend": "0 10 * * 0,6",
            "weekends": "0 10 * * 0,6",
        }

        for pattern, cron in patterns.items():
            if pattern in nl:
                time_match = re.search(r"at (\d{1,2})(?::(\d{2}))?", nl)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    cron = f"{minute} {hour} " + " ".join(cron.split()[2:])

                return {
                    "success": True,
                    "cron": cron,
                    "frequency": "custom",
                    "description": f"Matched pattern: {pattern}",
                    "next_run": self._calc_next_run(cron),
                }
        return None

    def _calc_next_run(self, cron: str) -> str:
        """Calculate next run time from cron expression."""
        parts = cron.split()
        if len(parts) != 5:
            return datetime.now().isoformat()

        minute, hour, day, month, dow = parts
        now = datetime.now()
        next_run = now

        try:
            if minute.startswith("*/"):
                interval = int(minute[2:])
                next_run = now.replace(second=0, microsecond=0)
                mins_since_hour = next_run.minute % interval
                if mins_since_hour != 0:
                    next_run += timedelta(minutes=interval - mins_since_hour)
            elif minute != "*":
                next_run = next_run.replace(minute=int(minute), second=0, microsecond=0)

            if hour != "*":
                next_run = next_run.replace(hour=int(hour))

            if next_run <= now:
                next_run += timedelta(days=1)

            return next_run.isoformat()
        except Exception:
            return now.isoformat()

    def to_cron(self, nl_text: str) -> str:
        """Convert natural language to cron expression."""
        result = self.parse(nl_text)
        if result.get("success"):
            return result["cron"]
        return ""


_nl_cron_instance: Optional[NLCronParser] = None


def get_nl_cron_parser() -> NLCronParser:
    """Get or create the NL cron parser instance."""
    global _nl_cron_instance
    if _nl_cron_instance is None:
        _nl_cron_instance = NLCronParser()
    return _nl_cron_instance


if __name__ == "__main__":
    parser = get_nl_cron_parser()

    test_cases = [
        "every 30 minutes",
        "every 2 hours",
        "every day at 9am",
        "every monday at 3pm",
        "every friday evening",
        "weekly on Wednesday at 10am",
        "every month on the 1st",
        "monthly on 15th at 6pm",
        "every hour",
        "daily at 6pm",
    ]

    print("=== Natural Language Cron Parser ===")
    for test in test_cases:
        result = parser.parse(test)
        print(f"\nInput: {test}")
        print(f"  Cron: {result.get('cron', 'ERROR')}")
        print(f"  Next: {result.get('next_run', '')}")