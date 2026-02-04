"""Sensor platform for HA AA integration."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import AlarmCoordinator

# Only one sensor per config entry, so no parallel updates needed
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensor platform from config entry."""
    coordinator: AlarmCoordinator = config_entry.runtime_data

    entities = [
        NextAlarmSensor(coordinator, config_entry),
    ]
    async_add_entities(entities)


class NextAlarmSensor(CoordinatorEntity[AlarmCoordinator], SensorEntity):
    """Sensor for the next upcoming alarm."""

    _attr_has_entity_name = True
    _attr_translation_key = "next_alarm"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:alarm"

    def __init__(
        self, coordinator: AlarmCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_next_alarm"

    @property
    def native_value(self) -> datetime | None:
        """Return the value of the sensor."""
        if self.coordinator.data:
            next_alarm_str = self.coordinator.data.get("next_alarm")
            if next_alarm_str:
                return datetime.fromisoformat(next_alarm_str)
        return None

    @property
    def extra_state_attributes(self) -> Mapping[str, int | str | None]:
        """Return additional state attributes."""
        if self.coordinator.data:
            return {
                "next_alarm_name": self.coordinator.data.get("next_alarm_name"),
                "total_alarms": len(self.coordinator.data.get("all_alarms", [])),
            }
        return {}
