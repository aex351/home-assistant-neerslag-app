from homeassistant.block_async_io import enable
from homeassistant.helpers.entity_platform import EntityPlatform
import logging
from os import truncate
import aiohttp

from random import random
import random as rand

import json
from homeassistant.helpers.entity import Entity
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME, CONF_SOURCE
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import EntityPlatform, async_get_platforms


from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_entries_for_device,
)


_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=180)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Set up sensor entity."""

    dev_reg = await hass.helpers.device_registry.async_get_registry()
    ent_reg = await hass.helpers.entity_registry.async_get_registry()

    if config_entry.data.get("buienalarm") == True:
        async_add_entities([NeerslagSensorBuienalarm(hass, config_entry, True)], update_before_add=True)

    if config_entry.data.get("buienalarm") == False:
        async_add_entities([NeerslagSensorBuienalarm(hass, config_entry, False)], update_before_add=False)

    if config_entry.data.get("buienradar") == True:
        async_add_entities([NeerslagSensorBuienradar(hass, config_entry, True)], update_before_add=True)

    if config_entry.data.get("buienradar") == False:
        async_add_entities([NeerslagSensorBuienradar(hass, config_entry, False)], update_before_add=False)


class mijnBasis(Entity):
    _enabled = None
    _unique_id = None
    _name = None

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, enabled: bool):
        _LOGGER.info("--<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>--->>>>>>>>>>>>>>>>>>>>>>>>")

    async def mine_update_listener(self, hass: HomeAssistant, config_entry: ConfigEntry, pp=None):
        """Handle options update."""

        if(self._name == "neerslag_buienalarm_regen_data"):
            self._enabled = config_entry.data.get("buienalarm")

        if(self._name == "neerslag_buienradar_regen_data"):
            self._enabled = config_entry.data.get("buienradar")

    @property
    def device_info(self):
        return {
            "identifiers": {
                ("neerslag", "neerslag-device")
            },
            "name": "Neerslag App",
            "manufacturer": "aex351",
            "model": "All-in-one package",
            "sw_version": "",
            "via_device": ("neerslag", "abcd"),
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._enabled

    @ property
    def state(self):
        return self._state

    @ property
    def name(self):
        return self._name

    @ property
    def unique_id(self):
        """Return unique ID."""
        return self._unique_id

    async def async_update(self):
        self._state = random()
        return True


class NeerslagSensorBuienalarm(mijnBasis):
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, enabled: bool):
        super().__init__(hass=hass, config_entry=config_entry, enabled=enabled)
        self._name = "neerslag_buienalarm_regen_data"
        self._state = "working"  # None
        self._attrs = ["data empty"]
        self._unique_id = "neerslag-sensor-buienalarm-1"

        self._enabled = enabled
        config_entry.add_update_listener(self.mine_update_listener)

        if config_entry.data.get("NeerslagSensorUseHAforLocation") == True:
            self._lat = hass.config.latitude
            self._lon = hass.config.longitude

        else:
            self._lat = config_entry.data.get("buienalarmLatitude")
            self._lon = config_entry.data.get("buienalarmLongitude")

        self._lat = f'{float(self._lat):.3f}'
        self._lon = f'{float(self._lon):.3f}'
        self._icon = "mdi:weather-cloudy"

    @ property
    def icon(self):
        return self._icon

    @ property
    def state_attributes(self):
        if not len(self._attrs):
            return
        return self._attrs

    async def async_update(self):
        if(self._enabled == True):
            self._state = random()
            self._attrs = await self.getBuienalarmData()
        return True

    async def getBuienalarmData(self) -> str:
        data = json.loads('{"data":""}')
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession() as session:
                url = 'https://cdn-secure.buienalarm.nl/api/3.4/forecast.php?lat=' + self._lat + '&lon=' + self._lon + '&region=nl&unit=mm%2Fu&c=' + str(rand.randint(0, 999999999999999))
                async with session.get(url, timeout=timeout) as response:
                    html = await response.text()
                    dataRequest = html.replace('\r\n', ' ')
                    if dataRequest == "" :
                        dataRequest = ""
                    data = json.loads('{"data":' + dataRequest + '}')
                    # _LOGGER.info(data)
                    await session.close()
        except:
            _LOGGER.info("getBuienalarmData - timeout")
            pass

        return data


class NeerslagSensorBuienradar(mijnBasis):
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, enabled: bool):
        super().__init__(hass=hass, config_entry=config_entry, enabled=enabled)

        self._name = "neerslag_buienradar_regen_data"
        self._state = "working"  # None
        self._attrs = ["data empty"]
        self._unique_id = "neerslag-sensor-buienradar-1"

        self._enabled = enabled
        config_entry.add_update_listener(self.mine_update_listener)

        if config_entry.data.get("NeerslagSensorUseHAforLocation") == True:
            self._lat = hass.config.latitude
            self._lon = hass.config.longitude

        else:
            self._lat = config_entry.data.get("buienradarLatitude")
            self._lon = config_entry.data.get("buienradarLongitude")

        self._lat = f'{float(self._lat):.2f}'
        self._lon = f'{float(self._lon):.2f}'
        self._icon = "mdi:weather-cloudy"

    @ property
    def icon(self):
        return self._icon

    @ property
    def state_attributes(self):
        if not len(self._attrs):
            return
        return self._attrs

    async def async_update(self):
        if(self._enabled == True):
            self._state = random()
            self._attrs = await self.getBuienradarData()
        return True

    async def getBuienradarData(self) -> str:
        data = json.loads('{"data":""}')
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession() as session:
                url = 'https://gps.buienradar.nl/getrr.php?lat=' + self._lat + '&lon=' + self._lon + '&c=' + str(rand.randint(0, 999999999999999))
                async with session.get(url, timeout=timeout) as response:
                    html = await response.text()
                    dataRequest = html.replace('\r\n', ' ')
                    if dataRequest == "" :
                        dataRequest = ""
                    data = json.loads('{"data": "' + dataRequest + '"}')
                    # _LOGGER.info(data)
                    await session.close()
        except:
            _LOGGER.info("getBuienradarData - timeout")
            pass

        return data
