"""Config flow for Neerslag Sensor (Buienalarm / Buienradar) integration."""
import logging
from typing import Optional

import voluptuous as vol
from homeassistant.core import callback

from homeassistant import config_entries, core, exceptions

from .const import DOMAIN  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Optional("buienalarm", default=False): bool,
                                    vol.Optional("buienalarmLatitude", description={"suggested_value": "55.000"}): str,
                                    vol.Optional("buienalarmLongitude", description={"suggested_value": "5.000"}): str,
                                    vol.Optional("buienradar", default=False): bool,
                                    vol.Optional("buienradarLatitude", description={"suggested_value": "55.00"}): str,
                                    vol.Optional("buienradarLongitude", description={"suggested_value": "5.00"}): str,
                                    vol.Optional("NeerslagSensorUseHAforLocation", default=True): bool
                                    })


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    # Return info that you want to store in the config entry.
    return {"title": "Neerslag"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Neerslag Sensor (Buienalarm / Buienradar)."""

    VERSION = 1

    CONNECTION_CLASS = config_entries.CONN_CLASS_UNKNOWN

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            title = "Neerslag App"
            data = user_input

        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):

        testtest = vol.Schema({vol.Optional("buienalarm", default=self.config_entry.data.get("buienalarm")): bool,
                               vol.Optional("buienalarmLatitude", default=self.config_entry.data.get("buienalarmLatitude")): str,
                               vol.Optional("buienalarmLongitude", default=self.config_entry.data.get("buienalarmLongitude")): str,
                               vol.Optional("buienradar", default=self.config_entry.data.get("buienradar")): bool,
                               vol.Optional("buienradarLatitude", default=self.config_entry.data.get("buienradarLatitude")): str,
                               vol.Optional("buienradarLongitude", default=self.config_entry.data.get("buienradarLongitude")): str,
                               vol.Optional("NeerslagSensorUseHAforLocation", default=self.config_entry.data.get("NeerslagSensorUseHAforLocation")): bool
                               })

        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=testtest,
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
