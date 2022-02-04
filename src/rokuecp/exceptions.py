"""Exceptions for Roku."""


class RokuError(Exception):
    """Generic Roku exception."""


class RokuConnectionError(RokuError):
    """Roku connection exception."""
