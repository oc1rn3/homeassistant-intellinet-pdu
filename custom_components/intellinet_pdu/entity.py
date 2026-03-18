from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN

class IntellinetPDUEntity(CoordinatorEntity):
    def __init__(self,coordinator,entry):
        super().__init__(coordinator)
        self._entry=entry

    @property
    def device_info(self):
        host=self._entry.data["host"]
        return DeviceInfo(
            identifiers={(DOMAIN,host)},
            name="Intellinet Smart PDU",
            manufacturer="Intellinet",
            model="163682",
            configuration_url=f"http://{host}",
        )

    def outlet_label(self,idx:int):
        cfg=self.coordinator.data.get("outlet_config",{}).get(idx)
        custom=getattr(cfg,"name","") if cfg else ""
        custom=(custom or "").strip()
        if custom:
            return f"Outlet {idx+1} - {custom}"
        return f"Outlet {idx+1}"
