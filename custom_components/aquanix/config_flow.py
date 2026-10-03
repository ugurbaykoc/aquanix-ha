import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    AUTH_HEADER,
    CONF_DEVICE_ID,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MESSAGES_ENDPOINT,
)


def _password_selector() -> selector.TextSelector:
    return selector.TextSelector(
        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
    )


def _user_schema(defaults: dict | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_DEVICE_ID, default=defaults.get(CONF_DEVICE_ID, "")): str,
            vol.Required(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, "")): _password_selector(),
        }
    )


async def validate_connection(hass: HomeAssistant, data: dict) -> bool:
    url = f"{MESSAGES_ENDPOINT}?sifre={data[CONF_PASSWORD]}&device_id={data[CONF_DEVICE_ID]}"
    headers = {"Authorization": AUTH_HEADER, "Accept": "application/json"}
    session = async_get_clientsession(hass)
    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
        return resp.status == 200


class AquanixConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._reauth_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                valid = await validate_connection(self.hass, user_input)
                if valid:
                    await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"Aquanix ST-101 ({user_input[CONF_DEVICE_ID]})",
                        data=user_input,
                    )
                errors["base"] = "invalid_auth"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(user_input),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data):
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors = {}
        if user_input is not None:
            data = {**self._reauth_entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]}
            try:
                valid = await validate_connection(self.hass, data)
                if valid:
                    self.hass.config_entries.async_update_entry(self._reauth_entry, data=data)
                    await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                    return self.async_abort(reason="reauth_successful")
                errors["base"] = "invalid_auth"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): _password_selector()}),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return AquanixOptionsFlowHandler(config_entry)


class AquanixOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                        vol.Coerce(int), vol.Range(min=15)
                    ),
                }
            ),
        )
