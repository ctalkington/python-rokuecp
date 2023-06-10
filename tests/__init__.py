"""Tests for Roku."""
import os
import socket


def fake_addrinfo_results(hosts: list, family: int = socket.AF_INET) -> list:
    """Resolve hostname for mocked testing."""
    return [(family, None, None, None, [h, 0]) for h in hosts]


def load_fixture(filename: str) -> str:
    """Load a fixture."""
    path = os.path.join(  # noqa: PTH118
        os.path.dirname(__file__),  # noqa: PTH120
        "fixtures",
        filename,
    )
    with open(path, encoding="utf-8") as fptr:  # noqa: PTH123
        return fptr.read()
