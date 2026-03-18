from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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

    def outlet_label(self, idx: int) -> str:
        cfg = self.coordinator.data.get("outlet_config", {}).get(idx)
        custom_name = getattr(cfg, "name", "") if cfg else ""
        custom_name = (custom_name or "").strip()
        if custom_name:
            return f"Outlet {idx + 1} - {custom_name}"
        return f"Outlet {idx + 1}"
