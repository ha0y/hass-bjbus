import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import aiohttp_client

from . import get_coordinator
from .bjbus import Bjbus
from .const import DOMAIN  # pylint:disable=unused-import


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize flow"""
        self._luhaokey = vol.UNDEFINED
        self._select_line_list = {}
        self._select_station_list = {}
        self._lineId = vol.UNDEFINED
        self._stationId = vol.UNDEFINED
        self._lineName = vol.UNDEFINED
        self._board = vol.UNDEFINED

    async def async_step_user(self, user_input=None):
        self.hass.data.setdefault(DOMAIN, {})
        if 'instance' not in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN]['token'] = token = await Bjbus.get_token(aiohttp_client.async_get_clientsession(self.hass))
            self.hass.data[DOMAIN]['instance'] = Bjbus(aiohttp_client.async_get_clientsession(self.hass), token)
        if user_input is not None:
            self._luhaokey = user_input['luhao_key']
            linelist = await self.hass.data[DOMAIN]['instance'].search_line(
                self._luhaokey
            )

            for item in linelist:
                self._select_line_list[item['lineId']] = item['caption']

            return await self.async_step_search_line()


        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema(
                {
                    vol.Required('luhao_key'): str,
                })
        )

    async def async_step_search_line(self, user_input=None):
        if user_input is not None:
            self._lineId = user_input['lineId']
            self._lineName = self._select_line_list[self._lineId].split('(')[0]
            stationlist = await self.hass.data[DOMAIN]['instance'].get_stations(
                self._lineId
            )
            for item in stationlist:
                self._select_station_list[item['stationId']] = item['stopName']
            return await self.async_step_station()

        return self.async_show_form(
            step_id='search_line',
            data_schema=vol.Schema({
                vol.Required('lineId'): vol.In(
                        self._select_line_list
                    )
            })
        )

    async def async_step_station(self, user_input=None):
        if user_input is not None:
            self._stationId = user_input['station']
            self._board = self._select_station_list[self._stationId]
            return self.async_create_entry(
                            title=f"{self._lineName}({self._board}上车)",
                            data={
                                'lineId': self._lineId,
                                'stationId': self._stationId
                            },
                        )

        return self.async_show_form(
            step_id='station',
            data_schema=vol.Schema({
                vol.Required('station'): vol.In(
                        self._select_station_list
                    )
            })
        )
