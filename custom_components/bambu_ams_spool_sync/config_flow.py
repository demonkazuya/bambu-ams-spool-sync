"""Config flow for Bambu AMS Spool Sync."""

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_SPOOLMAN_URL,
    DOMAIN,
)


class BambuAmsSpoolSyncConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle a Bambu AMS Spool Sync config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Handle the user setup step."""

        if user_input is not None:
            return self.async_create_entry(
                title="Bambu AMS Spool Sync",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SPOOLMAN_URL,
                ): cv.url,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )
