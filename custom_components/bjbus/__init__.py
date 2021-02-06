import asyncio
from datetime import timedelta
import logging

import async_timeout
from .bjbus import Bjbus

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import aiohttp_client, entity_registry, update_coordinator

from .const import DOMAIN

PLATFORMS = ["sensor"]

async def async_setup(hass, hassconfig: dict):
    """Setup Component."""
    hass.data.setdefault(DOMAIN, {})

    config = hassconfig.get(DOMAIN) or {}
    hass.data[DOMAIN]['config'] = config
    hass.data[DOMAIN]['token'] = token = await Bjbus.get_token(aiohttp_client.async_get_clientsession(hass))
    hass.data[DOMAIN]['instance'] = Bjbus(aiohttp_client.async_get_clientsession(hass), token)
    # await get_coordinator(hass, config)
    return True

async def async_setup_entry(hass, entry):
    """Set up from config flow."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]['configs']={}
    config = {}
    for item in ['lineId',
                 'stationId',
                 ]:
        config[item] = entry.data.get(item)
    # bjbus.LineStop()

    config['config_entry'] = entry
    entry_id = entry.entry_id
    unique_id = entry.unique_id
    hass.data[DOMAIN]['configs'][entry_id] = config
    hass.data[DOMAIN]['configs'][unique_id] = config

    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, 'sensor'))

    return True

async def get_coordinator(hass, config):
    """Get the data update coordinator."""
    try:
        return hass.data[DOMAIN][f"{config.get('lineId')}-{config.get('stationId')}"]
    except:
        pass

    async def async_update_data():
        with async_timeout.timeout(10):
            return [
                trip for trip in await hass.data[DOMAIN]['instance'].get_bustime(
                    config['lineId'],
                    config['stationId']
                )
            ]

    hass.data[DOMAIN][f"{config.get('lineId')}-{config.get('stationId')}"] = update_coordinator.DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name=f"{DOMAIN}-{config.get('lineId')}-{config.get('stationId')}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=10),
    )
    await hass.data[DOMAIN][f"{config.get('lineId')}-{config.get('stationId')}"].async_refresh()
    return hass.data[DOMAIN][f"{config.get('lineId')}-{config.get('stationId')}"]
