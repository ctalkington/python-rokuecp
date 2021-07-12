"""Tests for Roku Models."""
from datetime import datetime
from typing import List

import pytest
import rokuecp.models as models
import xmltodict
from rokuecp import RokuError

from . import load_fixture

ACTIVE_APP_NETFLIX = xmltodict.parse(load_fixture("active-app-netflix.xml"))
ACTIVE_APP_PLUTO = xmltodict.parse(load_fixture("active-app-pluto.xml"))
ACTIVE_APP_TV = xmltodict.parse(load_fixture("active-app-tvinput-dtv.xml"))
APPS = xmltodict.parse(load_fixture("apps.xml"))
APPS_TV = xmltodict.parse(load_fixture("apps-tv.xml"))
DEVICE_INFO = xmltodict.parse(load_fixture("device-info.xml"))
DEVICE_INFO_STICK = xmltodict.parse(load_fixture("device-info-stick.xml"))
DEVICE_INFO_TV = xmltodict.parse(load_fixture("device-info-tv.xml"))
MEDIA_PLAYER_CLOSE = xmltodict.parse(load_fixture("media-player-close.xml"))
MEDIA_PLAYER_PLUTO_LIVE = xmltodict.parse(load_fixture("media-player-pluto-live.xml"))
MEDIA_PLAYER_PLUTO_PAUSE = xmltodict.parse(load_fixture("media-player-pluto-pause.xml"))
MEDIA_PLAYER_PLUTO_PLAY = xmltodict.parse(load_fixture("media-player-pluto-play.xml"))
TV_ACTIVE_CHANNEL = xmltodict.parse(load_fixture("tv-active-channel.xml"))
TV_CHANNELS = xmltodict.parse(load_fixture("tv-channels.xml"))

DEVICE = {
    "info": DEVICE_INFO["device-info"],
    "apps": APPS["apps"]["app"],
    "app": ACTIVE_APP_PLUTO["active-app"],
    "media": MEDIA_PLAYER_PLUTO_PLAY["player"],
    "available": True,
    "standby": False,
}

DEVICE_TV = {
    "info": DEVICE_INFO_TV["device-info"],
    "apps": APPS_TV["apps"]["app"],
    "app": ACTIVE_APP_TV["active-app"],
    "channels": TV_CHANNELS["tv-channels"]["channel"],
    "channel": TV_ACTIVE_CHANNEL["tv-channel"]["channel"],
    "available": True,
    "standby": False,
}


def test_device() -> None:
    """Test the Device model."""
    device = models.Device(DEVICE)

    assert device

    assert device.info
    assert isinstance(device.info, models.Info)

    assert device.state
    assert isinstance(device.state, models.State)

    assert device.apps
    assert isinstance(device.apps, List)

    assert device.app
    assert isinstance(device.app, models.Application)

    assert device.media
    assert isinstance(device.media, models.MediaState)

    assert isinstance(device.channels, List)
    assert len(device.channels) == 0

    assert device.channel is None


def test_device_no_data() -> None:
    """Test the Device model with no device info."""
    with pytest.raises(RokuError):
        models.Device({})


def test_device_tv() -> None:
    """Test the Device model with Roku TV."""
    device = models.Device(DEVICE_TV)

    assert device

    assert device.info
    assert isinstance(device.info, models.Info)

    assert device.state
    assert isinstance(device.state, models.State)

    assert device.apps
    assert isinstance(device.apps, List)

    assert device.app
    assert isinstance(device.app, models.Application)
    assert device.app.app_id == "tvinput.dtv"

    assert device.media is None

    assert isinstance(device.channels, List)
    assert len(device.channels) == 2

    assert isinstance(device.channel, models.Channel)


def test_info() -> None:
    """Test the Info model."""
    info = models.Info.from_dict(DEVICE_INFO["device-info"])

    assert info
    assert info.name == "My Roku 3"
    assert info.brand == "Roku"
    assert info.device_location is None
    assert info.device_type == "box"
    assert info.network_type == "ethernet"
    assert info.network_name is None
    assert info.model_name == "Roku 3"
    assert info.model_number == "4200X"
    assert info.serial_number == "1GU48T017973"
    assert info.ethernet_support
    assert info.ethernet_mac == "b0:a7:37:96:4d:fa"
    assert info.wifi_mac == "b0:a7:37:96:4d:fb"
    assert not info.supports_private_listening
    assert not info.headphones_connected
    assert info.version == "7.5.0"


def test_info_stick() -> None:
    """Test the Info model with Roku Stick."""
    info = models.Info.from_dict(DEVICE_INFO_STICK["device-info"])

    assert info
    assert info.name == "My Roku Stick"
    assert info.brand == "Roku"
    assert info.device_location is None
    assert info.device_type == "stick"
    assert info.network_type == "wifi"
    assert info.network_name == "NetworkSSID"
    assert info.model_name == "Roku Stick"
    assert info.model_number == "3500X"
    assert info.serial_number == "2L647N055555"
    assert not info.ethernet_support
    assert info.ethernet_mac is None
    assert info.wifi_mac == "b0:a7:37:6a:ec:2d"
    assert not info.supports_private_listening
    assert not info.headphones_connected
    assert info.version == "10.0.0"


