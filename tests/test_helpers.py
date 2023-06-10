"""Tests for Roku Client Helpers."""
from ipaddress import ip_address
from socket import gaierror
from unittest.mock import AsyncMock

import pytest

from rokuecp.exceptions import RokuConnectionError
from rokuecp.helpers import (
    determine_device_name,
    guess_stream_format,
    is_ip_address,
    resolve_hostname,
)

from . import fake_addrinfo_results

HOSTNAME = "roku.local"
HOST = "192.168.1.2"


def test_determine_device_name() -> None:
    """Test the determine_device_name helper."""
    brand = "Brand"
    assert determine_device_name("", None, None, None) == "Roku (Unknown Name)"
    assert determine_device_name(brand, None, None, None) == "Brand"
    assert determine_device_name(brand, "Friendly Name", None, None) == "Friendly Name"
    assert determine_device_name(brand, None, "Default Name", None) == "Default Name"
    assert determine_device_name(brand, None, None, "Model Name") == "Brand Model Name"


def test_guess_stream_format() -> None:
    """Test the guess_stream_format helper."""
    assert guess_stream_format("/path/media.media") is None
    assert guess_stream_format("/path/media.txt") is None

    assert guess_stream_format("/path/media.mp4", "video/mp4") == "mp4"
    assert guess_stream_format("/path/media.mp4") == "mp4"
    assert guess_stream_format("/path/media.m4v") == "mp4"
    assert guess_stream_format("/path/media.mov") == "mp4"
    assert guess_stream_format("/path/media.mkv") == "mkv"
    assert guess_stream_format("/path/media.mks") == "mks"
    assert guess_stream_format("/path/media.m3u8") == "hls"
    assert guess_stream_format("/path/media.dash") == "dash"
    assert guess_stream_format("/path/media.mpd") == "dash"
    assert guess_stream_format("/path/media.ism/manifest") == "ism"

    assert guess_stream_format("/path/media.mp3") == "mp3"
    assert guess_stream_format("/path/media.m4a") == "m4a"
    assert guess_stream_format("/path/media.mka") == "mka"
    assert guess_stream_format("/path/media.wma") == "wma"


def test_is_ip_address() -> None:
    """Test the is_ip_address helper."""
    assert is_ip_address(HOST)
    assert not is_ip_address(HOSTNAME)


@pytest.mark.asyncio
async def test_resolve_hostname(resolver: AsyncMock) -> None:
    """Test the resolve_hostname helper."""
    resolver.return_value = fake_addrinfo_results([HOST])

    result = await resolve_hostname(HOSTNAME)
    assert result == HOST
    ip_address(result)


@pytest.mark.asyncio
async def test_resolve_hostname_error_invalid(resolver: AsyncMock) -> None:
    """Test the resolve_hostname helper fails properly."""
    resolver.return_value = fake_addrinfo_results(["not-an-ip"])

    with pytest.raises(RokuConnectionError):
        await resolve_hostname("error.local")


@pytest.mark.asyncio
async def test_resolve_hostname_error_not_found(resolver: AsyncMock) -> None:
    """Test the resolve_hostname helper fails properly."""
    resolver.side_effect = gaierror

    with pytest.raises(RokuConnectionError):
        await resolve_hostname("error.local")
