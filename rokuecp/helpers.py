"""Helpers for Roku Client."""
from ip_address import ip_address
from socket import gaierror as SocketGIAError, gethostbyname

from .exceptions import RokuConnectionError


def is_ip_address(host: str) -> bool:
    """Determine if host is an IP Address."""
    try:
        ip_address(host)
    except ValueError:
        return False

    return True


def resolve_hostname(host: str) -> str:
    """Resolve hostname to IP Address."""
    try:
        return gethostbyname(host)
    except SocketGIAError as exception:
        raise RokuConnectionError(
            f"Error occurred while resolving hostname: {host}"
        ) from exception
