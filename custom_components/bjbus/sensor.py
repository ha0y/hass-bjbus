import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION, ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import (aiohttp_client, entity_registry,
                                   update_coordinator)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import get_coordinator
from .bjbus import Bjbus
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

OPTIONS = {
    "station": ["station", "剩余站数", "mdi:bus-side", "站","stationLeft"],
    "distance": ["distance", "距离", "mdi:ruler", "m","distance"],
    "bustime": ["bustime", "到达时间", "mdi:clock-fast", "sec","eta"],
}

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Defer sensor setup to the shared sensor module."""

    config = hass.data[DOMAIN]['configs'].get(config_entry.entry_id, dict(config_entry.data))
    await async_setup_platform(hass, config, async_add_entities)

async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the sensor from config."""
    hass.data.setdefault(DOMAIN, {})
    # hass.data[DOMAIN]['token'] = getToken()
    lineId = config.get('lineId')
    stationId = config.get('stationId')
    coordinator = await get_coordinator(hass, config)
    lineInfo = await hass.data[DOMAIN]['instance'].get_lineinfo(
        lineId
    )
    if 'lineInfo' not in hass.data[DOMAIN]:
        hass.data[DOMAIN]['lineInfo'] = {}
    hass.data[DOMAIN]['lineInfo'][lineId] = lineInfo

    _LOGGER.info(f"Initializing bjbus, lineId: {lineId}, stationId: {stationId}")

    async_add_devices(
        BjbusSensor(coordinator, info_type, config, hass)
        for info_type in OPTIONS.values()
    )


class BjbusSensor(CoordinatorEntity):
    def __init__(self, coordinator, option, config = None, hass = None):
        super().__init__(coordinator)
        self._config = config
        self._coordinator = coordinator
        self._lineInfo = hass.data[DOMAIN]['lineInfo'][config['lineId']]

        self._unique_id = "bjbus_" + config['lineId'] + \
            '-' +config['stationId'] + '-'+self._lineInfo['direction']+'_'+option[0]
        self._name = f"{self._lineInfo['lineName']} {option[1]}"
        self._friendly_name = f"{self._lineInfo['lineName']} {option[1]}"
        self._icon = option[2]
        self._unit_of_measurement = option[3]

        self._type = option
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the device."""
        # return self._state
        if d := self._coordinator.data:
            return d[-1][self._type[4]]
        else:
            return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def icon(self):
        return self._icon

    @property
    def device_state_attributes(self):
        # if self._state is not None:
        return {
            ATTR_ATTRIBUTION: ("车辆均已过站" if not self._coordinator.data else None),
            "首末站"    :f"{self._lineInfo['firstStationName']}→{self._lineInfo['lastStationName']}",
            "方向"      :("上行" if self._lineInfo['direction'] == '1' else "下行" if self._lineInfo['direction'] == '0' else None) ,
            "线路全程"  :f"{float(self._lineInfo['lineLength'])} km",
            "运营时间"  :f"{self._lineInfo['serviceTime']}",
        }
    @property
    def available(self):
        """Return if sensor is available."""
        # if self._coordinator.data:
        #     return True
        # else:
        #     return False
        return True
