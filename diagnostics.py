from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN
from .entity import IntellinetPDUEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [IntellinetPDUOutletSwitch(coordinator, entry, idx) for idx in range(8)]
    async_add_entities(entities)


class IntellinetPDUOutletSwitch(IntellinetPDUEntity, SwitchEntity):
    def __init__(self, coordinator, entry, idx):
        super().__init__(coordinator, entry)
        self._idx = idx
        self._attr_unique_id = f"{entry.entry_id}_outlet_{idx + 1}"

    @property
    def name(self):
        cfg = self.coordinator.data.get("outlet_config", {}).get(self._idx)
        if cfg and getattr(cfg, "name", None):
            return f"Intellinet PDU {cfg.name}"
        return f"Intellinet PDU Outlet {self._idx + 1}"

    @property
    def is_on(self):
        return self.coordinator.data["outlets"][self._idx] == "on"

    @property
    def extra_state_attributes(self):
        cfg = self.coordinator.data.get("outlet_config", {}).get(self._idx)
        attrs = {"outlet": self._idx + 1}
        if cfg:
            attrs["turn_on_delay_s"] = cfg.turn_on_delay
            attrs["turn_off_delay_s"] = cfg.turn_off_delay
        return attrs

    async def async_turn_on(self, **kwargs):
        await self.coordinator.api.set_outlet_state(self._idx + 1, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.api.set_outlet_state(self._idx + 1, False)
        await self.coordinator.async_request_refresh()
