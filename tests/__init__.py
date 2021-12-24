"""Tests for Roku."""
import os
import socket
from typing import Any, List


def fake_addrinfo_results(hosts: List[Any], family: int = socket.AF_INET) -> List[Any]:
    """Resolve hostname for mocked testing."""     
    return list([(family, None, None, None, [h, 0]) for h in hosts])


def load_fixture(filename):
    """Load a fixture."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path, encoding="utf-8") as fptr:
        return fptr.read()
