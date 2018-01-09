
import json
from urllib import request, parse
from datetime import timedelta
import logging
import voluptuous as vol

from bs4 import BeautifulSoup
import re
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION, ATTR_FRIENDLY_NAME, TEMP_CELSIUS)
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval
import homeassistant.util.dt as dt_util

import logging

from homeassistant.const import (
    ATTR_ATTRIBUTION, ATTR_FRIENDLY_NAME, TEMP_CELSIUS)
from homeassistant.helpers.entity import Entity
 
TIME_BETWEEN_UPDATES = timedelta(seconds=5)

_LOGGER = logging.getLogger(__name__)

CONF_OPTIONS = "options"


OPTIONS = {
    "stops": [
        "bjbus_stops", "剩余站数", "mdi:bus-side", "站"],
    "distance": ["bjbus_distance", "距离", "mdi:ruler", "km"],
    "time": ["bjbus_time", "到达时间", "mdi:clock-fast", "min"],
}
ATTRIBUTION = ""

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    # 配置项的options是一个列表，列表内容只能是OPTIONS中定义的三个可选项
    vol.Required(CONF_OPTIONS,
                 default=[]): vol.All(cv.ensure_list, [vol.In(OPTIONS)]),
})
 
def setup_platform(hass, config, add_devices, discovery_info=None):

    _LOGGER.info("setup platform bjbus")

    data = busData(hass)
    
    # 根据配置文件options中的内容，添加若干个设备
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
        """更新函数，在sensor组件下系统会定时自动调用（时间间隔在配置文件中可以调整，缺省为30秒）."""

        if self._type == "stops":
            self._state = self._data.stops
        elif self._type == "distance":
            self._state = self._data.distance
        elif self._type == "time":
            self._state = self._data.time
#-------------------------------------------------------------------------------

class busData(object):

    def __init__(self, hass):

        self._stops = None
        self._distance = None
        self._time = None
        self._updatetime = None

        self.update(dt_util.now())

        track_time_interval(hass, self.update, TIME_BETWEEN_UPDATES)

    @property
    def stops(self):
        return self._stops

    @property
    def distance(self):
        return self._distance

    @property
    def time(self):
        return self._time

    def update(self, now):
        """从远程更新信息."""
        _LOGGER.info("Update...")

        # 通过HTTP访问，获取需要的信息
        html = request.urlopen(r'http://www.bjbus.com/home/ajax_rtbus_data.php?act=busTime&selBLine=108&selBDir=5629483961239037439&selBStop=6')
        hjson = json.loads(html.read().decode('utf-8'))
        #print (hjson['html'])
        html2 = hjson['html']
        soup = BeautifulSoup(html2,'html.parser')
        zhan=soup.p.next_sibling.next
        zhan = re.sub("\D", "", zhan) 
        #公里
        km=soup.span.next
        
        nStr = ""
        nStr = nStr.join(km)  #nStr是你要的int的str类型
        kmf = float(nStr)  #pNumr就是你要的int值了
        
        if kmf>20 and kmf<1000:
            kmf=kmf/1000
            #self._unit_of_measurement = "m"
        #else:
            #self._unit_of_measurement = "km"
        
        #分钟
        minute=soup.span.next_sibling.next_sibling.next        
        
        # 根据http返回的结果，更新数据
        self._stops = zhan
        self._distance = kmf
        self._time = minute

