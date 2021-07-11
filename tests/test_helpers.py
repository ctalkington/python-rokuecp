"""Tests for Roku Client Helpers."""
from socket import gaierror as SocketGIAError

import pytest
from rokuecp import RokuConnectionError
from rokuecp.helpers import is_ip_address, resolve_hostname

MOCK_HOSTNAME = "roku.local"
MOCK_HOST = "192.168.1.2"


def test_is_ip_address() -> None:
    """Test the is_ip_address helper."""
    assert is_ip_address(MOCK_HOST)
    assert not is_ip_address("roku.local")


def test_resolve_hostname() -> None:
    """Test the resolve_hostname helper."""
    with pytest.mock.patch(
        "rokuecp.helpers.gethostbyname", return_value=MOCK_HOST
    ) as mock_gethostbyname:
        assert resolve_hostname(MOCK_HOSTNAME) == MOCK_HOST
        assert len(mock_gethostbyname.mock_calls) == 1
          
    with pytest.raises(RokuConnectionError):
        with pytest.mock.patch(
            "rokuecp.helpers.gethostbyname", side_effect=SocketGIAError()
        ):
            resolve_hostname(MOCK_HOSTNAME)

