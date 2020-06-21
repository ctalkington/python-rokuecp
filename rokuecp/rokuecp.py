"""Asynchronous Python client for Roku."""
import asyncio
from collections import OrderedDict
from typing import Any, List, Optional
from urllib.parse import quote_plus

from aiohttp.client import ClientSession
from yarl import URL

from .client import Client
from .const import VALID_REMOTE_KEYS
from .exceptions import RokuError
from .models import Device


class Roku(Client):
    """Main class for Python API."""

    _device: Optional[Device] = None

    def __init__(
        self,
        host: str,
        base_path: str = "/",
        port: int = 8060,
        request_timeout: int = 5,
        session: ClientSession = None,
        user_agent: str = None,
    ) -> None:
        """Initialize connection with receiver."""
        super().__init__(
            host=host,
            base_path=base_path,
            port=port,
            request_timeout=request_timeout,
            session=session,
            user_agent=user_agent,
        )

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
        updates["media"] = None

        if full_update:
            updates["apps"] = []
            updates["channels"] = []

        updates["info"] = info = await self._get_device_info()

        if info.get("power-mode") != "PowerOn":
            updates["standby"] = True

        tasks = []
        futures: List[Any] = []
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

        if key_lower == "search":
            await self._request("search/browse", method="POST")
            return

        await self._request(f"keypress/{VALID_REMOTE_KEYS[key_lower]}", method="POST")

    async def search(self, keyword: str) -> None:
        """Emulate opening search and entering keyword."""
        request_params = {
            "keyword": keyword,
        }

        await self._request("search/browse", method="POST", params=request_params)

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

    async def _get_media_state(self) -> OrderedDict:
        """Retrieve media state for updates."""
        res = await self._request("/query/media-player")

        if not isinstance(res, dict) or "player" not in res:
            raise RokuError("Roku device returned a malformed result (player)")

        return res["player"]

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

    async def __aenter__(self) -> "Roku":
        """Async enter."""
        return self

    async def __aexit__(self, *exc_info) -> None:
        """Async exit."""
        await self.close_session()