def test_info_tv() -> None:
    """Test the Info model with TV."""
    info = models.Info.from_dict(DEVICE_INFO_TV["device-info"])

    assert info
    assert info.name == '58" Onn Roku TV'
    assert info.brand == "Onn"
    assert info.device_location == "Living room"
    assert info.device_type == "tv"
    assert info.network_type == "wifi"
    assert info.network_name == "NetworkSSID"
    assert info.model_name == "100005844"
    assert info.model_number == "7820X"
    assert info.serial_number == "YN00H5555555"
    assert info.ethernet_support
    assert info.ethernet_mac == "d4:3a:2e:07:fd:cb"
    assert info.wifi_mac == "d8:13:99:f8:b0:c6"
    assert info.supports_private_listening
    assert not info.headphones_connected
    assert info.version == "9.2.0"


def test_application() -> None:
    """Test the Application model."""
    app = models.Application.from_dict(APPS["apps"]["app"][0])

    assert app
    assert app.app_id == "11"
    assert app.name == "Roku Channel Store"


def test_application_active_app() -> None:
    """Test the Application model with active app."""
    app = models.Application.from_dict(ACTIVE_APP_NETFLIX["active-app"])

    assert app
    assert app.app_id == "12"
    assert app.name == "Netflix"
    assert app.version == "4.1.218"


def test_channel() -> None:
    """Test the Channel model."""
    channel = models.Channel.from_dict(TV_CHANNELS["tv-channels"]["channel"][0])

    assert channel
    assert channel.name == "WhatsOn"
    assert channel.number == "1.1"
    assert channel.channel_type == "air-digital"
    assert not channel.hidden
    assert channel.program_title is None
    assert channel.program_description is None
    assert channel.program_rating is None
    assert channel.signal_mode is None
    assert channel.signal_strength is None


def test_channel_active_tv() -> None:
    """Test the Channel model with active TV channel."""
    channel = models.Channel.from_dict(TV_ACTIVE_CHANNEL["tv-channel"]["channel"])
    description = """The team will travel all around the world in order to shut down
a global crime ring."""

    assert channel
    assert channel.name == "getTV"
    assert channel.number == "14.3"
    assert channel.channel_type == "air-digital"
    assert not channel.hidden
    assert channel.program_title == "Airwolf"
    assert channel.program_description == description.replace("\n", " ")
    assert channel.program_rating == "TV-14-D-V"
    assert channel.signal_mode == "480i"
    assert channel.signal_strength == -75


def test_channel_active_tv_signal_stength_non_numeric() -> None:
    """Test the Channel model with active TV channel and non-numeric signal strength."""
    active_channel = {
        **TV_ACTIVE_CHANNEL["tv-channel"]["channel"],
        "signal-strength": "n/a",
    }

    channel = models.Channel.from_dict(active_channel)
    description = """The team will travel all around the world in order to shut down
a global crime ring."""

    assert channel
    assert channel.name == "getTV"
    assert channel.number == "14.3"
    assert channel.channel_type == "air-digital"
    assert not channel.hidden
    assert channel.program_title == "Airwolf"
    assert channel.program_description == description.replace("\n", " ")
    assert channel.program_rating == "TV-14-D-V"
    assert channel.signal_mode == "480i"
    assert channel.signal_strength is None


def test_media_state_close() -> None:
    """Test the MediaState model with closed media."""
    state = models.MediaState.from_dict(MEDIA_PLAYER_CLOSE["player"])

    assert state is None


def test_media_state_live() -> None:
    """Test the MediaState model with live media."""
    state = models.MediaState.from_dict(MEDIA_PLAYER_PLUTO_LIVE["player"])

    assert state
    assert isinstance(state.at, datetime)

    assert not state.paused
    assert state.live
    assert state.duration == 95
    assert state.position == 73


def test_media_state_pause() -> None:
    """Test the MediaState model with paused media."""
    state = models.MediaState.from_dict(MEDIA_PLAYER_PLUTO_PAUSE["player"])

    assert state
    assert isinstance(state.at, datetime)

    assert state.paused
    assert not state.live
    assert state.duration == 6496
    assert state.position == 313


def test_media_state_play() -> None:
    """Test the MediaState model with playing media."""
    state = models.MediaState.from_dict(MEDIA_PLAYER_PLUTO_PLAY["player"])

    assert state
    assert isinstance(state.at, datetime)

    assert not state.paused
    assert not state.live
    assert state.duration == 6496
    assert state.position == 38


def test_state() -> None:
    """Test the State model."""
    state = models.State(available=True, standby=False)

    assert state
    assert isinstance(state.at, datetime)
