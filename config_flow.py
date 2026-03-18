from __future__ import annotations

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import aiohttp
from aiohttp import BasicAuth, ClientError, ClientSession

_LOGGER = logging.getLogger(__name__)


class IntellinetPDUError(Exception):
    """Base exception."""


class IntellinetPDUConnectionError(IntellinetPDUError):
    """Connection failed."""


class IntellinetPDUAuthError(IntellinetPDUError):
    """Authentication failed."""


class IntellinetPDUProtocolError(IntellinetPDUError):
    """Unexpected response format."""


@dataclass
class OutletConfig:
    name: str
    turn_on_delay: int | None = None
    turn_off_delay: int | None = None


class IntellinetPDUApi:
    def __init__(
        self,
        host: str,
        username: str | None = None,
        password: str | None = None,
        *,
        use_https: bool = False,
        verify_ssl: bool = False,
        nominal_voltage: float = 230.0,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.scheme = "https" if use_https else "http"
        self.verify_ssl = verify_ssl
        self.nominal_voltage = nominal_voltage
        self.outlet_config: dict[int, OutletConfig] = {}

    @property
    def base_url(self) -> str:
        return f"{self.scheme}://{self.host}"

    def _auth(self) -> BasicAuth | None:
        if self.username:
            return BasicAuth(self.username, self.password or "")
        return None

    async def _request(
        self,
        path: str,
        *,
        params: dict | None = None,
        method: str = "GET",
        data: dict | None = None,
    ) -> str:
        url = f"{self.base_url}/{path}"
        timeout = aiohttp.ClientTimeout(total=10)
        connector = aiohttp.TCPConnector(ssl=self.verify_ssl)
        try:
            async with ClientSession(
                auth=self._auth(),
                timeout=timeout,
                connector=connector,
            ) as session:
                async with session.request(method, url, params=params, data=data) as resp:
                    raw = await resp.read()
                    if resp.status == 401:
                        raise IntellinetPDUAuthError(f"HTTP 401 for {path}")
                    if resp.status >= 400:
                        raise IntellinetPDUConnectionError(f"HTTP {resp.status} for {path}")
                    return self._decode(raw)
        except IntellinetPDUError:
            raise
        except (ClientError, asyncio.TimeoutError) as err:
            raise IntellinetPDUConnectionError(str(err)) from err

    @staticmethod
    def _decode(raw: bytes) -> str:
        for enc in ("utf-8", "gb2312", "gbk", "latin-1"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode(errors="ignore")

    async def async_validate(self) -> None:
        await self.fetch_status()
        await self.fetch_outlet_config()

    async def fetch_status(self) -> dict:
        text = await self._request("status.xml")
        try:
            root = ET.fromstring(text)
        except ET.ParseError as err:
            _LOGGER.warning("Could not parse status.xml from %s: %s", self.base_url, text[:300])
            raise IntellinetPDUProtocolError("status.xml was not valid XML") from err

        def pick(*tags):
            for tag in tags:
                value = root.findtext(tag)
                if value not in (None, ""):
                    return value
            return None

        outlets = []
        for idx in range(8):
            state = pick(f"outletStat{idx}")
            if state is None:
                raise IntellinetPDUProtocolError("status.xml did not contain expected outlet tags")
            outlets.append(state.strip().lower())

        current = self._to_float(pick("curBan", "cur0"))
        temperature = self._to_float(pick("tempBan", "temp0"))
        humidity = self._to_float(pick("humBan", "hum0"))
        status = pick("statBan", "stat0", "status")
        voltage = self._to_float(pick("volBan", "vol0", "voltBan", "volt0"))
        if voltage is None:
            voltage = self.nominal_voltage

        outlet_on_count = sum(1 for s in outlets if s == "on")
        power = round(current * voltage, 1) if current is not None and voltage is not None else None

        return {
            "current": current,
            "temperature": temperature,
            "humidity": humidity,
            "status": status,
            "voltage": voltage,
            "power": power,
            "outlets": outlets,
            "outlet_on_count": outlet_on_count,
        }

    async def fetch_outlet_config(self) -> dict[int, OutletConfig]:
        text = await self._request("config_PDU.htm")
        rows = re.findall(r"<tr.*?</tr>", text, flags=re.IGNORECASE | re.DOTALL)
        parsed: dict[int, OutletConfig] = {}
        outlet_index = 0
        for row in rows:
            values = re.findall(r'value=["\']([^"\']*)["\']', row, flags=re.IGNORECASE)
            if len(values) >= 3 and outlet_index < 8:
                name = values[0].strip() or f"Outlet {outlet_index + 1}"
                on_delay = self._to_int(values[1])
                off_delay = self._to_int(values[2])
                parsed[outlet_index] = OutletConfig(
                    name=name,
                    turn_on_delay=on_delay,
                    turn_off_delay=off_delay,
                )
                outlet_index += 1

        if not parsed:
            parsed = {
                idx: OutletConfig(name=f"Outlet {idx + 1}")
                for idx in range(8)
            }

        self.outlet_config = parsed
        return parsed

    async def set_outlet_state(self, outlet: int, turn_on: bool) -> None:
        params = {
            f"outlet{outlet - 1}": 1,
            "op": 0 if turn_on else 1,
            "submit": "Anwenden",
        }
        await self._request("control_outlet.htm", params=params)

    async def power_cycle_outlet(self, outlet: int) -> None:
        params = {
            f"outlet{outlet - 1}": 1,
            "op": 2,
            "submit": "Anwenden",
        }
        await self._request("control_outlet.htm", params=params)

    @staticmethod
    def _to_float(value):
        if value in (None, ""):
            return None
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value):
        if value in (None, ""):
            return None
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None
