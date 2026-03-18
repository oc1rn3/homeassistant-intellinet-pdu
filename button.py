from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfElectricCurrent, UnitOfPower, UnitOfTemperature, PERCENTAGE, UnitOfElectricPotential
from homeassistant.entity import EntityCategory

from .const import DOMAIN
from .entity import IntellinetPDUEntity

SENSOR_TYPES = {
    "current": {
        "name": "Current",
        "device_class": SensorDeviceClass.CURRENT,
        "unit": UnitOfElectricCurrent.AMPERE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "power": {
        "name": "Estimated Power",
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.WATT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "voltage": {
        "name": "Voltage",
        "device_class": SensorDeviceClass.VOLTAGE,
        "unit": UnitOfElectricPotential.VOLT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "temperature": {
        "name": "Temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "humidity": {
        "name": "Humidity",
        "device_class": SensorDeviceClass.HUMIDITY,
        "unit": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "status": {
        "name": "Status",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
    "outlet_on_count": {
        "name": "Outlets On",
        "device_class": None,
        "unit": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [IntellinetPDUSensor(coordinator, entry, key, meta) for key, meta in SENSOR_TYPES.items()]
    async_add_entities(entities)


class IntellinetPDUSensor(IntellinetPDUEntity, SensorEntity):
    def __init__(self, coordinator, entry, key, meta):
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_name = f"Intellinet PDU {meta['name']}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_class = meta["device_class"]
        self._attr_native_unit_of_measurement = meta["unit"]
        self._attr_state_class = meta["state_class"]
        if key in ("status", "outlet_on_count"):
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    @property
    def extra_state_attributes(self):
        if self._key == "power":
            return {
                "note": "Calculated from current × voltage. Voltage falls back to the configured nominal voltage when the PDU does not expose a live voltage tag."
            }
        return None
