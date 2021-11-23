"""Asynchronous Python client for Roku."""
import asyncio
from socket import gaierror as SocketGIAError
from typing import Any, Mapping, Optional
from xml.parsers.expat import ExpatError

import aiohttp
import async_timeout
import xmltodict
from yarl import URL

from .__version__ import __version__
from .exceptions import RokuConnectionError, RokuError
from .helpers import is_ip_address, resolve_hostname


class Client:
    """Main class for handling connections with Roku."""

    def __init__(
        self,
        host: str,
        base_path: str = "/",
        port: int = 8060,
        request_timeout: int = 5,
        session: aiohttp.client.ClientSession = None,
        user_agent: str = None,
    ) -> None:
        """Initialize connection with device."""
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
        if not is_ip_address(self.host):
            self.host = await resolve_hostname(self.host)

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
            async with async_timeout.timeout(self.request_timeout):
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

    async def close_session(self) -> None:
        """Close open client session."""
        if self._session and self._close_session:
            await self._session.close()

    async def __aenter__(self) -> "Client":
        """Async enter."""
        return self

    async def __aexit__(self, *exc_info) -> None:
        """Async exit."""
        await self.close_session()
