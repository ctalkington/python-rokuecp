"""Helpers for Roku Client."""
from __future__ import annotations

from ipaddress import ip_address
from socket import gaierror as SocketGIAError

from .exceptions import RokuConnectionError
from .resolver import ThreadedResolver


def is_ip_address(host: str) -> bool:
    """Determine if host is an IP Address.

    Args:
        host: The hostname to check.

    Returns:
        Whether the provided hostname is an IP address.
    """
    try:
        ip_address(host)
    except ValueError:
        return False

    return True


async def resolve_hostname(host: str) -> str:
    """Resolve hostname to IP Address (asynchronously).

    Args:
        host: The hostname to resolve.

    Returns:
        The resolved IP address.

    Raises:
        RokuConnectionError: An error occurred while communicating with
            the Roku device.
    """
    try:
        resolver = ThreadedResolver()
        results = await resolver.resolve(host)
        ips = [ip_address(x["host"]) for x in results]
        return str(ips[0])
    except (OSError, SocketGIAError, ValueError) as exception:
        raise RokuConnectionError(
            f"Error occurred while resolving hostname: {host}"
        ) from exception
