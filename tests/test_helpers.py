"""Tests for Roku Client Helpers."""
import pytest

from rokuecp import RokuConnectionError
from rokuecp.helpers import is_ip_address, resolve_hostname

MOCK_HOSTNAME = "192.168.1.2"


def test_is_ip_address() -> None:
    """Test the is_ip_address helper."""
    assert is_ip_address("192.168.1.2")
    assert not is_ip_address("roku.local")


def test_resolve_hostname() -> None:
    """Test the resolve_hostname helper."""
    with patch(
        "rokuecp.helpers.gethostbyname", return_value=MOCK_HOSTNAME
    ) as mock_gethostbyname:
        assert resolve_hostname("roku.local") == MOCK_HOSTNAME
        assert len(mock_gethostbyname.mock_calls) == 1
          
    with pytest.raises(RokuConnectionError):
        resolve_hostname("roku.local")

