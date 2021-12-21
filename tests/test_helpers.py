"""Tests for Roku Client Helpers."""
from ipaddress import ip_address

import pytest

from rokuecp.exceptions import RokuConnectionError
from rokuecp.helpers import is_ip_address, resolve_hostname

from . import patch_resolver_loop

HOSTNAME = "roku.local"
HOST = "192.168.1.2"


def test_is_ip_address() -> None:
    """Test the is_ip_address helper."""
    assert is_ip_address(HOST)
    assert not is_ip_address(HOSTNAME)


@pytest.mark.asyncio
async def test_resolve_hostname() -> None:
    """Test the resolve_hostname helper."""
    with patch_resolver_loop([HOST]):
        result = await resolve_hostname(HOSTNAME)
        assert result == HOST
        ip_address(result)


@pytest.mark.asyncio
async def test_resolve_hostname_error_invalid() -> None:
    """Test the resolve_hostname helper fails properly."""
    with pytest.raises(RokuConnectionError), patch_resolver_loop(["not-an-ip"]):
        await resolve_hostname("error.local")


@pytest.mark.asyncio
async def test_resolve_hostname_error_not_found() -> None:
    """Test the resolve_hostname helper fails properly."""
    with pytest.raises(RokuConnectionError), patch_resolver_loop():
        await resolve_hostname("error.local")
