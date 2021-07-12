"""Tests for Roku Client Helpers."""
from socket import gaierror as SocketGIAError

import mock
import pytest
from rokuecp import RokuConnectionError
from rokuecp.helpers import is_ip_address, resolve_hostname

HOSTNAME = "roku.local"
HOST = "192.168.1.2"


def test_is_ip_address() -> None:
    """Test the is_ip_address helper."""
    assert is_ip_address(HOST)
    assert not is_ip_address(HOSTNAME)


def test_resolve_hostname() -> None:
    """Test the resolve_hostname helper."""
    with mock.patch(
        "rokuecp.helpers.gethostbyname", return_value=HOST
    ) as mock_gethostbyname:
        assert resolve_hostname(HOSTNAME) == HOST
        assert len(mock_gethostbyname.mock_calls) == 1

    with pytest.raises(RokuConnectionError):
        with mock.patch(
            "rokuecp.helpers.gethostbyname", side_effect=SocketGIAError()
        ):
            resolve_hostname(HOSTNAME)
