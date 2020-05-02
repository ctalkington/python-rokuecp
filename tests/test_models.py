"""Tests for Roku Models."""
from datetime import datetime

import pytest
import rokuecp.models as models
import xmltodict
from rokuecp import RokuError

from . import load_fixture

ACTIVE_APP_NETFLIX = xmltodict.parse(load_fixture("active-app-netflix.xml"))
APPS = xmltodict.parse(load_fixture("apps.xml"))
DEVICE_INFO = xmltodict.parse(load_fixture("device-info.xml"))
DEVICE_INFO_TV = xmltodict.parse(load_fixture("device-info-tv.xml"))
TV_ACTIVE_CHANNEL = xmltodict.parse(load_fixture("tv-active-channel.xml"))
TV_CHANNELS = xmltodict.parse(load_fixture("tv-channels.xml"))

DEVICE = {
    "info": DEVICE_INFO["device-info"],
    "apps": APPS["apps"]["app"],
    "app": ACTIVE_APP_NETFLIX,
    "available": True,
    "standby": False,
}


def test_device() -> None:
    """Test the Device model."""
    device = models.Device(DEVICE)

    assert device

    assert device.info
    assert isinstance(device.info, models.Info)


def test_device_no_data() -> None:
    """Test the Device model."""
    with pytest.raises(RokuError):
        models.Device({})


def test_info() -> None:
    """Test the Info model."""
    info = models.Info.from_dict(DEVICE_INFO["device-info"])

    assert info
    assert info.name == "My Roku 3"
    assert info.brand == "Roku"
    assert info.device_type == "box"
    assert info.model_name == "Roku 3"
    assert info.model_number == "4200X"
    assert info.serial_number == "1GU48T017973"
    assert info.version == "7.5.0"


def test_info_tv() -> None:
    """Test the Info model."""
    info = models.Info.from_dict(DEVICE_INFO_TV["device-info"])

    assert info
    assert info.name == '58" Onn Roku TV'
    assert info.brand == "Onn"
    assert info.device_type == "tv"
    assert info.model_name == "100005844"
    assert info.model_number == "7820X"
    assert info.serial_number == "YN00H5555555"
    assert info.version == "9.2.0"


def test_application() -> None:
    """Test the Application model."""
    app = models.Application.from_dict(APPS["apps"]["app"][0])

    assert app
    assert app.app_id == "11"
    assert app.name == "Roku Channel Store"


def test_application_active_app() -> None:
    """Test the Application model with active app."""
    app = models.Application.from_dict(ACTIVE_APP_NETFLIX["app"])

    assert app
    assert app.app_id == "12"
    assert app.name == "Netflix"
    assert app.version == "4.1.218"


def test_channel() -> None:
    """Test the Channel model."""
    channel = models.Channel.from_dict(TV_CHANNELS["tv-channels"]["tv-channel"])

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


def test_state() -> None:
    """Test the State model."""
    state = models.State(available=True, standby=False)

    assert state
    assert isinstance(state.at, datetime)
