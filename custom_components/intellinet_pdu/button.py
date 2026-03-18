from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import IntellinetPDUEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IntellinetPDUOutletRestartButton(coordinator, entry, idx) for idx in range(8)])


class IntellinetPDUOutletRestartButton(IntellinetPDUEntity, ButtonEntity):
    def __init__(self, coordinator, entry, idx):
        super().__init__(coordinator, entry)
        self._idx = idx
        self._attr_unique_id = f"{entry.entry_id}_restart_{idx + 1}"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_name = f"Restart {self.outlet_label(idx)}"
        self._attr_has_entity_name = False
        self._attr_object_id = f"intellinet_pdu_restart_outlet_{idx + 1}"

    @property
    def name(self):
        return f"Restart {self.outlet_label(self._idx)}"

    async def async_press(self) -> None:
        await self.coordinator.api.power_cycle_outlet(self._idx + 1)
        await self.coordinator.async_request_refresh()
