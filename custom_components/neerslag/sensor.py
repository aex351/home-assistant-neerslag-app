from homeassistant.block_async_io import enable
from homeassistant.helpers.entity_platform import EntityPlatform
import logging
from os import truncate
import aiohttp

import random as rand

import json
from homeassistant.helpers.entity import Entity
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME, CONF_SOURCE
from datetime import timedelta, datetime, time, date
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import EntityPlatform, async_get_platforms


from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_entries_for_device,
)


_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=180)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Set up sensor entity."""

    if config_entry.data.get("buienalarm") == True:
        async_add_entities(
            [NeerslagSensorBuienalarm(hass, config_entry, True)], update_before_add=True
        )

    if config_entry.data.get("buienalarm") == False:
        async_add_entities(
            [NeerslagSensorBuienalarm(hass, config_entry, False)],
            update_before_add=False,
        )

    if config_entry.data.get("buienradar") == True:
        async_add_entities(
            [NeerslagSensorBuienradar(hass, config_entry, True)], update_before_add=True
        )

    if config_entry.data.get("buienradar") == False:
        async_add_entities(
            [NeerslagSensorBuienradar(hass, config_entry, False)],
            update_before_add=False,
        )


class mijnBasis(Entity):
    _enabled = None
    _unique_id = None
    _name = None
    _icon = None
    _attrs = None

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, enabled: bool):
        _LOGGER.info(
            "--<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>--->>>>>>>>>>>>>>>>>>>>>>>>"
        )
        # self._enabled = enabled
        # config_entry.add_update_listener(self.mine_update_listener)

    async def mine_update_listener(
        self, hass: HomeAssistant, config_entry: ConfigEntry, pp=None
    ):
        """Handle options update."""

        if self._name == "neerslag_buienalarm_regen_data":
            self._enabled = config_entry.data.get("buienalarm")

        if self._name == "neerslag_buienradar_regen_data":
            self._enabled = config_entry.data.get("buienradar")

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                ("neerslag", "neerslag-device")
            },
            "name": "Neerslag App",
            "manufacturer": "aex351",
            "model": "All-in-one package",
            "sw_version": "",
            # "via_device": ("neerslag", "abcd"),
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._enabled

    @property
    def state(self):
        return self._state

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def unit_of_measurement(self):
        return "min"

    @property
    def unique_id(self):
        """Return unique ID."""
        return self._unique_id

    @property
    def state_attributes(self):
        return self._attrs


class NeerslagSensorBuienalarm(mijnBasis):
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, enabled: bool):
        super().__init__(hass=hass, config_entry=config_entry, enabled=enabled)
        self._name = "neerslag_buienalarm_regen_data"
        self._state = 0
        self._attrs = {"updated": 0}  # in epoch secs
        self._unique_id = "neerslag-sensor-buienalarm-1"

        self._enabled = enabled
        config_entry.add_update_listener(self.mine_update_listener)

        if config_entry.data.get("NeerslagSensorUseHAforLocation"):
            self._lat = hass.config.latitude
            self._lon = hass.config.longitude

        else:
            self._lat = config_entry.data.get("buienalarmLatitude")
            self._lon = config_entry.data.get("buienalarmLongitude")

        # format values, enforce 3 decimals
        self._lat = f"{float(self._lat):.3f}"
        self._lon = f"{float(self._lon):.3f}"

        # self._entity_picture = "https://www.buienalarm.nl/assets/img/social.png"
        self._icon = "mdi:weather-cloudy"

    def state_update(self):
        last_update = int(datetime.now().timestamp()) - self._attrs["updated"]
        try:
            precip = self._attrs["data"]["precip"]
            delta = self._attrs["data"]["delta"]
        except KeyError:
            assume_raining = 30  # 2 * 60 is after 2hrs
            if last_update > assume_raining and last_update < assume_raining + 20:
                # Assume it's raining after losing connection for more than 2 hrs.
                _LOGGER.warning(
                    f"getBuienalarmData lost connection for more {assume_raining} min"
                )
                self._state = 0
            return

        self._attrs["updated"] = int(datetime.now().timestamp())
        nz = next((i for i, x in enumerate(precip) if x), None)
        if nz:
            # Rain expected in x minutes
            self._state = int(nz * delta / 60)
        else:
            # None translates to "unknown", so make it next week
            self._state = 7 * 24 * 60
        return

    async def async_update(self):
        if self._enabled:
            self._attrs["data"] = await self.getBuienalarmData()
            self.state_update()
        return True

    async def getBuienalarmData(self) -> str:
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession() as session:
                url = (
                    "https://cdn-secure.buienalarm.nl/api/3.4/forecast.php?lat="
                    + self._lat
                    + "&lon="
                    + self._lon
                    + "&region=nl&c="
                    + str(rand.randint(0, 999999999999999))
                )
                async with session.get(url, timeout=timeout) as response:
                    html = await response.text()
                    dataRequest = html.replace("\r\n", " ")
                    data = json.loads(dataRequest)
                    # _LOGGER.info(data)
                    await session.close()
        except Exception as e:  # aiohttp.ConnectionTimeoutError
            _LOGGER.info("getBuienalarmData - timeout  {e}")
            data = {}
        return data


class NeerslagSensorBuienradar(mijnBasis):
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, enabled: bool):
        super().__init__(hass=hass, config_entry=config_entry, enabled=enabled)

        self._name = "neerslag_buienradar_regen_data"
        self._state = 0
        self._attrs = {"updated": 0}  # in epoch secs
        self._unique_id = "neerslag-sensor-buienradar-1"

        self._enabled = enabled
        config_entry.add_update_listener(self.mine_update_listener)

        if config_entry.data.get("NeerslagSensorUseHAforLocation"):
            self._lat = hass.config.latitude
            self._lon = hass.config.longitude

        else:
            self._lat = config_entry.data.get("buienradarLatitude")
            self._lon = config_entry.data.get("buienradarLongitude")

        # format values, enforce 2 decimals
        self._lat = f"{float(self._lat):.2f}"
        self._lon = f"{float(self._lon):.2f}"

        # self._entity_picture = "https://cdn.buienradar.nl/resources/images/br-logo-square.png"
        self._icon = "mdi:weather-cloudy"

    def state_update(self):
        last_update = int(datetime.now().timestamp()) - self._attrs["updated"]

        pt = [v.split("|") for v in self._attrs["data"].split(" ")]
        try:
            precip, times = zip(*pt)
        except ValueError as e:
            assume_raining = 30
            if (
                last_update > assume_raining and last_update < assume_raining + 20
            ):  # No data received
                # Assume it's raining after losing connection for more than 2 hrs.
                _LOGGER.warning(
                    f"getBuienradarData lost connection for more than {assume_raining} min"
                )
                self._state = 0
            return
        precip = [int(v) for v in precip]
        t0 = datetime.combine(date.today(), time.fromisoformat(times[0]))
        t1 = datetime.combine(date.today(), time.fromisoformat(times[1]))
        delta = int((t1 - t0).seconds)

        self._attrs["updated"] = int(datetime.now().timestamp())
        nz = next((i for i, x in enumerate(precip) if x), None)
        if nz:
            # Rain expected in minutes
            self._state = int(nz * delta / 60)
        else:
            # None translates to "unknown", so make it next week
            self._state = 7 * 24 * 60
        return

    async def async_update(self):
        if self._enabled:
            self._attrs["data"] = await self.getBuienradarData()
            self.state_update()
        return True

    async def getBuienradarData(self) -> str:
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession() as session:
                # https://www.buienradar.nl/overbuienradar/gratis-weerdata
                url = (
                    "https://gps.buienradar.nl/getrr.php?lat="
                    + self._lat
                    + "&lon="
                    + self._lon
                    + "&c="
                    + str(rand.randint(0, 999999999999999))
                )
                # _LOGGER.info(url)
                async with session.get(url, timeout=timeout) as response:
                    html = await response.text()
                    data = " ".join(html.splitlines())
                    # _LOGGER.info(data)
                    await session.close()
        except Exception as e:  # aiohttp.ConnectionTimeoutError
            _LOGGER.info(f"getBuienalarmData - timeout  {e}")
            data = ""
        return data
