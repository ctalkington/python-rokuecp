"""Tests for Roku Helpers."""
import pytest
from rokuecp import RokuConnectionError

from .helpers import is_ip_address, resolve_hostname


def test_is_ip_address() -> None:
    """Test the is_ip_address helper."""
    assert is_ip_address("192.168.1.2")
    assert not is_ip_address("roku.local")


def test_resolve_hostname() -> None:
    """Test the resolve_hostname helper."""
    assert resolve_hostname("roku.local") == "192.168.1.2"
