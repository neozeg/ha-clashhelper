import json
import logging

import aiohttp

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CONF_SECRET,CONF_URI, DOMAIN

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, async_add_entities, discovery_info=None):
    if discovery_info is None:
        _LOGGER.warning("No discovery info")
        return

    uri = hass.data[DOMAIN][CONF_URI]
    ps_coor = hass.data[DOMAIN]["ps_coor"]    
    pms_coor = hass.data[DOMAIN]["pms_coor"]
    # _LOGGER.debug(pms_coor)
    # _LOGGER.debug(pms_coor["mode"])
    # _LOGGER.debug(pms_coor.data["mode"])
    # #secret = '123456'
    secret = hass.data[DOMAIN][CONF_SECRET]

    for proxy in ps_coor.data:
        if ps_coor.data[proxy]["type"] == "Selector":
            async_add_entities([Selector(proxy, ps_coor, uri,secret)])

    async_add_entities([ProxyModeSelector(pms_coor,uri,secret)])


class ProxyModeSelector(CoordinatorEntity, SelectEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, coordinator, uri,secret):
        super().__init__(coordinator)
        self.sensor_name = "ProxyMode"
        self.uri = uri
        self._attr_unique_id = "proxymode_select"
        self._attr_name = "proxymode 当前选择"
        self.secret = secret
        _LOGGER.debug(coordinator.data["mode"])

    async def async_select_option(self, option: str) -> None:
        body = json.dumps({"mode": option})
        headers = {'Authorization': f'Bearer {self.secret}'}
        async with aiohttp.ClientSession() as session:
            await session.patch(
                f"http://{self.uri}/configs", headers=headers,data=body
            )
        await self.coordinator.async_request_refresh()

    @property
    def current_option(self):
        curr_option = self.coordinator.data["mode"]
        return curr_option#"direct"

    @property
    def options(self):
        options = ["global","rule","direct"]
        return options

    @property
    def available(self):
        if self.coordinator.data["mode"]:
            return True
        return False

class Selector(CoordinatorEntity, SelectEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, sensor_name, coordinator, uri,secret):
        super().__init__(coordinator, context=f"{sensor_name}.now")
        self.sensor_name = sensor_name
        self.uri = uri
        self._attr_unique_id = f"{sensor_name}_select"
        self._attr_name = f"{sensor_name} 当前选择"
        self.secret = secret

    async def async_select_option(self, option: str) -> None:
        body = json.dumps({"name": option})
        headers = {'Authorization': f'Bearer {self.secret}'}
        async with aiohttp.ClientSession() as session:
            await session.put(
                f"http://{self.uri}/proxies/{self.sensor_name}", headers=headers,data=body
            )
        await self.coordinator.async_request_refresh()

    @property
    def current_option(self):
        return self.coordinator.data[self.sensor_name]["now"]

    @property
    def options(self):
        return self.coordinator.data[self.sensor_name]["all"]

    @property
    def available(self):
        if self.coordinator.data[self.sensor_name]:
            return True
        return False
