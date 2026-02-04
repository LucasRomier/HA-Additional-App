"""Config flow for the HA AA integration."""

from __future__ import annotations

import base64
from io import BytesIO
import logging
from typing import Any
import uuid

import qrcode
import voluptuous as vol

from homeassistant.components.webhook import async_generate_url
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_URL
from homeassistant.helpers import selector

from .const import (
    CONF_URL_TYPE,
    CONF_WEBHOOK_ID,
    DOMAIN,
    URL_TYPE_LOCAL,
    URL_TYPE_PUBLIC,
)

__all__ = ["LRHAAAConfigFlow"]

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL_TYPE): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(
                        value=URL_TYPE_LOCAL,
                        label="Local URL",
                    ),
                    selector.SelectOptionDict(
                        value=URL_TYPE_PUBLIC,
                        label="Public URL",
                    ),
                ],
            ),
        ),
    }
)


class LRHAAAConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA AA."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured (single instance)
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            # Validate and generate webhook
            try:
                url_type = user_input[CONF_URL_TYPE]
                webhook_id = str(uuid.uuid4())

                if url_type == URL_TYPE_LOCAL:
                    webhook_url = async_generate_url(
                        self.hass, webhook_id, allow_internal=True
                    )
                else:
                    webhook_url = async_generate_url(
                        self.hass, webhook_id, allow_internal=False
                    )

                # Generate QR code
                qr_code_data_uri = self._generate_qr_code(webhook_url)
                qr_code_markdown = f'![QR Code]({qr_code_data_uri} "QR Code")'

                # Store data for next step
                self.data = {
                    CONF_URL: webhook_url,
                    CONF_WEBHOOK_ID: webhook_id,
                    "qr_code": qr_code_markdown,
                }

                return await self.async_step_confirm()

            except Exception as err:
                _LOGGER.exception("Error in user step: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Display webhook URL and QR code for confirmation."""
        if user_input is not None:
            # User confirmed, create entry
            return self.async_create_entry(
                title="HA AA Alarms",
                data={
                    CONF_URL: self.data[CONF_URL],
                    CONF_WEBHOOK_ID: self.data[CONF_WEBHOOK_ID],
                },
            )

        return self.async_show_form(
            step_id="confirm",
            description_placeholders={
                "qr_code": self.data["qr_code"],
                "webhook_url": self.data[CONF_URL],
            },
        )

    @staticmethod
    def _generate_qr_code(data: str) -> str:
        """Generate a QR code and return as base64 data URI."""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            return f"data:image/png;base64,{img_str}"
        except Exception as err:
            _LOGGER.exception("Error generating QR code: %s", err)
            raise
