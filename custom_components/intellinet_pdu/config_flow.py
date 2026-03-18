from __future__ import annotations

import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_NOMINAL_VOLTAGE,
    CONF_SCAN_INTERVAL,
    DEFAULT_NOMINAL_VOLTAGE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .pdu import (
    IntellinetPDUApi,
    IntellinetPDUAuthError,
    IntellinetPDUConnectionError,
    IntellinetPDUProtocolError,
)

_LOGGER = logging.getLogger(__name__)


class IntellinetPDUConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            api = IntellinetPDUApi(
                host=host,
                username=user_input.get(CONF_USERNAME),
                password=user_input.get(CONF_PASSWORD),
                use_https=user_input.get("use_https", False),
                verify_ssl=user_input.get("verify_ssl", False),
                nominal_voltage=user_input.get(CONF_NOMINAL_VOLTAGE, DEFAULT_NOMINAL_VOLTAGE),
            )
            try:
                await api.async_validate()
            except IntellinetPDUAuthError:
                errors["base"] = "invalid_auth"
            except IntellinetPDUProtocolError:
                errors["base"] = "invalid_response"
            except IntellinetPDUConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error while validating Intellinet PDU")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=f"Intellinet PDU ({host})", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_USERNAME): str,
                vol.Optional(CONF_PASSWORD): str,
                vol.Optional("use_https", default=False): bool,
                vol.Optional("verify_ssl", default=False): bool,
                vol.Optional(CONF_NOMINAL_VOLTAGE, default=DEFAULT_NOMINAL_VOLTAGE): vol.Coerce(float),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        return IntellinetPDUOptionsFlow(config_entry)


class IntellinetPDUOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                vol.Optional(
                    CONF_NOMINAL_VOLTAGE,
                    default=self.config_entry.options.get(CONF_NOMINAL_VOLTAGE, DEFAULT_NOMINAL_VOLTAGE),
                ): vol.All(vol.Coerce(float), vol.Range(min=100, max=250)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
