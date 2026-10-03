from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AquanixCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AquanixCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AquanixWaterLowSensor(coordinator, entry)])


class AquanixWaterLowSensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator: AquanixCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_water_low"
        self._attr_name = "Aquanix Hazne Durumu"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_icon = "mdi:water-pump-off"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Aquanix ST-101 ({coordinator.device_id})",
            manufacturer="Aquanix",
            model="ST-101",
        )

    @property
    def is_on(self):
        if self.coordinator.data is None:
            return False
        return self.coordinator.data.get("has_message", False)
