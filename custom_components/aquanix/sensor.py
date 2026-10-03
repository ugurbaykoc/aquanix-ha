from homeassistant.components.sensor import SensorEntity
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
    async_add_entities([AquanixMessageSensor(coordinator, entry)])


class AquanixMessageSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: AquanixCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_message"
        self._attr_name = "Aquanix Son Mesaj"
        self._attr_icon = "mdi:water-pump"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Aquanix ST-101 ({coordinator.device_id})",
            manufacturer="Aquanix",
            model="ST-101",
        )

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        if self.coordinator.data.get("has_message"):
            return self.coordinator.data.get("message", "")
        return "OK"

    @property
    def extra_state_attributes(self):
        if self.coordinator.data is None:
            return {}
        return {
            "message_id": self.coordinator.data.get("message_id", ""),
            "datetime": self.coordinator.data.get("datetime", ""),
            "has_message": self.coordinator.data.get("has_message", False),
            "hours_until_delete": self.coordinator.data.get("hours_until_delete", 0),
        }
