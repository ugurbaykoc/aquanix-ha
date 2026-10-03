import logging
from datetime import timedelta, datetime, timezone

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DEVICE_ID,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DELETE_ENDPOINT,
    DOMAIN,
    AUTH_HEADER,
    MESSAGE_NO_RECORD,
    MESSAGES_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)

_NO_MESSAGE_RESULT = {
    "has_message": False,
    "message": "",
    "message_id": "",
    "datetime": "",
    "hours_until_delete": 0,
}


class AquanixCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, config_entry) -> None:
        self.config_entry = config_entry
        self.device_id = config_entry.data[CONF_DEVICE_ID]
        self.password = config_entry.data[CONF_PASSWORD]
        self.scan_interval = config_entry.options.get(
            CONF_SCAN_INTERVAL,
            config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        self._headers = {"Authorization": AUTH_HEADER, "Accept": "application/json"}
        self._message_first_seen: dict[str, datetime] = {}

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.scan_interval),
        )

    async def _async_update_data(self):
        session = async_get_clientsession(self.hass)
        url = f"{MESSAGES_ENDPOINT}?sifre={self.password}&device_id={self.device_id}"

        try:
            async with session.get(
                url, headers=self._headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status in (401, 403):
                    raise ConfigEntryAuthFailed("Aquanix: kimlik doğrulama reddedildi")
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                data = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Bağlantı hatası: {err}") from err

        if isinstance(data, list) and len(data) > 0:
            return await self._handle_message(data[0])

        if isinstance(data, dict) and data.get("MessageText") == MESSAGE_NO_RECORD:
            return dict(_NO_MESSAGE_RESULT)

        return dict(_NO_MESSAGE_RESULT)

    async def _handle_message(self, item: dict) -> dict:
        message_id = item.get("ID", "")
        message_text = item.get("MessageText", "")
        message_dt = item.get("DateTime", "")

        now = datetime.now(timezone.utc)

        if message_id not in self._message_first_seen:
            self._message_first_seen[message_id] = now
            _LOGGER.info(
                "Aquanix: Yeni mesaj tespit edildi (ID: %s), 24 saat sonra silinecek.",
                message_id,
            )

        first_seen = self._message_first_seen[message_id]
        elapsed = now - first_seen

        if elapsed >= timedelta(hours=24):
            _LOGGER.info("Aquanix: 24 saat doldu, mesaj siliniyor (ID: %s).", message_id)
            deleted = await self.async_delete_message(message_id)
            if deleted:
                self._message_first_seen.pop(message_id, None)
                return dict(_NO_MESSAGE_RESULT)
            # Silme başarısız oldu (ör. ağ hatası) — mesajı hâlâ aktif say ki
            # gerçek bir "su bitti" durumu geçici olarak "OK" görünmesin;
            # bir sonraki sorguda tekrar silinmeye çalışılacak.
            _LOGGER.warning(
                "Aquanix: mesaj silinemedi (ID: %s), aktif olarak raporlanmaya devam edilecek.",
                message_id,
            )

        remaining = timedelta(hours=24) - elapsed
        hours_left = max(0, int(remaining.total_seconds() // 3600))

        return {
            "has_message": True,
            "message": message_text,
            "message_id": message_id,
            "datetime": message_dt,
            "hours_until_delete": hours_left,
        }

    async def async_delete_message(self, message_id: str) -> bool:
        session = async_get_clientsession(self.hass)
        url = f"{DELETE_ENDPOINT}?sifre={self.password}&id={message_id}"
        try:
            async with session.get(
                url, headers=self._headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    return True
        except aiohttp.ClientError as err:
            _LOGGER.error("Mesaj silinemedi: %s", err)
        return False
