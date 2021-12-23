"""Setup pytest."""
from unittest.mock import Mock, patch

import pytest

from .async_mock import AsyncMock

@pytest.fixture(name="resolver")
def resolver_fixture():
    """Mock the threaded resolver."""
    resolver = AsyncMock(return_value=[])
    loop = Mock()
    loop.getaddrinfo = resolver

    with patch("rokuecp.resolver.get_running_loop", return_value=loop):
        yield resolver
