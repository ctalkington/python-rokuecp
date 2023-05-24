"""Models for Roku."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from math import floor
from typing import Any

from .exceptions import RokuError
from .helpers import determine_device_name


def _ms_to_sec(msec: str) -> int:
    """Convert millisecond string to seconds integer.

    Args:
        msec: The number of milliseconds as a string.

    Returns:
        The number of seconds converted from milliseconds.
    """
    msi = int(msec.replace("ms", "").strip())
    return floor(msi / 1000)


@dataclass
class Application:
    """Object holding application information from Roku."""

    app_id: str | None
    name: str | None
    version: str | None
    screensaver: bool

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Application:
        """Return Application object from Roku API response.

        Args:
            data: Dictionary of data.

        Returns:
            The Application object.
        """
        app = data.get("app", data)

        if isinstance(app, str):
            app = {"#text": app}

        return Application(
            app_id=app.get("@id", None),
            name=app.get("#text", None),
            version=app.get("@version", None),
            screensaver=data.get("screensaver") is not None,
        )


@dataclass
class Info:
    """Object holding device information from Roku."""

    name: str | None
    brand: str
    device_type: str
    device_location: str | None
    model_name: str | None
    model_number: str | None
    serial_number: str | None
    version: str | None
    network_type: str | None = None
    network_name: str | None = None
    ethernet_support: bool | None = None
    ethernet_mac: str | None = None
    wifi_mac: str | None = None
    supports_airplay: bool | None = None
    supports_find_remote: bool | None = None
    supports_private_listening: bool | None = None
    supports_wake_on_wlan: bool | None = None
    headphones_connected: bool | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Info:
        """Return Info object from Roku API response.

        Args:
            data: Dictionary of data.

        Returns:
            The Info object.
        """
        device_type = "box"

        if data.get("is-tv", "false") == "true":
            device_type = "tv"
        elif data.get("is-stick", "false") == "true":
            device_type = "stick"

        device_name = data.get("user-device-name", None)
        model_name = data.get("model-name", None)
        brand = data.get("vendor-name", "Roku")

        if device_name is None or not device_name.strip():
            friendly_device_name = data.get("friendly-device-name", None)
            default_device_name = data.get("default-device-name", None)
            device_name = determine_device_name(
                brand, friendly_device_name, default_device_name, model_name
            )

        airplay = data.get("supports-airplay", "false") == "true"
        find_remote = data.get("supports-find-remote", "false") == "true"
        private_listening = data.get("supports-private-listening", "false") == "true"

        return Info(
            name=device_name,
            brand=brand,
            device_type=device_type,
            device_location=data.get("user-device-location", None),
            model_name=model_name,
            model_number=data.get("model-number", None),
            network_type=data.get("network-type", None),
            network_name=data.get("network-name", None),
            serial_number=data.get("serial-number", None),
            version=data.get("software-version", None),
            ethernet_support=data.get("supports-ethernet", "false") == "true",
            ethernet_mac=data.get("ethernet-mac", None),
            wifi_mac=data.get("wifi-mac", None),
            supports_airplay=airplay,
            supports_find_remote=find_remote,
            supports_private_listening=private_listening,
            supports_wake_on_wlan=data.get("supports-wake-on-wlan", "false") == "true",
            headphones_connected=data.get("headphones-connected", "false") == "true",
        )


@dataclass
class Channel:
    """Object holding all information of TV Channel."""

    name: str | None
    number: str
    channel_type: str
    hidden: bool
    program_title: str | None = None
    program_description: str | None = None
    program_rating: str | None = None
    signal_mode: str | None = None
    signal_strength: int | None = None

    @staticmethod
    def from_dict(data: dict) -> Channel:
        """Return Channel object from Roku response.

        Args:
            data: Dictionary of data.

        Returns:
            The Channel object.
        """
        if (strength := data.get("signal-strength", None)) is not None:
            try:
                strength = int(strength)
            except ValueError:
                strength = None

        return Channel(
            name=data.get("name", None),
            number=data.get("number", "0"),
            channel_type=data.get("type", "unknown"),
            hidden=data.get("user-hidden", "false") == "true",
            program_title=data.get("program-title", None),
            program_description=data.get("program-description", None),
            program_rating=data.get("program-ratings", None),
            signal_mode=data.get("signal-mode", None),
            signal_strength=strength,
        )


@dataclass
class MediaState:
    """Object holding all information of media state."""

    duration: int
    live: bool
    paused: bool
    position: int
    at: datetime = datetime.utcnow()  # pylint: disable=C0103

    @staticmethod
    def from_dict(data: dict) -> MediaState | None:
        """Return MediaStste object from Roku response.

        Args:
            data: Dictionary of data.

        Returns:
            The MediaState object.
        """
        if (state := data.get("@state", None)) not in ("play", "pause"):
            return None

        duration = data.get("duration", "0")
        position = data.get("position", "0")

        return MediaState(
            live=data.get("is_live", "false") == "true",
            paused=state == "pause",
            duration=_ms_to_sec(duration),
            position=_ms_to_sec(position),
        )


@dataclass
class State:
    """Object holding all information of device state."""

    available: bool
    standby: bool
    at: datetime = datetime.utcnow()  # pylint: disable=C0103


class Device:
    """Object holding all information of device."""

    info: Info
    state: State
    apps: list[Application] = []
    channels: list[Channel] = []
    app: Application | None = None
    channel: Channel | None = None
    media: MediaState | None = None

    def __init__(self, data: dict[str, Any]):
        """Initialize an empty Roku device class.

        Args:
            data: Dictionary of data.

        Raises:
            RokuError: Received an unexpected response from the Roku device.
        """
        # Check if all elements are in the passed dict, else raise an Error
        if any(k not in data for k in ("info", "available", "standby")):
            raise RokuError("Roku data is incomplete, cannot construct device object")

        self.update_from_dict(data)

    def as_dict(self) -> dict[str, Any]:
        """Return dictionary version of the Roku device.

        Returns:
            A Python dictionary created from the Device object attributes.
        """
        apps = None
        if self.apps is not None:
            apps = [asdict(app) for app in self.apps]

        channels = None
        if self.channels is not None:
            channels = [asdict(channel) for channel in self.channels]

        app = None
        if self.app is not None:
            app = asdict(self.app)

        channel = None
        if self.channel is not None:
            channel = asdict(self.channel)

        media = None
        if self.media is not None:
            media = asdict(self.media)

        return {
            "info": asdict(self.info),
            "state": asdict(self.state),
            "apps": apps,
            "channels": channels,
            "app": app,
            "channel": channel,
            "media": media,
        }

    def update_from_dict(
        self, data: dict[str, Any], update_state: bool = True
    ) -> Device:
        """Return Device object from Roku device data.

        Args:
            data: Dictionary of data.
            update_state: Whether to update state attributes.

        Returns:
            The Device object.
        """
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
