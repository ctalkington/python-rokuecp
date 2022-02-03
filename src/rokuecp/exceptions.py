"""Exceptions for Roku."""


class RokuError(Exception):
    """Generic Roku exception."""

    pass


class RokuConnectionError(RokuError):
    """Roku connection exception."""

    pass
