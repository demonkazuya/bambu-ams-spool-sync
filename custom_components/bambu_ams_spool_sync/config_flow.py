"""Config flow for Bambu AMS Spool Sync."""

from __future__ import annotations

import json
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_SPOOLMAN_URL,
    DOMAIN,
)

SPOOLMAN_TIMEOUT = aiohttp.ClientTimeout(total=10)


def _build_schema() -> vol.Schema:
    """Return the user step schema."""

    return vol.Schema(
        {
            vol.Required(
                CONF_SPOOLMAN_URL,
            ): cv.url,
        }
    )


async def _async_validate_spoolman(
    flow: config_entries.ConfigFlow,
    spoolman_url: str,
) -> str | None:
    """Return an error key when Spoolman cannot be reached, otherwise None."""

    url = f"{spoolman_url.rstrip('/')}/api/v1/health"

    try:
        session = async_get_clientsession(flow.hass)
        async with session.get(url, timeout=SPOOLMAN_TIMEOUT) as response:
            body = await response.text()
            status = response.status
    except TimeoutError:
        # aiohttp.ServerTimeoutError derives from both ClientError and
        # TimeoutError, so this has to be checked before ClientError.
        return "timeout"
    except aiohttp.ClientError:
        return "cannot_connect"

    if status != 200:
        return "invalid_response"

    # A wrong path can still answer with a HTML page, so make sure the
    # response really is the Spoolman API and not another web interface.
    try:
        payload = json.loads(body)
    except ValueError:
        return "invalid_response"

    if not isinstance(payload, dict) or payload.get("status") != "healthy":
        return "invalid_response"

    return None


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

        errors: dict[str, str] = {}

        if user_input is not None:
            spoolman_url = user_input[CONF_SPOOLMAN_URL].rstrip("/")

            await self.async_set_unique_id(spoolman_url)
            self._abort_if_unique_id_configured()

            error = await _async_validate_spoolman(self, spoolman_url)
            if error:
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title="Bambu AMS Spool Sync",
                    data={CONF_SPOOLMAN_URL: spoolman_url},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(),
            errors=errors,
        )
