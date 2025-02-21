from homeassistant.core import HomeAssistant
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from aiohttp import web
import logging
import os
from .const import FRONTEND_SCRIPT_URL, DATA_EXTRA_MODULE_URL
import time

_LOGGER = logging.getLogger(__name__)


async def setup_view(hass: HomeAssistant):
    timestamp = str(time.time())
    frontend_script_url_with_parameter = FRONTEND_SCRIPT_URL+"?cache="+timestamp

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                FRONTEND_SCRIPT_URL,
                hass.config.path("custom_components/neerslag/home-assistant-neerslag-card/neerslag-card.js"),
                True
            )
        ]
    )
    add_extra_js_url(hass, frontend_script_url_with_parameter , es5=False)

    # Check if Neerslag Card is loaded in frontend, if not: add it again
    resources = hass.data["lovelace"]["resources"]
    if resources:
        if not resources.loaded:
            await resources.async_load()
            resources.loaded = True

        frontend_added = False
        for r in resources.async_items():
            if r["url"].startswith(FRONTEND_SCRIPT_URL):
                frontend_added = True
                continue

        if not frontend_added:
            if getattr(resources, "async_create_item", None):
                await resources.async_create_item(
                    {
                        "res_type": "module",
                        "url": FRONTEND_SCRIPT_URL + "?automatically-added" + "&cache=" + timestamp,
                    }
                )
            elif getattr(resources, "data", None) and getattr(
                resources.data, "append", None
            ):
                resources.data.append(
                    {
                        "type": "module",
                        "url": FRONTEND_SCRIPT_URL + "?automatically-added" + "&cache=" + timestamp,

                    }
                )
