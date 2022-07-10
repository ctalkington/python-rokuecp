"""Asynchronous Python client for Roku."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from importlib import metadata
from socket import gaierror as SocketGIAError
from typing import Any
from urllib.parse import quote_plus, urlencode
from xml.parsers.expat import ExpatError

import async_timeout
import xmltodict
from aiohttp.client import ClientError, ClientSession
from yarl import URL

from .const import VALID_REMOTE_KEYS
from .exceptions import RokuConnectionError, RokuConnectionTimeoutError, RokuError
from .helpers import is_ip_address, resolve_hostname
from .models import Device

LOGGER = logging.getLogger(__package__)


@dataclass
class Roku:
    """Main class for Python API."""

    host: str
    base_path: str = "/"
    port: int = 8060
    request_timeout: int = 5
    session: ClientSession | None = None
    user_agent: str | None = None

    _close_session: bool = False
    _dns_lookup: bool = False
    _dns_ip_address: str | None = None
    _dns_resolved_at: datetime | None = None
    _dns_update_interval: timedelta | None = None

    _device: Device | None = None
    _scheme: str = "http"

    def __post_init__(self):
        """Initialize connection parameters."""
        if not is_ip_address(self.host):
            self._dns_lookup = True

        if self.user_agent is None:
            version = metadata.version(__package__)

            self.user_agent = f"PythonRokuECP/{version}"

    async def _resolve_hostname(self) -> str:
        """Attempt to resolve hostname from cache or via resolver.

        Returns:
            The resolved IP Address.
        """
        if self._dns_update_interval is None:
            self._dns_update_interval = timedelta(hours=2)

        update = self._dns_resolved_at is None or datetime.utcnow() >= (
            self._dns_resolved_at + self._dns_update_interval
        )

        if self._dns_ip_address is None or update:
            ip_address = await resolve_hostname(self.host)
            self._dns_ip_address = ip_address
            self._dns_resolved_at = datetime.utcnow()

        return self._dns_ip_address

    async def _request(
        self,
        uri: str = "",
        method: str = "GET",
        data: Any | None = None,
        params: dict[str, Any] | None = None,
        encoded: bool = False,
    ) -> Any:
        """Handle a request to a Roku device.

        Args:
            uri: Request URI, for example `/query/device-info`.
            method: HTTP method to use for the request.E.g., "GET" or "POST".
            data: Dictionary of data to send to the Roku device.
            params: Dictionary of request parameters to send to the Roku device.
            encoded: Whether the URI has already been url encoded.

        Returns:
            A Python dictionary (XML decoded) with the response from the
            Roku device.

        Raises:
            RokuConnectionTimeoutError: A timeout occurred while communicating with
                the Roku device.
            RokuConnectionError: An error occurred while communicating with
                the Roku device.
            RokuError: Received an unexpected response from the Roku device.
        """
        host = self.host

        if self._dns_lookup:
            host = await self._resolve_hostname()

        url = URL.build(
            scheme=self._scheme,
            host=host,
            port=self.port,
            path=self.base_path,
        ).join(URL(uri, encoded=encoded))

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/xml, text/xml, text/plain, */*",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with async_timeout.timeout(self.request_timeout):
                response = await self.session.request(
                    method,
                    url,
                    data=data,
                    params=params,
                    headers=headers,
                )
        except asyncio.TimeoutError as exception:
            raise RokuConnectionTimeoutError(
                "Timeout occurred while connecting to device"
            ) from exception
        except (ClientError, SocketGIAError) as exception:
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
                LOGGER.debug("Requesting %s returned %s", url, data)
            except (ExpatError, IndexError) as error:
                raise RokuError from error

            return data

        return await response.text()

    @property
    def device(self) -> Device | None:
        """Get Roku device information.

        Returns:
            A Device object with information about the Roku device.
        """
        return self._device

    def app_icon_url(self, app_id: str) -> str:
        """Get the URL to the application icon.

        Args:
            app_id: The application ID.

        Returns:
            The URL to the icon for the requested application ID.
        """
        icon_url = URL.build(
            scheme=self._scheme, host=self.host, port=self.port, path=self.base_path
        ).join(URL(f"query/icon/{app_id}"))

        return str(icon_url)

    async def update(  # pylint: disable=too-many-branches
        self, full_update: bool = False
    ) -> Device:
        """Get all information about the device in a single call.

        Args:
            full_update: Should application and channel lists be updated.

        Returns:
            A Device object, with information about the Roku device.
        """
        if self._device is None:
            full_update = True

        updates: dict = {}
        updates["info"] = None
        updates["available"] = True
        updates["standby"] = False
        updates["app"] = None
        updates["channel"] = None
        updates["media"] = None

        if full_update:
            updates["apps"] = []
            updates["channels"] = []

        updates["info"] = info = await self._get_device_info()

        if info.get("power-mode") != "PowerOn":
            updates["standby"] = True

        tasks = []
        futures: list[Any] = []
        app_id = None

        if updates["available"] and not updates["standby"]:
            updates["app"] = app = await self._get_active_app()

            if isinstance(app["app"], dict):
                app_id = app["app"].get("@id")

            if app_id and app_id[:7] != "tvinput":
                tasks.append("media")
                futures.append(self._get_media_state())

            if app_id == "tvinput.dtv":
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

    async def play_on_roku(
        self, video_url: str, params: dict[str, Any] | None = None
    ) -> None:
        """Play video via PlayOnRoku channel.

        Args:
            video_url: The URL to play on the Roku device.
            params: Dictionary of request parameters to send to the Roku device.
        """
        if params is None:
            params = {}

        request_params = {
            "t": "v",
            "u": video_url,
            **params,
        }

        encoded = urlencode(request_params)
        await self._request(f"input/15985?{encoded}", method="POST", encoded=True)

    async def launch(self, app_id: str, params: dict[str, Any] | None = None) -> None:
        """Launch an application on the Roku device.

        Args:
            app_id: The application ID to launch on the Roku device.
            params: Dictionary of request parameters to send to the Roku device.
        """
        if params is None:
            params = {}

        encoded = urlencode(params)
        await self._request(f"launch/{app_id}?{encoded}", method="POST", encoded=True)

    async def literal(self, text: str) -> None:
        """Send literal text to the Roku device.

        Args:
            text: The literal text to send to the Roku device.
        """
        for char in text:
            encoded = quote_plus(char)
            await self._request(f"keypress/Lit_{encoded}", method="POST")

    async def remote(self, key: str) -> None:
        """Emulate pressing a key on the remote.

        Args:
            key: The remote keypress to send to the Roku device.

        Raises:
            RokuError: Received an unexpected response from the Roku device.
        """
        key_lower = key.lower()
        if key_lower not in VALID_REMOTE_KEYS:
            raise RokuError(f"Remote key is invalid: {key}")

        if key_lower == "search":
            await self._request("search/browse", method="POST")
            return

        await self._request(f"keypress/{VALID_REMOTE_KEYS[key_lower]}", method="POST")

    async def search(self, keyword: str) -> None:
        """Emulate opening search and entering keyword on the Roku device.

        Args:
            keyword: The search keyword to send to the Roku device.
        """
        request_params = {
            "keyword": keyword,
        }

        await self._request("search/browse", method="POST", params=request_params)

    async def tune(self, channel: str) -> None:
        """Change the channel on Roku TV device.

        Args:
            channel: The channel number to send to the Roku device.
        """
        await self.launch("tvinput.dtv", {"ch": channel})

    async def _get_active_app(self) -> dict[str, Any]:
        """Retrieve active app for updates.

        Returns:
            A Dictionary.

        Raises:
            RokuError: Received an unexpected response from the Roku device.
        """
        res = await self._request("/query/active-app")

        if not isinstance(res, dict) or "active-app" not in res:
            raise RokuError("Roku device returned a malformed result (active-app)")

        return res["active-app"]

    async def _get_apps(self) -> list[dict[str, Any]]:
        """Retrieve apps for updates.

        Returns:
            A list of Python Dictionaries.

        Raises:
            RokuError: Received an unexpected response from the Roku device.
        """
        res = await self._request("/query/apps")

        if not isinstance(res, dict) or "apps" not in res:
            raise RokuError("Roku device returned a malformed result (apps)")

        if isinstance(res["apps"]["app"], dict):
            return [res["apps"]["app"]]

        return res["apps"]["app"]

    async def _get_device_info(self) -> dict[str, Any]:
        """Retrieve device info for updates.

        Returns:
            A Dictionary.

        Raises:
            RokuError: Received an unexpected response from the Roku device.
        """
        res = await self._request("/query/device-info")

        if not isinstance(res, dict) or "device-info" not in res:
            raise RokuError("Roku device returned a malformed result (device-info)")

        return res["device-info"]

    async def _get_media_state(self) -> dict[str, Any]:
        """Retrieve media state for updates.

        Returns:
            A Dictionary.

        Raises:
            RokuError: Received an unexpected response from the Roku device.
        """
        res = await self._request("/query/media-player")

        if not isinstance(res, dict) or "player" not in res:
            raise RokuError("Roku device returned a malformed result (player)")

        return res["player"]

    async def _get_tv_active_channel(self) -> dict[str, Any]:
        """Retrieve active TV channel for updates.

        Returns:
            A Dictionary.

        Raises:
            RokuError: Received an unexpected response from the Roku device.
        """
        res = await self._request("/query/tv-active-channel")

        if not isinstance(res, dict) or "tv-channel" not in res:
            raise RokuError(
                "Roku device returned a malformed result (tv-active-channel)"
            )

        return res["tv-channel"]["channel"]

    async def _get_tv_channels(self) -> list[dict[str, Any]]:
        """Retrieve TV channels for updates.

        Returns:
            A list of Python Dictionaries.

        Raises:
            RokuError: Received an unexpected response from the Roku device.
        """
        res = await self._request("/query/tv-channels")

        if not isinstance(res, dict) or "tv-channels" not in res:
            raise RokuError("Roku device returned a malformed result (tv-channels)")

        if res["tv-channels"] is None or "channel" not in res["tv-channels"]:
            return []

        if isinstance(res["tv-channels"]["channel"], dict):
            return [res["tv-channels"]["channel"]]

        return res["tv-channels"]["channel"]

    def get_dns_state(self) -> dict[str, Any]:
        """Retrieve DNS resolution state.

        Returns:
            A dictionary of DNS state properties.
        """
        state = {
            "enabled": self._dns_lookup,
            "hostname": self.host if self._dns_lookup else None,
            "ip_address": self._dns_ip_address,
            "resolved_at": self._dns_resolved_at,
        }

        return state

    async def close_session(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Roku:
        """Async enter.

        Returns:
            The Roku object.
        """
        return self

    async def __aexit__(self, *_exc_info: Any) -> None:
        """Async exit.

        Args:
            _exc_info: Exec type.
        """
        await self.close_session()
