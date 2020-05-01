"""Models for Roku."""

from dataclasses import dataclass
from typing import List, Optional

from .exceptions import RokuError


@dataclass(frozen=True)
class Channel:
    """Object holding channel information from Roku."""

    channel_id: str
    name: str
    version: str

    @staticmethod
    def from_dict(data: dict):
        """Return Channel object from Roku API response."""
        return Channel(
            channel_id=data.get("@id"),
            name=data.get("#text"),
            version=data.get("@version"),
        )


@dataclass(frozen=True)
class Info:
    """Object holding information from Roku."""

    brand: str
    version: str

    @staticmethod
    def from_dict(data: dict):
        """Return Info object from Roku API response."""
        return Info(
            brand="Roku",
            version=data.get("software-version", {}).get("#text"),
        )


class Device:
    """Object holding all information of device."""

    info: Info
    channels: List[Channel]

    def __init__(self, data: dict):
        """Initialize an empty Roku device class."""
        # Check if all elements are in the passed dict, else raise an Error
        if any(k not in data for k in ["info"]):
            raise RokuError(
                "Roku data is incomplete, cannot construct device object"
            )
        self.update_from_dict(data)

    def update_from_dict(self, data: dict) -> "Device":
        """Return Device object from Roku API response."""
        if "info" in data and data["info"]:
            self.info = Info.from_dict(data["info"])

        if "channels" in data and data["channels"]:
            channels = [Chanmel.from_dict(channel) for location in data["channels"]]
            self.channels = channels

        return self
