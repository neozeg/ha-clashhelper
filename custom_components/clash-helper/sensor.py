import asyncio
from datetime import datetime
import json
import logging

import websockets

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import CONF_SECRET, CONF_URI, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    if discovery_info is None:
        _LOGGER.warning("No discovery info")
        return

    uri = hass.data[DOMAIN][CONF_URI]
    ps_coor = hass.data[DOMAIN]["ps_coor"]
    con_num_coor = hass.data[DOMAIN]["con_num_coor"]
    # con_num_coor2 = hass.data[DOMAIN]["con_num_coor"]
    

    secret = hass.data[DOMAIN][CONF_SECRET]

    coordinator = MyCoordinator(hass, uri,secret)
    await coordinator.async_config_entry_first_refresh()
    async_add_entities(
        [
            #MyWebSocketSensor("Clash_up", coordinator, "up"),
            #MyWebSocketSensor("Clash_down", coordinator, "down"),
            DataRateSensor("UploadRate", coordinator, "up"),
            DataRateSensor("DownloadRate", coordinator, "down"),
            TotalLoadSensor("DownloadTotal", con_num_coor, "downloadTotal"),
            TotalLoadSensor("UploadTotal", con_num_coor, "uploadTotal"),
            ConnectionNumberSensor("ConnectionNumber",con_num_coor)
        ]
    )
    #for proxy in ps_coor.data:
    #    async_add_entities(
    #        [
    #            LastSpeedTestTimeSensor(proxy, ps_coor),
    #            DelaySensor(proxy, ps_coor),
    #        ]
    #    )
    #    if (
    #        ps_coor.data[proxy]["type"] == "Fallback"
    #        or ps_coor.data[proxy]["type"] == "URLTest"
    #    ):
    #        async_add_entities([FallbackCurrentSensor(proxy, ps_coor)])


class MyCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, uri,secret):
        super().__init__(hass, _LOGGER, name="clash sensor", always_update=True)
        self.uri = f"ws://{uri}/traffic"
        self.hass = hass
        self.secret = secret

   # uri = 'ws://your-websocket-server'
   # headers = {
   #     'Authorization': 'Bearer your_token'
   # }
   # async with websockets.client.connect(uri, extra_headers=headers) as websocket:
   #     name = await websocket.recv()
   #     print(f"Received: {name}")

    async def async_config_entry_first_refresh(self):
        headers = {
            'Authorization': f'Bearer {self.secret}'
        }
        #websocket = await websockets.connect(self.uri)
        websocket = await websockets.connect(self.uri,extra_headers=headers)

        async def handle_message(message):
            try:
                data = json.loads(message)
                self.async_set_updated_data(data)
            except json.JSONDecodeError:
                _LOGGER.error("Invalid JSON message received: %s", message)

        async def websocket_handler():
            nonlocal websocket
            while True:
                try:
                    message = await websocket.recv()
                    await handle_message(message)
                except websockets.ConnectionClosed:
                    _LOGGER.warning(
                        "WebSocket connection closed. Retrying in 3 seconds"
                    )
                    await asyncio.sleep(3)
                    #websocket = await websockets.connect(self.uri)
                    websocket = await websockets.connect(self.uri,extra_headers=headers)

        self.hass.loop.create_task(websocket_handler())


class DataRateSensor(CoordinatorEntity, SensorEntity):
    _attr_native_unit_of_measurement = "kB/s"
    _attr_state_class = "measurement"
    _attr_device_class = "data_rate"
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self,sensor_name, coordinator, up_down):
        super().__init__(coordinator, context=up_down)
        self._attr_unique_id = sensor_name
        self.up_down = up_down
      

    @property
    def state(self):
        return round(self.coordinator.data[self.up_down]/1024,2)

    @property
    def available(self):
        return bool(self.coordinator.data)

