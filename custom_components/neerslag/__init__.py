"""The Neerslag Sensor (Buienalarm / Buienradar) integration."""
import asyncio
from .load_frontend import setup_view
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS = ["sensor"]
FRONTEND_SETUP_KEY = "frontend_setup_done"

_LOGGER = logging.getLogger(__name__)


async def options_update_listener(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> None:
    """Handle options update.

    Wordt aangeroepen als de OptionsFlow een wijziging opslaat.
    Kopieert hier de options naar data, 
    """
    _LOGGER.info(
        "Neerslag: options_update_listener triggered for entry %s",
        config_entry.entry_id,
    )

    # LET OP: dit gedrag is bewust zo gelaten; spiegel options terug naar data.
    hass.config_entries.async_update_entry(
        config_entry,
        data=config_entry.options,
    )

async def _ensure_frontend_setup(hass: HomeAssistant):
    """Run setup_view exactly once."""
    hass.data.setdefault(DOMAIN, {})

    if not hass.data[DOMAIN].get(FRONTEND_SETUP_KEY):
        await setup_view(hass)
        hass.data[DOMAIN][FRONTEND_SETUP_KEY] = True

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Neerslag Sensor (Buienalarm / Buienradar) component. (YAML path)"""
    await _ensure_frontend_setup(hass)
    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up from a config entry (UI path)."""

    await _ensure_frontend_setup(hass)

    hass_data = dict(config_entry.data)
    unsub = config_entry.add_update_listener(options_update_listener)
    hass_data["unsub_options_update_listener"] = unsub

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = hass_data

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    # Remove options_update_listener.

    _LOGGER.info(
        "Neerslag: unloading config entry %s",
        config_entry.entry_id,
    )
    
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    # Options-listener verwijderen
    entry_data = hass.data[DOMAIN].get(config_entry.entry_id)
    if entry_data and "unsub_options_update_listener" in entry_data:
        try:
            entry_data["unsub_options_update_listener"]()
        except Exception:  # defensief
            _LOGGER.exception(
                "Neerslag: error while unsubscribing options listener for %s",
                config_entry.entry_id,
            )

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok
