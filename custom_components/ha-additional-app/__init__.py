"""The HA AA integration."""

from __future__ import annotations

from datetime import datetime
import logging

from aiohttp import web
from aiohttp.web import Request

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

from .const import CONF_WEBHOOK_ID, DOMAIN
from .coordinator import AlarmCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

# Refresh next alarm computation every 15 minutes
REFRESH_INTERVAL = 60 * 15

type LRHAAAConfigEntry = ConfigEntry[AlarmCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: LRHAAAConfigEntry) -> bool:
    """Set up HA AA from a config entry."""
    _LOGGER.debug("Setting up HA AA with entry ID: %s", entry.entry_id)

    try:
        coordinator = AlarmCoordinator(hass, entry)
        entry.runtime_data = coordinator
        _LOGGER.debug("AlarmCoordinator created and set as runtime_data")
    except Exception:
        _LOGGER.exception("Error creating AlarmCoordinator")
        return False

    # Register webhook for Android app to send alarm data
    webhook_id = entry.data.get(CONF_WEBHOOK_ID, entry.entry_id)
    _LOGGER.info("🔗 Webhook ID: %s", webhook_id)

    async def handle_webhook(
        hass: HomeAssistant, webhook_id: str, request: Request
    ) -> web.Response:
        """Handle webhook from Android app."""
        _LOGGER.info("🔔 Webhook called with ID: %s", webhook_id)
        try:
            data = await request.json()
            _LOGGER.debug(
                "Webhook received JSON data with keys: %s", list(data.keys()))

            if "alarms" in data and isinstance(data["alarms"], list):
                timezone = data.get("timezone")
                _LOGGER.info(
                    "Processing %d alarms with timezone: %s",
                    len(data["alarms"]),
                    timezone,
                )
                coordinator.update_alarms(data["alarms"], timezone=timezone)
                _LOGGER.info("✓ Updated alarms from Android app: %d alarms",
                             len(data["alarms"]))
                return web.Response(text="OK", status=200)

            _LOGGER.warning(
                "Webhook data missing 'alarms' key or not a list")
            return web.Response(text="Missing alarms data", status=400)

        except ValueError as err:
            _LOGGER.error("Invalid JSON in webhook: %s", err)
            return web.Response(text="Invalid JSON", status=400)
        except Exception as err:
            _LOGGER.error("Unexpected error in webhook handler: %s", err)
            return web.Response(text="Internal server error", status=500)

    try:
        webhook.async_register(
            hass,
            DOMAIN,
            "Alarm Update",
            webhook_id,
            handle_webhook,
            allowed_methods=["POST"],
        )
        _LOGGER.info("✓ Webhook registered at: /api/webhook/%s", webhook_id)
    except Exception:
        _LOGGER.exception("Error registering webhook")
        return False

    # Set up periodic refresh for next alarm computation
    refresh_handle_storage: dict = {"handle": None}
    
    async def refresh_alarm(now: datetime | None = None) -> None:
        """Refresh next alarm computation."""
        _LOGGER.debug("Refreshing next alarm computation")
        try:
            coordinator.refresh_next_alarm()
        except Exception:
            _LOGGER.exception("Error refreshing next alarm")
        # Reschedule the next refresh
        refresh_handle_storage["handle"] = async_call_later(
            hass, REFRESH_INTERVAL, refresh_alarm
        )

    # Schedule the first refresh
    refresh_handle_storage["handle"] = async_call_later(
        hass, REFRESH_INTERVAL, refresh_alarm
    )

    def unregister_refresh() -> None:
        """Unregister the refresh callback."""
        _LOGGER.debug("Unregistering refresh callback")
        if refresh_handle_storage["handle"]:
            refresh_handle_storage["handle"]()

    entry.async_on_unload(unregister_refresh)

    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.debug("HA AA setup completed successfully")
    except Exception:
        _LOGGER.exception("Error setting up platforms")
        return False

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Webhook is automatically unregistered on unload
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
