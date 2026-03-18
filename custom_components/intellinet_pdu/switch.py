from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN
from .entity import IntellinetPDUEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IntellinetPDUOutletSwitch(coordinator, entry, idx) for idx in range(8)])


class IntellinetPDUOutletSwitch(IntellinetPDUEntity, SwitchEntity):
    def __init__(self, coordinator, entry, idx):
        super().__init__(coordinator, entry)
        self._idx = idx
        self._attr_unique_id = f"{entry.entry_id}_outlet_{idx + 1}"
        self._attr_name = self.outlet_label(idx)
        self._attr_has_entity_name = False
        self._attr_object_id = f"intellinet_pdu_outlet_{idx + 1}"

    @property
    def name(self):
        return self.outlet_label(self._idx)

    @property
    def is_on(self):
        outlets = self.coordinator.data.get("outlets", [])
        return len(outlets) > self._idx and outlets[self._idx] == "on"

    @property
    def available(self):
        return super().available and len(self.coordinator.data.get("outlets", [])) > self._idx

    @property
    def extra_state_attributes(self):
        cfg = self.coordinator.data.get("outlet_config", {}).get(self._idx)
        attrs = {"outlet": self._idx + 1}
        if cfg:
            attrs["configured_name"] = getattr(cfg, "name", "") or None
            attrs["turn_on_delay_s"] = cfg.turn_on_delay
            attrs["turn_off_delay_s"] = cfg.turn_off_delay
        return attrs

    async def async_turn_on(self, **kwargs):
        await self.coordinator.api.set_outlet_state(self._idx + 1, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.api.set_outlet_state(self._idx + 1, False)
        await self.coordinator.async_request_refresh()
