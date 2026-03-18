from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data


async def async_get_config_entry_diagnostics(hass, entry) -> dict:
    coordinator = hass.data["intellinet_pdu"][entry.entry_id]
    return {
        "entry": async_redact_data(dict(entry.data), {"host", "username", "password"}),
        "options": dict(entry.options),
        "last_data": coordinator.data,
    }
