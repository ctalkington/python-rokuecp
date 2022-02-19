"""Helpers for Roku Client."""
from __future__ import annotations

import mimetypes
from ipaddress import ip_address
from socket import gaierror as SocketGIAError

import yarl

from .exceptions import RokuConnectionError
from .resolver import ThreadedResolver

MIME_TO_STREAM_FORMAT = {
    "application/dash+xml": "dash",
    "application/x-mpegURL": "hls",
    "application/vnd.apple.mpegurl": "hls",
    "audio/mpeg": "mp3",
    "audio/x-ms-wma": "wma",
    "video/mp4": "mp4",
    "video/quicktime": "mp4",
    "video/x-matroska": "mkv",
}


def guess_stream_format(  # pylint: disable=too-many-return-statements
    url: str, mime_type: str | None = None
) -> str | None:
    """Guess the Roku stream format for a given URL and MIME type.

    Args:
        url: The URL to determine stream format for.
        mime_type: The MIME type to aid in stream format determination.

    Returns:
        The stream format or None if unable to determine stream format.
    """
    parsed = yarl.URL(url)
    parsed_name = parsed.name.lower()

    if mime_type is None:
        mime_type, _ = mimetypes.guess_type(parsed.path)

    if mime_type == "audio/mpeg" and parsed_name.endswith(".m4a"):
        return "m4a"

    if mime_type is None:
        if parsed_name.endswith(".dash"):
            return "dash"
        if parsed_name.endswith(".mpd"):
            return "dash"
        if parsed_name.endswith(".m4v"):
            return "mp4"
        if parsed_name.endswith(".mks"):
            return "mks"
        if parsed_name.endswith(".mka"):
            return "mka"
        if ".ism/manifest" in parsed.path.lower():
            return "ism"

    if mime_type is None:
        return None

    if mime_type not in MIME_TO_STREAM_FORMAT:
        return None

    return MIME_TO_STREAM_FORMAT[mime_type]


def is_ip_address(host: str) -> bool:
    """Determine if host is an IP Address.

    Args:
        host: The hostname to check.

    Returns:
        Whether the provided hostname is an IP address.
    """
    try:
        ip_address(host)
    except ValueError:
        return False

    return True


async def resolve_hostname(host: str) -> str:
    """Resolve hostname to IP Address (asynchronously).

    Args:
        host: The hostname to resolve.

    Returns:
        The resolved IP address.

    Raises:
        RokuConnectionError: An error occurred while communicating with
            the Roku device.
    """
    try:
        resolver = ThreadedResolver()
        results = await resolver.resolve(host)
        ips = [ip_address(x["host"]) for x in results]
        return str(ips[0])
    except (OSError, SocketGIAError, ValueError) as exception:
        raise RokuConnectionError(
            f"Error occurred while resolving hostname: {host}"
        ) from exception
