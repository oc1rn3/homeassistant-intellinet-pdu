from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, PLATFORMS, CONF_NOMINAL_VOLTAGE
from .coordinator import IntellinetPDUCoordinator
from .pdu import IntellinetPDUApi

_LOGGER = logging.getLogger(__name__)

SERVICE_RESTART_OUTLET = "restart_outlet"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    api = IntellinetPDUApi(
        host=entry.data["host"],
        username=entry.data.get("username"),
        password=entry.data.get("password"),
        use_https=entry.data.get("use_https", False),
        verify_ssl=entry.data.get("verify_ssl", False),
        nominal_voltage=entry.options.get(
            CONF_NOMINAL_VOLTAGE, entry.data.get(CONF_NOMINAL_VOLTAGE, 230.0)
        ),
    )

    coordinator = IntellinetPDUCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def async_handle_restart_outlet(call: ServiceCall) -> None:
        outlet = int(call.data["outlet"])
        await coordinator.api.power_cycle_outlet(outlet)
        await coordinator.async_request_refresh()

    if not hass.services.has_service(DOMAIN, SERVICE_RESTART_OUTLET):
        hass.services.async_register(
            DOMAIN,
            SERVICE_RESTART_OUTLET,
            async_handle_restart_outlet,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    if not hass.data[DOMAIN] and hass.services.has_service(DOMAIN, SERVICE_RESTART_OUTLET):
        hass.services.async_remove(DOMAIN, SERVICE_RESTART_OUTLET)
    return unload_ok
