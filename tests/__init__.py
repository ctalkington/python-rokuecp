"""Tests for Roku."""
import os
import socket
from typing import Any, Awaitable, Callable, List, Optional
from unittest.mock import Mock, patch


def fake_addrinfo(
    hosts: Optional[List[Any]] = None, family: int = socket.AF_INET
) -> Callable[..., Awaitable[Any]]:
    """Resolve hostname for mocked testing."""

    async def fake(
        # pylint: disable=unused-argument
        *args: Any,
        **kwargs: Any,
    ) -> List[Any]:
        """Mock the addrinfo return format."""
        if not hosts:
            raise socket.gaierror

        return list([(family, None, None, None, [h, 0]) for h in hosts])

    return fake


def fake_addrinfo_results(
    hosts: Optional[List[Any]] = None, family: int = socket.AF_INET
) -> List[Any]:
    """Resolve hostname for mocked testing."""
    return list([(family, None, None, None, [h, 0]) for h in hosts])


def load_fixture(filename):
    """Load a fixture."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path) as fptr:
        return fptr.read()


def patch_resolver_loop(hosts: Optional[List[Any]] = None):
    """Mock the threaded resolver."""
    loop = Mock()
    loop.getaddrinfo = fake_addrinfo(hosts)

    return patch("rokuecp.resolver.get_running_loop", return_value=loop)
