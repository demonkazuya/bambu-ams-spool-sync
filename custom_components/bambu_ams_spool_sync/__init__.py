"""Bambu AMS Spool Sync integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Bambu AMS Spool Sync integration."""
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Bambu AMS Spool Sync from a config entry."""

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a Bambu AMS Spool Sync config entry."""

    runtime = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if runtime and runtime.get("unsub"):
        runtime["unsub"]()

    return await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )
