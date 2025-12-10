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
    dir_path = os.path.dirname(os.path.realpath(__file__))
    path_to_file = os.path.join(
        dir_path,
        "home-assistant-neerslag-card",
        "neerslag-card.js",
    )

    should_cache = False

    _LOGGER.debug(
        "Neerslag frontend: registering static path %s -> %s",
        FRONTEND_SCRIPT_URL,
        path_to_file,
    )

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                FRONTEND_SCRIPT_URL,
                path_to_file,
                should_cache,
            )
        ]
    )

    add_extra_js_url(hass, FRONTEND_SCRIPT_URL, es5=False)

    _LOGGER.debug(
        "Neerslag frontend: registered extra JS module URL %s",
        FRONTEND_SCRIPT_URL,
    )
