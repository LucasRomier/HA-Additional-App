"""Data update coordinator for HA AA integration."""

from __future__ import annotations

from datetime import datetime, time, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util.dt import get_time_zone

_LOGGER = logging.getLogger(__name__)

type AlarmData = dict[str, Any]


class AlarmCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate alarm data from Android app."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="HA AA Alarms",
            config_entry=config_entry,
        )
        self.alarms: list[AlarmData] = []
        self.device_timezone_name: str | None = None

        # Initialize with empty alarm state
        self.data = self._compute_next_alarm()

    def update_alarms(
        self, alarms: list[AlarmData], timezone: str | None = None
    ) -> None:
        """Update alarms from Android app."""
        if timezone:
            self.device_timezone_name = timezone
        self.alarms = alarms
        self.async_set_updated_data(self._compute_next_alarm())

    def refresh_next_alarm(self) -> None:
        """Refresh the next alarm computation (useful for periodic updates)."""
        self.async_set_updated_data(self._compute_next_alarm())

    def _compute_next_alarm(self) -> dict[str, Any]:
        """Compute the next upcoming alarm."""
        if not self.alarms:
            return {"next_alarm": None, "all_alarms": []}

        # Get the device timezone or use HA's local timezone
        tz = None
        if self.device_timezone_name:
            tz = get_time_zone(self.device_timezone_name)

        now = datetime.now(tz=tz)
        current_weekday = now.weekday()  # 0=Monday, 6=Sunday
        current_time = now.time()

        next_alarm: AlarmData | None = None
        next_alarm_datetime: datetime | None = None

        for alarm in self.alarms:
            if not alarm.get("isEnabled", True):
                continue

            alarm_time = self._parse_time(alarm["time"])
            if alarm_time is None:
                continue

            days = alarm.get("days", [])
            if not days:
                # No specific days means every day
                days = list(range(7))

            for day in days:
                # day: 0=Monday, 6=Sunday (matching Python's weekday)
                # Check if this day is today and time hasn't passed
                if day == current_weekday and alarm_time > current_time:
                    alarm_dt = datetime.combine(
                        now.date(), alarm_time, tzinfo=now.tzinfo
                    )
                    if next_alarm_datetime is None or alarm_dt < next_alarm_datetime:
                        next_alarm = alarm
                        next_alarm_datetime = alarm_dt
                # Check future days
                elif day > current_weekday:
                    days_until = day - current_weekday
                    alarm_dt = datetime.combine(
                        now.date() + timedelta(days=days_until),
                        alarm_time,
                        tzinfo=now.tzinfo,
                    )
                    if next_alarm_datetime is None or alarm_dt < next_alarm_datetime:
                        next_alarm = alarm
                        next_alarm_datetime = alarm_dt
                # Wrap around week for past days
                elif day < current_weekday:
                    days_until = 7 - current_weekday + day
                    alarm_dt = datetime.combine(
                        now.date() + timedelta(days=days_until),
                        alarm_time,
                        tzinfo=now.tzinfo,
                    )
                    if next_alarm_datetime is None or alarm_dt < next_alarm_datetime:
                        next_alarm = alarm
                        next_alarm_datetime = alarm_dt

        return {
            "next_alarm": next_alarm_datetime.isoformat()
            if next_alarm_datetime
            else None,
            "next_alarm_name": next_alarm.get("name", "Unknown")
            if next_alarm
            else None,
            "all_alarms": self.alarms,
        }

    @staticmethod
    def _parse_time(time_str: str) -> time | None:
        """Parse time string in HH:MM format."""
        try:
            parts = time_str.split(":")
            if len(parts) == 2:
                return time(int(parts[0]), int(parts[1]))
        except (ValueError, AttributeError):
            pass
        return None
