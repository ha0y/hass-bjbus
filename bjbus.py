'''本插件的编写参考了 hachina 的开发教程。'''
import json
from urllib import request, parse
import logging
from datetime import timedelta
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION, ATTR_FRIENDLY_NAME, TEMP_CELSIUS)
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval
import homeassistant.util.dt as dt_util

from bs4 import BeautifulSoup
import re

_LOGGER = logging.getLogger(__name__)

TIME_BETWEEN_UPDATES = timedelta(seconds=5)

CONF_OPTIONS = "options"
CONF_LINE = "line"
CONF_DIR = "direction"
CONF_BOARD = "board"

OPTIONS = {
    "station": ["bjbus_station", "剩余站数", "mdi:bus-side", "站"],
    "distance": ["bjbus_distance", "距离", "mdi:ruler", ""],
    "bustime": ["bjbus_bustime", "到达时间", "mdi:clock-fast", ""],
}

#ATTR_UPDATE_TIME = "更新时间"
ATTRIBUTION = ""


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_LINE): cv.string,
    vol.Required(CONF_DIR): cv.string,
    vol.Required(CONF_OPTIONS, default=[]): vol.All(cv.ensure_list, [vol.In(OPTIONS)]),
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    _LOGGER.info("setup platform sensor.bjbus...")

    line = config.get(CONF_LINE)
    direction = config.get(CONF_DIR)
    board = config.get(CONF_BOARD)

    data = busData(hass, line, direction, board)

    dev = []
    for option in config[CONF_OPTIONS]:
        dev.append(bjbus(data, option))
    add_devices(dev, True)


class bjbus(Entity):

    def __init__(self, data, option):
        self._data = data
        self._object_id = OPTIONS[option][0]
        self._friendly_name = OPTIONS[option][1]
        self._icon = OPTIONS[option][2]
        self._unit_of_measurement = OPTIONS[option][3]

        self._type = option
        self._state = None
#        self._updatetime = None

    @property
    def name(self):
        return self._object_id

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return self._icon

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def device_state_attributes(self):
        if self._state is not None:
            return {
                ATTR_ATTRIBUTION: ATTRIBUTION,
                ATTR_FRIENDLY_NAME: self._friendly_name,
#                ATTR_UPDATE_TIME: self._updatetime
            }

    def update(self):

        if self._type == "station":
            self._state = self._data.station
        elif self._type == "distance":
            self._state = self._data.distance
        elif self._type == "bustime":
            self._state = self._data.bustime


class busData(object):

    def __init__(self, hass, line, direction, board):
        """初始化函数."""

        self._line = line
        self._direction = direction
        self._board = board

        self._station = None
        self._distance = None
        self._bustime = None
        self._updatetime = None

        self.update(dt_util.now())

        track_time_interval(hass, self.update, TIME_BETWEEN_UPDATES)

    @property
    def station(self):
        return self._station

    @property
    def distance(self):
        return self._distance

    @property
    def bustime(self):
        return self._bustime

    def update(self, now):
        """从远程更新信息."""
        _LOGGER.info("Update from bjbus...")

        url = 'http://www.bjbus.com/home/ajax_rtbus_data.php?act=busTime&selBLine=' + str(self._line) + '&selBDir=' + str(self._direction) + '&selBStop=' + str(self._board)
        infomation_file = request.urlopen(url)
        hjson = json.loads(infomation_file.read().decode('utf-8'))

        if hjson is None:
            _LOGGER.error("Request api Error")
            return

        soup = BeautifulSoup(hjson['html'],'html.parser')
        if ((soup.span.next_sibling).find("公里") == -1):
            unit = (" m")
        else:
            unit = (" km")

        zhan = soup.p.next_sibling.next
        zhan = re.sub("\D", "", zhan)         
        self._station = zhan
        self._distance = (soup.span.next + unit)
        self._bustime = (soup.span.next_sibling.next_sibling.next + soup.span.next_sibling.next_sibling.next_sibling)
