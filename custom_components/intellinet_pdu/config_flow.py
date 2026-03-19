from __future__ import annotations

import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_NOMINAL_VOLTAGE,
    CONF_OPTIMISTIC_SWITCHING,
    CONF_SCAN_INTERVAL,
    DEFAULT_NOMINAL_VOLTAGE,
    DEFAULT_OPTIMISTIC_SWITCHING,
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


def _build_full_schema(defaults: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Optional(CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")): str,
            vol.Optional(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, "")): str,
            vol.Optional("use_https", default=defaults.get("use_https", False)): bool,
            vol.Optional("verify_ssl", default=defaults.get("verify_ssl", False)): bool,
            vol.Optional(
                CONF_NOMINAL_VOLTAGE,
                default=defaults.get(CONF_NOMINAL_VOLTAGE, DEFAULT_NOMINAL_VOLTAGE),
            ): vol.Coerce(float),
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
            vol.Optional(
                CONF_OPTIMISTIC_SWITCHING,
                default=defaults.get(CONF_OPTIMISTIC_SWITCHING, DEFAULT_OPTIMISTIC_SWITCHING),
            ): bool,
        }
    )


class IntellinetPDUConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        defaults = {
            CONF_NOMINAL_VOLTAGE: DEFAULT_NOMINAL_VOLTAGE,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_OPTIMISTIC_SWITCHING: DEFAULT_OPTIMISTIC_SWITCHING,
            "use_https": False,
            "verify_ssl": False,
        }

        if user_input is not None:
            host = user_input[CONF_HOST].strip()

            api = IntellinetPDUApi(
                host=host,
                username=user_input.get(CONF_USERNAME) or None,
                password=user_input.get(CONF_PASSWORD) or None,
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
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                data = {
                    CONF_HOST: host,
                    CONF_USERNAME: user_input.get(CONF_USERNAME, ""),
                    CONF_PASSWORD: user_input.get(CONF_PASSWORD, ""),
                    "use_https": user_input.get("use_https", False),
                    "verify_ssl": user_input.get("verify_ssl", False),
                    CONF_NOMINAL_VOLTAGE: user_input.get(CONF_NOMINAL_VOLTAGE, DEFAULT_NOMINAL_VOLTAGE),
                }
                options = {
                    CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    CONF_OPTIMISTIC_SWITCHING: user_input.get(CONF_OPTIMISTIC_SWITCHING, DEFAULT_OPTIMISTIC_SWITCHING),
                    CONF_NOMINAL_VOLTAGE: user_input.get(CONF_NOMINAL_VOLTAGE, DEFAULT_NOMINAL_VOLTAGE),
                }
                return self.async_create_entry(title=f"Intellinet PDU ({host})", data=data, options=options)

            defaults = user_input

        return self.async_show_form(
            step_id="user",
            data_schema=_build_full_schema(defaults),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return IntellinetPDUOptionsFlow(config_entry)


class IntellinetPDUOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}

        defaults = {
            CONF_HOST: self._config_entry.data.get(CONF_HOST, ""),
            CONF_USERNAME: self._config_entry.data.get(CONF_USERNAME, ""),
            CONF_PASSWORD: self._config_entry.data.get(CONF_PASSWORD, ""),
            "use_https": self._config_entry.data.get("use_https", False),
            "verify_ssl": self._config_entry.data.get("verify_ssl", False),
            CONF_NOMINAL_VOLTAGE: self._config_entry.options.get(
                CONF_NOMINAL_VOLTAGE,
                self._config_entry.data.get(CONF_NOMINAL_VOLTAGE, DEFAULT_NOMINAL_VOLTAGE),
            ),
            CONF_SCAN_INTERVAL: self._config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            CONF_OPTIMISTIC_SWITCHING: self._config_entry.options.get(
                CONF_OPTIMISTIC_SWITCHING, DEFAULT_OPTIMISTIC_SWITCHING
            ),
        }

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            api = IntellinetPDUApi(
                host=host,
                username=user_input.get(CONF_USERNAME) or None,
                password=user_input.get(CONF_PASSWORD) or None,
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
                _LOGGER.exception("Unexpected error while updating Intellinet PDU options")
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={
                        CONF_HOST: host,
                        CONF_USERNAME: user_input.get(CONF_USERNAME, ""),
                        CONF_PASSWORD: user_input.get(CONF_PASSWORD, ""),
                        "use_https": user_input.get("use_https", False),
                        "verify_ssl": user_input.get("verify_ssl", False),
                        CONF_NOMINAL_VOLTAGE: user_input.get(CONF_NOMINAL_VOLTAGE, DEFAULT_NOMINAL_VOLTAGE),
                    },
                    options={
                        CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                        CONF_OPTIMISTIC_SWITCHING: user_input.get(
                            CONF_OPTIMISTIC_SWITCHING, DEFAULT_OPTIMISTIC_SWITCHING
                        ),
                        CONF_NOMINAL_VOLTAGE: user_input.get(CONF_NOMINAL_VOLTAGE, DEFAULT_NOMINAL_VOLTAGE),
                    },
                )
                return self.async_create_entry(title="", data={})

            defaults = user_input

        return self.async_show_form(
            step_id="init",
            data_schema=_build_full_schema(defaults),
            errors=errors,
        )
