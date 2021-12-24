"""Tests for Roku Client Helpers."""
from ipaddress import ip_address
from socket import gaierror as SocketGIAError

import pytest
from rokuecp.exceptions import RokuConnectionError
from rokuecp.helpers import is_ip_address, resolve_hostname

from . import fake_addrinfo_results

HOSTNAME = "roku.local"
HOST = "192.168.1.2"


def test_is_ip_address() -> None:
    """Test the is_ip_address helper."""
    assert is_ip_address(HOST)
    assert not is_ip_address(HOSTNAME)


@pytest.mark.asyncio
async def test_resolve_hostname(resolver) -> None:
    """Test the resolve_hostname helper."""
    resolver.return_value = fake_addrinfo_results([HOST])

    result = await resolve_hostname(HOSTNAME)
    assert result == HOST
    ip_address(result)


@pytest.mark.asyncio
async def test_resolve_hostname_error_invalid(resolver) -> None:
    """Test the resolve_hostname helper fails properly."""
    resolver.return_value = fake_addrinfo_results(["not-an-ip"])

    with pytest.raises(RokuConnectionError):
        await resolve_hostname("error.local")


@pytest.mark.asyncio
async def test_resolve_hostname_error_not_found(resolver) -> None:
    """Test the resolve_hostname helper fails properly."""
    resolver.side_effect = SocketGIAError

    with pytest.raises(RokuConnectionError):
        await resolve_hostname("error.local")
