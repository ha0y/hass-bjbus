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

# 配置文件中三个配置项的名称
CONF_OPTIONS = "options"
CONF_LINE = "line"
CONF_DIR = "direction"

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
    # 配置项的options是一个列表，列表内容只能是OPTIONS中定义的三个可选项
    vol.Required(CONF_OPTIONS, default=[]): vol.All(cv.ensure_list, [vol.In(OPTIONS)]),
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """根据配置文件，setup_platform函数会自动被系统调用."""
    _LOGGER.info("setup platform sensor.bjbus...")

    line = config.get(CONF_LINE)
    direction = config.get(CONF_DIR)

    data = busData(hass, line, direction)

    # 添加若干个设备
    dev = []
    for option in config[CONF_OPTIONS]:
        dev.append(bjbus(data, option))
    add_devices(dev, True)


class bjbus(Entity):
    """定义一个温度传感器的类，继承自HomeAssistant的Entity类."""

    def __init__(self, data, option):
        """初始化."""
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
        """更新函数，在sensor组件下系统会定时自动调用（时间间隔在配置文件中可以调整，缺省为30秒）."""
        # update只是从busData中获得数据，数据由busData维护。
#        self._updatetime = self._data.updatetime

        if self._type == "station":
            self._state = self._data.station
        elif self._type == "distance":
            self._state = self._data.distance
        elif self._type == "bustime":
            self._state = self._data.bustime


class busData(object):

    def __init__(self, hass, line, direction):
        """初始化函数."""
        #self._url = "http://www.bjbus.com/home/ajax_rtbus_data.php"
        self._line = line
        self._direction = direction
        #self._params = {"selBLine": line,
                        #"selBDir": direction,
                        #"selBStop": 6,
                        #"act": "busTime"}
        self._station = None
        self._distance = None
        self._bustime = None
        self._updatetime = None

        self.update(dt_util.now())
        # 每隔TIME_BETWEEN_UPDATES，调用一次update(),从京东万象获取数据
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

    #@property
    #def updatetime(self):
        #"""更新时间."""
        #return self._updatetime

    def update(self, now):
        _LOGGER.info("Update from bjbus...")

        # 通过HTTP访问，获取需要的信息
        url = 'http://www.bjbus.com/home/ajax_rtbus_data.php?act=busTime&selBLine=' + str(self._line) + '&selBDir=' + str(self._direction) + '&selBStop=' + '6'
        infomation_file = request.urlopen(url)
        hjson = json.loads(infomation_file.read().decode('utf-8'))

        if hjson is None:
            _LOGGER.error("Request api Error")
            return
        
        #elif result["code"] != "10000":
            #_LOGGER.error("Error API return, code=%s, msg=%s",
                          #result["code"],
                          #result["msg"])
            #return
        soup = BeautifulSoup(hjson['html'],'html.parser')
        if ((soup.span.next_sibling).find("公里") == -1):
            unit = (" 米")
        else:
            unit = (" 千米")
            
        # 根据http返回的结果，更新数据
        #all_result = result["result"]["HeWeather5"][0]
        #self._station = all_result["now"]["tmp"]
        #self._distance = all_result["now"]["hum"]
        #self._bustime = all_result["aqi"]["line"]["bustime"]
        #self._updatetime = all_result["basic"]["update"]["loc"]
        
#        result2 = result['html']

        zhan = soup.p.next_sibling.next
        zhan = re.sub("\D", "", zhan)         
        self._station = zhan
        self._distance = (soup.span.next + unit)
        self._bustime = (soup.span.next_sibling.next_sibling.next + soup.span.next_sibling.next_sibling.next_sibling)