class TotalLoadSensor(CoordinatorEntity, SensorEntity):
    _attr_native_unit_of_measurement = "kB"
    _attr_state_class = "measurement"
    _attr_device_class = "data_size"
    _attr_should_poll = False

    def __init__(self, sensor_name, coordinator, up_down):
        super().__init__(coordinator, context=up_down)
        self._attr_unique_id = sensor_name
        self.up_down = up_down

    @property
    def native_value(self):
        totalLoad = round(self.coordinator.data[self.up_down]/1024,2)
        _LOGGER.debug(f"{self._attr_unique_id} = {totalLoad}")
        return totalLoad

    @property
    def available(self):
        return bool(self.coordinator.data)
    
    @property
    def state_attributes(self): 
        attrs = {}
        data = self.coordinator.data
        if self.coordinator.data.get(self.kind + "_attrs"):
            attrs = self.coordinator.data[self.kind + "_attrs"]
        if data:            
            attrs["querytime"] = data["querytime"]        
        return attrs  

    
class ConnectionNumberSensor(CoordinatorEntity, SensorEntity):
    #_attr_native_unit_of_measurement = "kB"
    _attr_state_class = "total"
    #_attr_device_class = "data_size"
    _attr_should_poll = False

    def __init__(self, sensor_name, coordinator):
        super().__init__(coordinator, context= "Connection Number")
        self._attr_unique_id = sensor_name
        #self.up_down = up_down
        num = 0
        connections = {}
        connections = self.coordinator.data["connections"]
        for connection in connections:
            if (
                connection["download"] > 0
                or connection["upload"] > 0
            ):
                num += 1
        # _LOGGER.debug(f"connection number = {num}")
        self.connection_number = num

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:connection"


    @property
    def state(self):
        """Return the state."""
        num = 0
        connections = {}
        connections = self.coordinator.data["connections"]
        for connection in connections:
            if (
                connection["download"] > 0
                or connection["upload"] > 0
            ):
                num += 1
        # _LOGGER.debug(f"connection number = {num}")
        self.connection_number = num
        _LOGGER.debug(f"connection number = {self.connection_number}")
        return self.connection_number

    # @property
    # def native_value(self):
    #     return self.connection_number
    @property
    def available(self):
        return bool(self.coordinator.data)





class LastSpeedTestTimeSensor(CoordinatorEntity, SensorEntity):
    _attr_should_poll = False
    _attr_device_class = "date"
    _attr_has_entity_name = True

    def __init__(self, sensor_name, ):
        super().__init__(coordinator, context=f"{sensor_name}.history")
        self.sensor_name = sensor_name
        self._attr_unique_id = f"{sensor_name}_last_speed_test_time"
        self._attr_name = f"{sensor_name} 上次测速时间"

    @property
    def native_value(self):
        history = self.coordinator.data[self.sensor_name]["history"]
        item = history[-1]
        return datetime.fromisoformat(item["time"])

    @property
    def available(self):
        if not self.coordinator.data[self.sensor_name]:
            return False
        history = self.coordinator.data[self.sensor_name]["history"]
        if not history:
            return False
        return True


class DelaySensor(CoordinatorEntity, SensorEntity):
    _attr_should_poll = False
    _attr_device_class = "duration"
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "ms"
    _attr_suggested_unit_of_measurement = "ms"
    _attr_suggested_display_precision = 0

    def __init__(self, sensor_name, coordinator):
        super().__init__(coordinator, context=f"{sensor_name}.history")
        self.sensor_name = sensor_name
        self._attr_unique_id = f"{sensor_name}_delay"
        self._attr_name = sensor_name

    @property
    def native_value(self):
        history = self.coordinator.data[self.sensor_name]["history"]
        item = history[-1]
        return item["delay"]

    @property
    def available(self):
        if not self.coordinator.data[self.sensor_name]:
            return False
        history = self.coordinator.data[self.sensor_name]["history"]
        if not history:
            return False
        item = history[-1]
        return bool(item["delay"])


class FallbackCurrentSensor(CoordinatorEntity, SensorEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, sensor_name, coordinator):
        super().__init__(coordinator, context=f"{sensor_name}.now")
        self.sensor_name = sensor_name
        self._attr_unique_id = f"{sensor_name}_current"
        self._attr_name = f"{sensor_name} 当前选择"

    @property
    def native_value(self):
        return self.coordinator.data[self.sensor_name]["now"]

    @property
    def available(self):
        if self.coordinator.data[self.sensor_name]:
            return True
        return False
