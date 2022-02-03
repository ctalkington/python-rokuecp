"""DNS Resolver for Roku Client based on aiohttp logic."""
import socket
from asyncio import get_running_loop
from typing import Any, Dict, List


class ThreadedResolver:
    """Use ThreadPoolExecutor for synchronous getaddrinfo() calls."""

    def __init__(self) -> None:
        """Initialize threaded resolver."""
        self._loop = get_running_loop()

    def get_loop(self):
        """Return the running loop."""
        return self._loop

    async def resolve(
        self, hostname: str, port: int = 0, family: int = socket.AF_INET
    ) -> List[Dict[str, Any]]:
        """Return IP address for given hostname."""
        infos = await self.get_loop().getaddrinfo(
            hostname,
            port,
            type=socket.SOCK_STREAM,
            family=family,
            flags=socket.AI_ADDRCONFIG,
        )

        hosts = []
        for _family, _, proto, _, address in infos:
            if _family == socket.AF_INET6 and address[3]:  # pragma: no cover
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
