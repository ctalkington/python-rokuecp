"""Models for Roku."""

from dataclasses import dataclass
from datetime import datetime
from math import floor
from typing import List, Optional

from .exceptions import RokuError


def _ms_to_sec(ms: str) -> int:
    """Convert millisecond string to seconds integer."""
    msi = int(ms.replace("ms", "").strip())
    return floor(msi / 1000)


@dataclass(frozen=True)
class Application:
    """Object holding application information from Roku."""

    app_id: str
    name: str
    version: str
    screensaver: bool

    @staticmethod
    def from_dict(data: dict):
        """Return Application object from Roku API response."""
        if "app" in data:
            app = data["app"]
        else:
            app = data

        if isinstance(app, str):
            app = {"#text": app}

        return Application(
            app_id=app.get("@id", None),
            name=app.get("#text", None),
            version=app.get("@version", None),
            screensaver=data.get("screensaver") is not None,
        )


@dataclass(frozen=True)
class Info:
    """Object holding device information from Roku."""

    name: str
    brand: str
    device_type: str
    model_name: str
    model_number: str
    serial_number: str
    version: str
    network_type: Optional[str] = None
    network_name: Optional[str] = None
    ethernet_support: Optional[bool] = None
    ethernet_mac: Optional[str] = None
    wifi_mac: Optional[str] = None
    supports_private_listening: Optional[bool] = None
    headphones_connected: Optional[bool] = None

    @staticmethod
    def from_dict(data: dict):
        """Return Info object from Roku API response."""
        device_type = "box"

        if data.get("is-tv", "false") == "true":
            device_type = "tv"
        elif data.get("is-stick", "false") == "true":
            device_type = "stick"

        private_listening = data.get("supports-private-listening", "false") == "true"

        return Info(
            name=data.get("user-device-name", None),
            brand=data.get("vendor-name", "Roku"),
            device_type=device_type,
            model_name=data.get("model-name", None),
            model_number=data.get("model-number", None),
            network_type=data.get("network-type", None),
            network_name=data.get("network-name", None),
            serial_number=data.get("serial-number", None),
            version=data.get("software-version", None),
            ethernet_support=data.get("supports-ethernet", "false") == "true",
            ethernet_mac=data.get("ethernet-mac", None),
            wifi_mac=data.get("wifi-mac", None),
            supports_private_listening=private_listening,
            headphones_connected=data.get("headphones-connected", "false") == "true",
        )


@dataclass(frozen=True)
class Channel:
    """Object holding all information of TV Channel."""

    name: str
    number: str
    channel_type: str
    hidden: bool
    program_title: Optional[str] = None
    program_description: Optional[str] = None
    program_rating: Optional[str] = None
    signal_mode: Optional[str] = None
    signal_strength: Optional[int] = None

    @staticmethod
    def from_dict(data: dict):
        """Return Channel object from Roku response."""
        strength = data.get("signal-strength", None)

        return Channel(
            name=data.get("name", None),
            number=data.get("number", None),
            channel_type=data.get("type", "unknown"),
            hidden=data.get("user-hidden", "false") == "true",
            program_title=data.get("program-title", None),
            program_description=data.get("program-description", None),
            program_rating=data.get("program-ratings", None),
            signal_mode=data.get("signal-mode", None),
            signal_strength=int(strength) if strength is not None else None,
        )


@dataclass(frozen=True)
class MediaState:
    """Object holding all information of media state."""

    duration: int
    live: bool
    paused: bool
    position: int
    at: datetime = datetime.utcnow()

    @staticmethod
    def from_dict(data: dict):
        """Return MediaStste object from Roku response."""
        state = data.get("@state", None)
        if state not in ("play", "pause"):
            return None

        duration = data.get("duration", "0")
        position = data.get("position", "0")

        return MediaState(
            live=data.get("is_live", "false") == "true",
            paused=state == "pause",
            duration=_ms_to_sec(duration),
            position=_ms_to_sec(position),
        )


@dataclass(frozen=True)
class State:
    """Object holding all information of device state."""

    available: bool
    standby: bool
    at: datetime = datetime.utcnow()


class Device:
    """Object holding all information of device."""

    info: Info
    state: State
    apps: Optional[List[Application]] = []
    channels: Optional[List[Channel]] = []
    app: Optional[Application] = None
    channel: Optional[Channel] = None
    media: Optional[MediaState] = None

    def __init__(self, data: dict):
        """Initialize an empty Roku device class."""
        # Check if all elements are in the passed dict, else raise an Error
        if any(k not in data for k in ["info", "available", "standby"]):
            raise RokuError("Roku data is incomplete, cannot construct device object")

        self.update_from_dict(data)

    def update_from_dict(self, data: dict, update_state: bool = True) -> "Device":
        """Return Device object from Roku API response."""
        if update_state:
            self.state = State(
                available=data.get("available", False),
                standby=data.get("standby", False),
            )

        if "info" in data and data["info"]:
            self.info = Info.from_dict(data["info"])

        if "apps" in data and data["apps"]:
            self.apps = [
                Application.from_dict(app_data)
                for app_data in data["apps"]
                if data["apps"] is not None
            ]

        if "channels" in data and data["channels"]:
            self.channels = [
                Channel.from_dict(channel_data)
                for channel_data in data["channels"]
                if data["channels"] is not None
            ]

        if "app" in data and data["app"]:
            self.app = Application.from_dict(data["app"])
        elif "app" in data:
            self.app = None

        if "channel" in data and data["channel"]:
            self.channel = Channel.from_dict(data["channel"])
        elif "channel" in data:
            self.channel = None

        if "media" in data and data["media"]:
            self.media = MediaState.from_dict(data["media"])
        elif "media" in data:
            self.media = None

        return self
