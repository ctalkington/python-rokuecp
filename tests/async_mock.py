"""Mock utilities that are async aware."""
# pylint: disable-all
import sys

if sys.version_info[:2] < (3, 8):
    from asynctest.mock import *  # noqa

    AsyncMock = CoroutineMock  # type: ignore # noqa
else:
    from unittest.mock import *  # noqa
