from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


class IntellinetPDUEntity(CoordinatorEntity):
    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        host = self._entry.data["host"]
        return DeviceInfo(
            identifiers={(DOMAIN, host)},
            name="Intellinet Smart PDU",
            manufacturer="Intellinet",
            model="163682",
            configuration_url=f"http://{host}",
        )
