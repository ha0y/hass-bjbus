import time
import asyncio
import aiohttp
from dataclasses import dataclass
from aiohttp import ClientSession, ClientTimeout
import logging
import json, base64

class Bjbus:
    def __init__(self, session, token):
        self._session = session
        self._token = token

    async def get_lineinfo(self, lineId):
        """lineinfo."""
        lineInfoUrl = "http://www.bjbus.com/api/api_etaline.php"
        params = {"lineId": lineId,
            "pageNum": 1, "token": self._token}
        resp = await self._session.get(lineInfoUrl, params = params)
        data = await resp.json(content_type=None)

        if data['errorCode'] == 10000:
            results = data['data']
        else:
            results = data

        return results

    async def get_stations(self, lineId):
        """stations."""
        stationListUrl = "http://www.bjbus.com/api/api_etastation.php"
        params = {"lineId": lineId, "token": self._token}
        resp = await self._session.get(stationListUrl, params = params)
        data = await resp.json(content_type=None)

        results = []

        if data['errorCode'] == 10000:
            results = data['data']
        else:
            results = data

        return results

    async def get_bustime(self, lineId, stationId):
        """bustime."""
        busTimeUrl = "http://www.bjbus.com/api/api_etartime.php"
        params = {"conditionstr": lineId + '-'+stationId, "token": self._token}
        resp = await self._session.get(busTimeUrl, params = params)
        data = await resp.json(content_type=None)
        results = []
        if d := data["data"][0]["datas"]:
            for item in d["trip"]:
                try:
                    results.append(item)
                except KeyError:
                    logging.getLogger(__name__).warning("Got wrong data: %s", item)

        return results

    async def search_line(self, keyword):
        searchUrl = "http://www.bjbus.com/api/api_etaline_list.php"
        params = {"city": "北京", "pageindex": 1, "pagesize": 30, "what": keyword}
        resp = await self._session.get(searchUrl, params = params)
        data = await resp.json(content_type=None)
        if data.get('msg') == "无此线路信息":
            return []
        else:
            return data['response']['resultset']['data']['feature']

    @staticmethod
    async def get_token(session: ClientSession):
        """token."""
        url="http://www.bjbus.com/home/fun_rtbus.php?uSec=00000160&uSub=00000162"
        resp = await session.get(url)
        data = await resp.text()
        token = data.split(
            """lineId='+_val+'&pageNum=1&token=""")[1].split("',")[0]
        # tokenExpireTime = json.loads(base64.b64decode(token.split(".")[1]))['exp']
        return token
