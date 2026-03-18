from homeassistant.components.switch import SwitchEntity
from .entity import IntellinetPDUEntity
from .const import DOMAIN

async def async_setup_entry(hass,entry,async_add_entities):
    coord=hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IntellinetPDUOutletSwitch(coord,entry,i) for i in range(8)])

class IntellinetPDUOutletSwitch(IntellinetPDUEntity,SwitchEntity):
    def __init__(self,coordinator,entry,idx):
        super().__init__(coordinator,entry)
        self._idx=idx
        self._attr_unique_id=f"{entry.entry_id}_outlet_{idx+1}"
        self._attr_object_id=f"intellinet_pdu_outlet_{idx+1}"

    @property
    def name(self):
        return self.outlet_label(self._idx)

    @property
    def is_on(self):
        outlets=self.coordinator.data.get("outlets",[])
        return len(outlets)>self._idx and outlets[self._idx]=="on"

    async def async_turn_on(self,**kw):
        await self.coordinator.api.set_outlet_state(self._idx+1,True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self,**kw):
        await self.coordinator.api.set_outlet_state(self._idx+1,False)
        await self.coordinator.async_request_refresh()
