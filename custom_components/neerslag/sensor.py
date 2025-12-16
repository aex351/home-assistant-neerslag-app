from __future__ import annotations

import logging
import math
import json
from datetime import timedelta, datetime, time, date
from random import random
import random as rand
from typing import Any

import aiohttp
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=180)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Set up sensor entity."""

    # Buienalarm – altijd entity registreren, enabled via checkbox
    buienalarm_enabled = bool(config_entry.data.get("buienalarm", False))
    async_add_entities(
        [NeerslagSensorBuienalarm(hass, config_entry, buienalarm_enabled)],
        update_before_add=buienalarm_enabled,
    )

    # Buienradar – idem
    buienradar_enabled = bool(config_entry.data.get("buienradar", False))
    async_add_entities(
        [NeerslagSensorBuienradar(hass, config_entry, buienradar_enabled)],
        update_before_add=buienradar_enabled,
    )


class mijnBasis(Entity):
    _enabled: bool
    _unique_id: str | None
    _name: str | None
    _lat: float
    _lon: float

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, enabled: bool):
        _LOGGER.info("Neerslag entity geladen")

    async def mine_update_listener(
        self, hass: HomeAssistant, config_entry: ConfigEntry, pp=None
    ):
        """Handle options update."""

        if self._name == "neerslag_buienalarm_regen_data":
            self._enabled = bool(config_entry.data.get("buienalarm"))

        if self._name == "neerslag_buienradar_regen_data":
            self._enabled = bool(config_entry.data.get("buienradar"))

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
            self._lat = float(hass.config.latitude)
            self._lon = float(hass.config.longitude)

        else:
            self._lat = float(config_entry.data.get("buienalarmLatitude") or 0.0)
            self._lon = float(config_entry.data.get("buienalarmLongitude") or 0.0)

        # format values, enforce 3 decimals
        self._lat = float(f"{float(self._lat):.3f}" or 0.0)
        self._lon = float(f"{float(self._lon):.3f}" or 0.0)

        # self._entity_picture = "https://www.buienalarm.nl/assets/img/social.png"
        self._icon = "mdi:weather-cloudy"

    def state_update(self):
        last_update = int(datetime.now().timestamp()) - self._attrs["updated"]
        try:
            precip = self._attrs["data"]["data"]["precip"]
            delta = self._attrs["data"]["data"]["delta"]
        except KeyError:
            assume_raining = 30  # 2 * 60 is after 2hrs
            if last_update > assume_raining and last_update < assume_raining + 20:
                # Assume it's raining after losing connection for more than 2 hrs.
                _LOGGER.warning(
                    f"getBuienalarmData lost connection for more {assume_raining} min"
                )
                self._state = 0
            return False

        self._attrs["updated"] = int(datetime.now().timestamp())
        nz = next((i for i, x in enumerate(precip) if x), None)
        if nz:
            # Rain expected in x minutes
            self._state = int(nz * delta / 60)
        else:
            # None translates to "unknown", so make it next week
            self._state = 7 * 24 * 60
        return True

    async def async_update(self):
        if self._enabled:
            self._attrs["data"] = await self.getBuienalarmData()
            return self.state_update()
        return True

    async def getBuienalarmData(self) -> str:
        # Oude structuur
        data = {
            "success": False,
            "start": None,
            "delta": 0,
            "precip": [],
        }

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession() as session:
                url = (
                    "https://imn-rust-lb.infoplaza.io/v4/nowcast/ba/timeseries/"
                    + str(self._lat)
                    + "/"
                    + str(self._lon)
                    + "/?c="
                    + str(rand.randint(0, 999999999999999))
                )

                async with session.get(url, timeout=timeout) as response:
                    raw = await response.text()
                    raw = raw.replace("\r\n", " ")

                    if not raw.strip():
                        return data

                    new_json = json.loads(raw)

                    timeseries = new_json.get("data", [])
                    summary = new_json.get("summary", {})

                    old = data
                    old["success"] = True

                    # START: uit summary.timestamp (of fallback)
                    start_ts = summary.get("timestamp")
                    if start_ts is None and timeseries:
                        start_ts = timeseries[0].get("timestamp")
                    old["start"] = start_ts

                    # PRECIP-array
                    old["precip"] = [
                        item.get("precipitationrate", 0) for item in timeseries
                    ]

                    # DELTA: interval tussen eerste twee timestamps
                    if len(timeseries) >= 2:
                        t0 = timeseries[0].get("timestamp")
                        t1 = timeseries[1].get("timestamp")

                        if isinstance(t0, int) and isinstance(t1, int):
                            diff = t1 - t0
                            if diff > 0:
                                old["delta"] = diff  # default wordt overschreven

                    # --- PRECIP (mm/h → code 0..255) ---
                    precip_codes = []
                    for item in timeseries:
                        rate = item.get(
                            "precipitationrate", 0.0
                        )  # mm/uur (waarschijnlijk)

                        if rate <= 0:
                            code = 0
                        else:
                            code = 32 * math.log10(rate) + 109
                            code = round(code)
                            code = max(0, min(255, code))  # clamp

                        precip_codes.append(code)

                    old["precip"] = precip_codes

        except Exception:
            _LOGGER.info("getBuienalarmData - timeout")
            pass

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
            self._lat = float(config_entry.data.get("buienradarLatitude") or 0.0)
            self._lon = float(config_entry.data.get("buienradarLongitude") or 0.0)

        # format values, enforce 2 decimals
        self._lat = float(f"{float(self._lat):.2f}" or 0.0)
        self._lon = float(f"{float(self._lon):.2f}" or 0.0)

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
            return False
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
        return True

    async def async_update(self):
        if self._enabled:
            self._attrs["data"] = await self.getBuienradarData()
            return self.state_update()
        return True

    async def getBuienradarData(self) -> str:
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession() as session:
                # https://www.buienradar.nl/overbuienradar/gratis-weerdata
                url = (
                    "https://gps.buienradar.nl/getrr.php?lat="
                    + str(self._lat)
                    + "&lon="
                    + str(self._lon)
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
            _LOGGER.info(f"getBuienradarData - timeout  {e}")
            data = ""
        return data
