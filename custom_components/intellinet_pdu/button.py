from homeassistant.components.button import ButtonEntity
from .entity import IntellinetPDUEntity
from .const import DOMAIN

async def async_setup_entry(hass,entry,async_add_entities):
    coord=hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RestartButton(coord,entry,i) for i in range(8)])

class RestartButton(IntellinetPDUEntity,ButtonEntity):
    def __init__(self,coordinator,entry,idx):
        super().__init__(coordinator,entry)
        self._idx=idx
        self._attr_unique_id=f"{entry.entry_id}_restart_{idx+1}"
        self._attr_object_id=f"intellinet_pdu_restart_outlet_{idx+1}"

    @property
    def name(self):
        return f"Restart {self.outlet_label(self._idx)}"

    async def async_press(self):
        await self.coordinator.api.power_cycle_outlet(self._idx+1)
        await self.coordinator.async_request_refresh()
