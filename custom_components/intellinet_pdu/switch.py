from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from .const import CONF_OPTIMISTIC_SWITCHING, DEFAULT_OPTIMISTIC_SWITCHING, DOMAIN
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

    @property
    def suggested_object_id(self) -> str:
        return f"intellinet_pdu_outlet_{self._idx + 1}"

    @property
    def name(self):
        return self.outlet_label(self._idx)

    @property
    def _optimistic_enabled(self) -> bool:
        return self._entry.options.get(CONF_OPTIMISTIC_SWITCHING, DEFAULT_OPTIMISTIC_SWITCHING)

    @property
    def is_on(self):
        if self._optimistic_enabled:
            optimistic = self.coordinator.optimistic_states.get(self._idx)
            if optimistic is not None:
                return optimistic == "on"
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
        if self._optimistic_enabled and self._idx in self.coordinator.optimistic_states:
            attrs["optimistic_state"] = self.coordinator.optimistic_states[self._idx]
        return attrs

    async def async_turn_on(self, **kwargs):
        if self._optimistic_enabled:
            self.coordinator.optimistic_states[self._idx] = "on"
            self.async_write_ha_state()
        await self.coordinator.api.set_outlet_state(self._idx + 1, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        if self._optimistic_enabled:
            self.coordinator.optimistic_states[self._idx] = "off"
            self.async_write_ha_state()
        await self.coordinator.api.set_outlet_state(self._idx + 1, False)
        await self.coordinator.async_request_refresh()
