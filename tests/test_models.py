"""Tests for Roku Models."""
import pytest
import rokuecp.models as models
import xmltodict
from rokuecp import RokuError

from . import load_fixture

INFO = xmltodict.parse(load_fixture("device-info.xml"))
APPS = xmltodict.parse(load_fixture("apps.xml"))

DEVICE = {"info": INFO["device-info"], "apps": APPS["apps"]["app"]}


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
    info = models.Info.from_dict(INFO["device-info"])

    assert info
    assert info.name == "My Roku 3"
    assert info.brand == "Roku"
    assert info.model_name == "Roku 3"
    assert info.model_number == "4200X"
    assert info.serial_number == "1GU48T017973'"
    assert info.version == "7.5.0"


def test_application() -> None:
    """Test the Application model."""
    app = models.Application.from_dict(APPS["apps"]["app"][0])

    assert app
    assert app.app_id == "11"
    assert app.name == "Roku Channel Store"
