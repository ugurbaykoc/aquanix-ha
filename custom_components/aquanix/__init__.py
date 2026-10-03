import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .coordinator import AquanixCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = AquanixCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def handle_delete_message(call: ServiceCall) -> None:
        entry_id = call.data.get("entry_id")
        coordinators = hass.data.get(DOMAIN, {})
        targets = (
            [coordinators[entry_id]]
            if entry_id and entry_id in coordinators
            else list(coordinators.values())
        )
        for coord in targets:
            if coord.data and coord.data.get("has_message"):
                message_id = coord.data.get("message_id", "")
                if message_id:
                    await coord.async_delete_message(message_id)
                    await coord.async_request_refresh()

    hass.services.async_register(DOMAIN, "delete_message", handle_delete_message)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
