"""Tests for Roku Client Helpers."""
from ipaddress import ip_address
from socket import gaierror as SocketGIAError

import pytest
from rokuecp.exceptions import RokuConnectionError
from rokuecp.helpers import guess_stream_format, is_ip_address, resolve_hostname

from . import fake_addrinfo_results

HOSTNAME = "roku.local"
HOST = "192.168.1.2"


def test_guess_stream_format() -> None:
    """Test the guess_stream_format helper."""
    assert guess_stream_format("/path/media.media") is None

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
