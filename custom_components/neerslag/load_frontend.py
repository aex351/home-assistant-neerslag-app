from homeassistant.core import HomeAssistant
from homeassistant.components.frontend import add_extra_js_url
from aiohttp import web
from homeassistant.components.http import HomeAssistantView
import logging
import os
from .const import FRONTEND_SCRIPT_URL, DATA_EXTRA_MODULE_URL

_LOGGER = logging.getLogger(__name__)


def setup_view(hass: HomeAssistant):
    _LOGGER.info("-----------setup_view --------")

    add_extra_js_url(hass, FRONTEND_SCRIPT_URL, es5=False)

    # if DATA_EXTRA_MODULE_URL not in hass.data:
    #     hass.data[DATA_EXTRA_MODULE_URL] = set()
    # url_set = hass.data[DATA_EXTRA_MODULE_URL]
    # url_set.add(FRONTEND_SCRIPT_URL)

    hass.http.register_view(NeerslagView(hass, FRONTEND_SCRIPT_URL))


class NeerslagView(HomeAssistantView):
    name = "neerslag_card_script"
    requires_auth = False

    def __init__(self, hass, url):

        _LOGGER.info("-----------__init__ ------oooppppppppppppppppppppppppppppppppppppppppp--")

        self.url = url
        self.config_dir = hass.config.path()

    async def get(self, request):

        dir_path = os.path.dirname(os.path.realpath(__file__))
        _LOGGER.info(dir_path)
        # path = "{}/homeassistant/components/neerslag/neerslag-card.js".format(self.config_dir)
        path = "{}/home-assistant-neerslag-card/neerslag-card.js".format(dir_path)

        _LOGGER.info(self.config_dir)
        _LOGGER.info(path)

        # /workspaces/core/homeassistant/components/neerslag
        filecontent = ""

        try:
            with open(path, mode="r", encoding="utf-8", errors="ignore") as localfile:
                filecontent = localfile.read()
                # _LOGGER.info(filecontent)
                localfile.close()
        except Exception as exception:
            pass

        return web.Response(body=filecontent, content_type="text/javascript", charset="utf-8")
