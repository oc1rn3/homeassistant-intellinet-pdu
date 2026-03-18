from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_OUTLET,
    CONF_NOMINAL_VOLTAGE,
    DOMAIN,
    PLATFORMS,
    SERVICE_RESTART_ALL_OFFLINE,
    SERVICE_RESTART_OUTLET,
)
from .coordinator import IntellinetPDUCoordinator
from .pdu import IntellinetPDUApi


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
        outlet = int(call.data[ATTR_OUTLET])
        await coordinator.api.power_cycle_outlet(outlet)
        await coordinator.async_request_refresh()

    async def async_handle_restart_all_offline(call: ServiceCall) -> None:
        for idx, state in enumerate(coordinator.data.get("outlets", []), start=1):
            if state != "on":
                await coordinator.api.power_cycle_outlet(idx)
        await coordinator.async_request_refresh()

    if not hass.services.has_service(DOMAIN, SERVICE_RESTART_OUTLET):
        hass.services.async_register(
            DOMAIN,
            SERVICE_RESTART_OUTLET,
            async_handle_restart_outlet,
            schema=vol.Schema(
                {vol.Required(ATTR_OUTLET): vol.All(cv.positive_int, vol.Range(min=1, max=8))}
            ),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_RESTART_ALL_OFFLINE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_RESTART_ALL_OFFLINE,
            async_handle_restart_all_offline,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    if not hass.data[DOMAIN]:
        if hass.services.has_service(DOMAIN, SERVICE_RESTART_OUTLET):
            hass.services.async_remove(DOMAIN, SERVICE_RESTART_OUTLET)
        if hass.services.has_service(DOMAIN, SERVICE_RESTART_ALL_OFFLINE):
            hass.services.async_remove(DOMAIN, SERVICE_RESTART_ALL_OFFLINE)
    return unload_ok
