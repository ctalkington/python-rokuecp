"""Asynchronous Python client for Roku."""
import asyncio
from collections import OrderedDict
from socket import gaierror as SocketGIAError
from typing import Any, List, Mapping, Optional
from urllib.parse import quote_plus
from xml.parsers.expat import ExpatError

import aiohttp
import async_timeout
import xmltodict
from yarl import URL

from .__version__ import __version__
from .const import VALID_REMOTE_KEYS
from .exceptions import RokuConnectionError, RokuError
from .models import Device


class Roku:
    """Main class for handling connections with Roku."""

    _device: Optional[Device] = None

    def __init__(
        self,
        host: str,
        base_path: str = "/",
        port: int = 8060,
        request_timeout: int = 5,
        session: aiohttp.client.ClientSession = None,
        user_agent: str = None,
    ) -> None:
        """Initialize connection with receiver."""
        self._session = session
        self._close_session = False

        self.base_path = base_path
        self.host = host
        self.port = port
        self.request_timeout = request_timeout
        self.scheme = "http"
        self.user_agent = user_agent

        if user_agent is None:
            self.user_agent = f"PythonRokuECP/{__version__}"

    async def _request(
        self,
        uri: str = "",
        method: str = "GET",
        data: Optional[Any] = None,
        params: Optional[Mapping[str, str]] = None,
    ) -> Any:
        """Handle a request to a receiver."""
        url = URL.build(
            scheme=self.scheme, host=self.host, port=self.port, path=self.base_path
        ).join(URL(uri))

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/xml, text/xml, text/plain, */*",
        }

        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._close_session = True

        try:
            with async_timeout.timeout(self.request_timeout):
                response = await self._session.request(
                    method, url, data=data, params=params, headers=headers,
                )
        except asyncio.TimeoutError as exception:
            raise RokuConnectionError(
                "Timeout occurred while connecting to device"
            ) from exception
        except (aiohttp.ClientError, SocketGIAError) as exception:
            raise RokuConnectionError(
                "Error occurred while communicating with device"
            ) from exception

        content_type = response.headers.get("Content-Type", "")

        if (response.status // 100) in [4, 5]:
            content = await response.read()
            response.close()

            raise RokuError(
                f"HTTP {response.status}",
                {
                    "content-type": content_type,
                    "message": content.decode("utf8"),
                    "status-code": response.status,
                },
            )

        if "application/xml" in content_type or "text/xml" in content_type:
            content = await response.text()

            try:
                data = xmltodict.parse(content)
            except (ExpatError, IndexError) as error:
                raise RokuError from error

            return data

        return await response.text()

    @property
    def device(self) -> Optional[Device]:
        """Return the cached Device object."""
        return self._device

    def app_icon_url(self, app_id: str) -> str:
        """Get the URL to the application icon."""
        icon_url = URL.build(
            scheme=self.scheme, host=self.host, port=self.port, path=self.base_path
        ).join(URL(f"query/icon/{app_id}"))

        return str(icon_url)

    async def update(self, full_update: bool = False) -> Device:
        """Get all information about the device in a single call."""
        if self._device is None:
            full_update = True

        updates: dict = {}
        updates["info"] = None
        updates["available"] = True
        updates["standby"] = False
        updates["app"] = None
        updates["channel"] = None

        if full_update:
            updates["apps"] = []
            updates["channels"] = []

        updates["info"] = info = await self._get_device_info()

        if info.get("power-mode") != "PowerOn":
            updates["standby"] = True

        tasks = []
        futures: List[Any] = []

        if updates["available"] and not updates["standby"]:
            updates["app"] = app = await self._get_active_app()

            if isinstance(app["app"], dict) and app["app"].get("@id") == "tvinput.dtv":
                tasks.append("channel")
                futures.append(self._get_tv_active_channel())

        if full_update and updates["available"]:
            tasks.append("apps")
            futures.append(self._get_apps())

            if info.get("is-tv", "false") == "true":
                tasks.append("channels")
                futures.append(self._get_tv_channels())

        if len(tasks) > 0:
            results = await asyncio.gather(*futures)

            for (task, result) in zip(tasks, results):
                updates[task] = result

        if self._device is None:
            self._device = Device(updates)
        else:
            self._device.update_from_dict(updates)

        return self._device

    async def launch(self, app_id: str, params: Optional[dict] = None) -> None:
        """Launch application."""
        if params is None:
            params = {}

        request_params = {
            "contentID": app_id,
            **params,
        }

        await self._request(f"launch/{app_id}", method="POST", params=request_params)

    async def literal(self, text: str) -> None:
        """Send literal text."""
        for char in text:
            encoded = quote_plus(char)
            await self._request(f"keypress/Lit_{encoded}", method="POST")

    async def remote(self, key: str) -> None:
        """Emulate pressing a key on the remote."""
        key_lower = key.lower()
        if key_lower not in VALID_REMOTE_KEYS:
            raise RokuError(f"Remote key is invalid: {key}")

        await self._request(f"keypress/{VALID_REMOTE_KEYS[key_lower]}", method="POST")

    async def tune(self, channel: str) -> None:
        """Change the channel on TV tuner."""
        await self.launch("tvinput.dtv", {"ch": channel})

    async def _get_active_app(self) -> OrderedDict:
        """Retrieve active app for updates."""
        res = await self._request("/query/active-app")

        if not isinstance(res, dict) or "active-app" not in res:
            raise RokuError("Roku device returned a malformed result (active-app)")

        return res["active-app"]

    async def _get_apps(self) -> List[OrderedDict]:
        """Retrieve apps for updates."""
        res = await self._request("/query/apps")

        if not isinstance(res, dict) or "apps" not in res:
            raise RokuError("Roku device returned a malformed result (apps)")

        if isinstance(res["apps"]["app"], OrderedDict):
            return [res["apps"]["app"]]

        return res["apps"]["app"]

    async def _get_device_info(self) -> OrderedDict:
        """Retrieve device info for updates."""
        res = await self._request("/query/device-info")

        if not isinstance(res, dict) or "device-info" not in res:
            raise RokuError("Roku device returned a malformed result (device-info)")

        return res["device-info"]

    async def _get_tv_active_channel(self) -> OrderedDict:
        """Retrieve active TV channel for updates."""
        res = await self._request("/query/tv-active-channel")

        if not isinstance(res, dict) or "tv-channel" not in res:
            raise RokuError(
                "Roku device returned a malformed result (tv-active-channel)"
            )

        return res["tv-channel"]["channel"]

    async def _get_tv_channels(self) -> List[OrderedDict]:
        """Retrieve TV channels for updates."""
        res = await self._request("/query/tv-channels")

        if not isinstance(res, dict) or "tv-channels" not in res:
            raise RokuError("Roku device returned a malformed result (tv-channels)")

        if res["tv-channels"] is None or "channel" not in res["tv-channels"]:
            return []

        if isinstance(res["tv-channels"]["channel"], OrderedDict):
            return [res["tv-channels"]["channel"]]

        return res["tv-channels"]["channel"]

    async def close(self) -> None:
        """Close open client session."""
        if self._session and self._close_session:
            await self._session.close()

    async def __aenter__(self) -> "Roku":
        """Async enter."""
        return self

    async def __aexit__(self, *exc_info) -> None:
        """Async exit."""
        await self.close()
