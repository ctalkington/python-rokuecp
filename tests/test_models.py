"""Tests for Roku Models."""
import pytest
import rokuecp.models as models
import xmltodict
from rokuecp import RokuError

from . import load_fixture

INFO = xmltodict.parse(load_fixture("device-info.xml"))
APPS = xmltodict.parse(load_fixture("apps.xml"))

DEVICE = {"info": INFO, "apps": APPS["apps"]["app"]}


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
    print(INFO)
    info = models.Info.from_dict(INFO)

    assert info
    assert info.name == ""
    assert info.version == ""


def test_application() -> None:
    """Test the Application model."""
    app = models.Application.from_dict(APPS[0])

    assert app
    assert app.app_id == ""
    assert app.name == ""
