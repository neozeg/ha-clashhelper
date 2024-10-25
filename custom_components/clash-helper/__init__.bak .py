from datetime import timedelta
import logging

import aiohttp
import voluptuous as vol
# import time
import datetime

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SELECT]

DOMAIN = "clash-helper"
CONF_SENSOR_NAME = "sensor_name"
CONF_URI = "uri"
CONF_SECRET = "secret"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: {
            vol.Required(CONF_URI): cv.string,
        }
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    uri = config[DOMAIN][CONF_URI]
    secret = config[DOMAIN][CONF_SECRET]
    ps_coor = ProxyStatusCoordinator(hass, uri ,secret)
    con_num_coor = ConnectionCoordinator(hass, uri ,secret)
    pms_coor = ProxyModeStatusCoordinator(hass,uri,secret)
    await ps_coor.async_config_entry_first_refresh()
    await con_num_coor.async_config_entry_first_refresh()
    await pms_coor.async_config_entry_first_refresh()
    hass.data[DOMAIN] = {CONF_URI: uri, "ps_coor": ps_coor,CONF_SECRET:secret,"con_num_coor" : con_num_coor,"pms_coor" : pms_coor}
    await hass.helpers.discovery.async_load_platform(Platform.SENSOR, DOMAIN, {}, {})
    hass.helpers.discovery.load_platform(Platform.SELECT, DOMAIN, {}, {})
    hass.data.setdefault(DOMAIN, {})
    return True

# async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry) -> bool:
#     uri = config[DOMAIN][CONF_URI]
#     secret = config[DOMAIN][CONF_SECRET]
#     ps_coor = ProxyStatusCoordinator(hass, uri ,secret)
#     con_num_coor = ConnectionCoordinator(hass, uri ,secret)
#     pms_coor = ProxyModeStatusCoordinator(hass,uri,secret)
#     await ps_coor.async_config_entry_first_refresh()
#     await con_num_coor.async_config_entry_first_refresh()
#     await pms_coor.async_config_entry_first_refresh()
#     hass.data[DOMAIN] = {CONF_URI: uri, "ps_coor": ps_coor,CONF_SECRET:secret,"con_num_coor" : con_num_coor,"pms_coor" : pms_coor}
#     # await hass.helpers.discovery.async_load_platform(Platform.SENSOR, DOMAIN, {}, {})
#     # hass.helpers.discovery.load_platform(Platform.SELECT, DOMAIN, {}, {})
#     return True


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

class ProxyStatusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, uri, secret):
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

class ConnectionCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, uri, secret):
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