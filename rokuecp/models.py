"""Models for Roku."""

from dataclasses import dataclass
from typing import List

from .exceptions import RokuError


@dataclass(frozen=True)
class Application:
    """Object holding application information from Roku."""

    app_id: str
    name: str
    version: str

    @staticmethod
    def from_dict(data: dict):
        """Return Application object from Roku API response."""
        return Application(
            app_id=data.get("@id", None),
            name=data.get("#text", None),
            version=data.get("@version", None),
        )


@dataclass(frozen=True)
class Info:
    """Object holding device information from Roku."""

    name: str
    brand: str
    model_name: str
    model_number: str
    serial_number: str
    version: str

    @staticmethod
    def from_dict(data: dict):
        """Return Info object from Roku API response."""
        return Info(
            name=data.get("user-device-name", None),
            brand=data.get("vendor-name", "Roku"),
            model_name=data.get("model-name", None),
            model_number=data.get("model-number", None),
            serial_number=data.get("serial-number", None),
            version=data.get("software-version", None),
        )


class Device:
    """Object holding all information of device."""

    info: Info
    apps: List[Application]

    def __init__(self, data: dict):
        """Initialize an empty Roku device class."""
        # Check if all elements are in the passed dict, else raise an Error
        if any(k not in data for k in ["info"]):
            raise RokuError("Roku data is incomplete, cannot construct device object")

        self.update_from_dict(data)

    def update_from_dict(self, data: dict) -> "Device":
        """Return Device object from Roku API response."""
        if "info" in data and data["info"]:
            self.info = Info.from_dict(data["info"])

        if "apps" in data and data["apps"]:
            apps = [Application.from_dict(app_data) for app_data in data["apps"]]
            self.apps = apps

        return self
