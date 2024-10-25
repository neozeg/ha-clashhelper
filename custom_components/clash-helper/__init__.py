"""The Clash integration."""
from __future__ import annotations
from async_timeout import timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, Config
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed


import aiohttp
from datetime import timedelta
import voluptuous as vol
import time
import datetime
import logging
import asyncio

from homeassistant.exceptions import ConfigEntryNotReady
# from .const import (
#     DOMAIN,
#     CONF_USERNAME,
#     CONF_PASSWD,
#     CONF_PASS,
#     CONF_HOST,    
#     CONF_UPDATE_INTERVAL,
#     COORDINATOR,
#     UNDO_UPDATE_LISTENER,
# )

DOMAIN = "clash-helper"
CONF_SENSOR_NAME = "sensor_name"
CONF_URI = "uri"
CONF_SECRET = "secret"
CONF_UPDATE_INTERVAL = "update_interval_seconds"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: {
            vol.Required(CONF_URI): cv.string,
        }
    },
    extra=vol.ALLOW_EXTRA,
)




_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SELECT]


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up configured Clash."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Clash from a config entry."""
    uri = entry[DOMAIN][CONF_URI]
    secret = entry[DOMAIN][CONF_SECRET]
    ps_coor = ProxyStatusCoordinator(hass, uri ,secret)
    con_num_coor = ConnectionCoordinator(hass, uri ,secret)
    pms_coor = ProxyModeStatusCoordinator(hass,uri,secret)
    await ps_coor.async_config_entry_first_refresh()
    await con_num_coor.async_config_entry_first_refresh()
    await pms_coor.async_config_entry_first_refresh()
    # await coordinator.async_refresh()

    if not ps_coor.last_update_success:
        raise ConfigEntryNotReady
    if not con_num_coor.last_update_success:
        raise ConfigEntryNotReady
    if not pms_coor.last_update_success:
        raise ConfigEntryNotReady

    undo_listener = entry.add_update_listener(update_listener)

    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: ps_coor,
        COORDINATOR: con_num_coor,
        COORDINATOR: pms_coor,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    hass.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
    

async def update_listener(hass, entry):
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)


class ConnectionCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Clash data."""

    def __init__(self, hass, uri, secret):
        """Initialize."""
        update_interval = datetime.timedelta(seconds=15)
        _LOGGER.debug("%s Data will be update every %s", uri, update_interval)
        super().__init__(
            hass,
            _LOGGER,
            name="Connection_Number",
            always_update=True,
            update_interval=timedelta(seconds=15),
        )
        self.hass = hass
        self.uri = f"http://{uri}/connections"
        self.secret = secret

    async def _async_update_data(self):
        headers = {'Authorization': f'Bearer {self.secret}'}
        async with (
            aiohttp.ClientSession() as session,
            #session.get(self.uri) as response,
            session.get(self.uri, headers = headers)  as response,
        ):
            connections = await response.json()
            # querytime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # connections["querytime"] = querytime
            # _LOGGER.debug(connections)
            return connections

class ProxyStatusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, uri, secret):
        """Initialize."""
        update_interval = datetime.timedelta(seconds=15)
        _LOGGER.debug("%s Data will be update every %s", uri, update_interval)
        super().__init__(
            hass,
            _LOGGER,
            name="Clash proxy status",
            always_update=True,
            update_interval=timedelta(seconds=15),
        )
        self.hass = hass
        self.uri = f"http://{uri}/proxies"
        self.secret = secret

    async def _async_update_data(self):
        headers = {'Authorization': f'Bearer {self.secret}'}
        async with (
            aiohttp.ClientSession() as session,
            #session.get(self.uri) as response,
            session.get(self.uri, headers = headers)  as response,
        ):
            return (await response.json())["proxies"]

class ProxyModeStatusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, uri, secret):
        super().__init__(
            hass,
            _LOGGER,
            name="Clash Proxy Mode status",
            always_update=True,
            update_interval=timedelta(seconds=15),
        )
        self.hass = hass
        self.uri = f"http://{uri}/configs"
        self.secret = secret

    async def _async_update_data(self):
        headers = {'Authorization': f'Bearer {self.secret}'}
        async with (
            aiohttp.ClientSession() as session,
            #session.get(self.uri) as response,
            session.get(self.uri, headers = headers)  as response,
        ):
            configs = await response.json()
            _LOGGER.debug(configs)
            return configs


# class IKUAIDataUpdateCoordinator(DataUpdateCoordinator):
#     """Class to manage fetching Clash data."""

#     def __init__(self, hass, host, username, passwd, pas, update_interval_seconds):
#         """Initialize."""
#         update_interval = datetime.timedelta(seconds=update_interval_seconds)
#         _LOGGER.debug("%s Data will be update every %s", host, update_interval)
#         self._token = ""
#         self._token_expire_time = 0
#         self._allow_login = True
    
#         super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

#         self._fetcher = DataFetcher(hass, host, username, passwd, pas)
#         self.host = host
        
#     async def get_access_token(self):
#         if time.time() < self._token_expire_time:
#             return self._token
#         else:
#             if self._allow_login == True:
#                 self._token = await self._fetcher._login_ikuai()
#                 if self._token == 10001:
#                     self._allow_login = False
#                 self._token_expire_time = time.time() + 60*60*2          
#                 return self._token
#             else:
#                 _LOGGER.error("The username or password has been incorrect, please reconfigure the Clash integration.")
#                 return

#     async def _async_update_data(self):
#         """Update data via DataFetcher."""
#         _LOGGER.debug("token_expire_time=%s", self._token_expire_time)
#         if self._allow_login == True:
        
#             sess_key = await self.get_access_token()
#             _LOGGER.debug(sess_key) 

#             try:
#                 async with timeout(10):
#                     data = await self._fetcher.get_data(sess_key)
#                     if data == 401:
#                         self._token_expire_time = 0
#                         return
#                     if not data:
#                         raise UpdateFailed("failed in getting data")
#                     return data
#             except Exception as error:
#                 raise UpdateFailed(error) from error



