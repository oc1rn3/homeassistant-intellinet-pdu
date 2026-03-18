from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .pdu import IntellinetPDUApi, IntellinetPDUError

_LOGGER = logging.getLogger(__name__)


class IntellinetPDUCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: IntellinetPDUApi) -> None:
        self.entry = entry
        self.api = api
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=f"intellinet_pdu_{entry.entry_id}",
            update_interval=timedelta(seconds=int(interval)),
        )

    async def _async_setup(self) -> None:
        await self.api.fetch_outlet_config()

    async def _async_update_data(self) -> dict:
        try:
            data = await self.api.fetch_status()
            if not self.api.outlet_config:
                await self.api.fetch_outlet_config()
            data["outlet_config"] = self.api.outlet_config
            return data
        except IntellinetPDUError as err:
            raise UpdateFailed(str(err)) from err
