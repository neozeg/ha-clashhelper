"""Config flow for ikuai integration."""

# passwd:明文密码md5
# pass：salt_11+明文密码base64-utf8编码
# remember_passwd：null，在此处写为None，经过dumps自动转为null
# username:用户名明文


from __future__ import annotations

import aiohttp
import logging
import uuid
import voluptuous as vol
import requests

import json,base64
from hashlib import md5

from homeassistant import config_entries
from homeassistant.core import callback

from collections import OrderedDict
from . import CONF_SECRET,CONF_URI,CONF_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """handle config flow for this integration"""
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlow(config_entry)
        
        
    def __init__(self):
        """Initialize."""
        self._errors = {}

    def _login_clash(self,uri, secret):
        self.uri = f"http://{uri}/configs"
        self.secret = secret
        headers = {'Authorization': f'Bearer {self.secret}'}
        # async with (
        #     aiohttp.ClientSession() as session,
        #     #session.get(self.uri) as response,
        #     session.get(self.uri, headers = headers)  as response,
        # ):
        #     configs = await response.json()
        #     _LOGGER.debug(configs)
        #     return configs
        return requests.get(self.uri, headers = headers)

    async def async_step_user(self, user_input={}):
        self._errors = {}
        if user_input is not None:
            config_data = {}      
            uri = user_input[CONF_URI]
            secret = user_input[CONF_SECRET]      
            _LOGGER.debug(
                "uri: %s, secret: %s",
                uri, secret
            )

            response = await self.hass.async_add_executor_job(
                self._login_clash, uri, secret
            )
            _LOGGER.debug(response)

            if response.status_code != 200:
                self._errors["base"] = "unkown"
                return await self._show_config_form(user_input)

            # json_text = response.content.decode('utf-8')
            # resdata = json.loads(json_text)            
            # if resdata["Result"] == 10001:
            #     self._errors["base"] = "invalid_auth"
            #     return await self._show_config_form(user_input)

            _LOGGER.debug(
                "Login  Clash successfully, save data for Clash: %s",
                uri,
            )
            await self.async_set_unique_id(f"Clash-{uri}")
            self._abort_if_unique_id_configured()

            config_data[CONF_URI] = uri
            config_data[CONF_SECRET] = secret
            return self.async_create_entry(title=f"Clash-{uri}", data=config_data)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):

        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_URI, default = "192.168.1.1")] = str
        data_schema[vol.Required(CONF_SECRET, default = "666666")] = str

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors
        )


class OptionsFlow(config_entries.OptionsFlow):
    """Config flow options for autoamap."""

    def __init__(self, config_entry):
        """Initialize autoamap options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(CONF_UPDATE_INTERVAL, 10),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600))
                }
            ),
        )
