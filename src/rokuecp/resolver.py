"""DNS Resolver for Roku Client based on aiohttp logic."""
from __future__ import annotations

import socket
from asyncio import AbstractEventLoop, get_running_loop
from typing import Any


class ThreadedResolver:
    """Use ThreadPoolExecutor for synchronous getaddrinfo() calls."""

    def __init__(self) -> None:
        """Initialize threaded resolver."""
        self._loop = get_running_loop()

    def get_loop(self) -> AbstractEventLoop:
        """Return the running loop.

        Returns:
            The currently running event loop.
        """
        return self._loop

    async def resolve(
        self, hostname: str, port: int = 0, family: int = socket.AF_INET
    ) -> list[dict[str, Any]]:
        """Return IP addresses for given hostname.

        Args:
            hostname: The hostname to resolve.
            port: The port to use when resolving.
            family: The socket address family.

        Returns:
            List of resolved IP addresses dictionaries.

        Raises:
            OSError: An error occurred while resolving the hostname.
        """
        infos = await self.get_loop().getaddrinfo(
            hostname,
            port,
            type=socket.SOCK_STREAM,
            family=family,
            flags=socket.AI_ADDRCONFIG,
        )

        hosts = []
        for _family, _, proto, _, address in infos:
            if _family == socket.AF_INET6 and address[3]:  # type: ignore
                # LL IPv6 is a VERY rare case.
                raise OSError("link-local IPv6 addresses not supported")

            host, port = address[:2]
            hosts.append(
                {
                    "hostname": hostname,
                    "host": host,
                    "port": port,
                    "family": _family,
                    "proto": proto,
                    "flags": socket.AI_NUMERICHOST | socket.AI_NUMERICSERV,
                }
            )

        return hosts

    async def close(self) -> None:
        """Release resolver."""
