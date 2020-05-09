"""Tests for Roku."""
from typing import List

import pytest
import rokuecp.models as models
from aiohttp import ClientSession
from rokuecp import Roku, RokuError

from . import load_fixture

HOST = "192.168.1.86"
PORT = 8060

MATCH_HOST = f"{HOST}:{PORT}"
ICON_BASE = f"http://{MATCH_HOST}/query/icon"


@pytest.mark.asyncio
async def test_app_icon_url():
    """Test app_icon_url is handled correctly."""
    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        assert roku.app_icon_url("101") == f"{ICON_BASE}/101"


@pytest.mark.asyncio
async def test_device(aresponses):
    """Test app property is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/query/device-info",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("device-info.xml"),
        ),
    )

    aresponses.add(
        MATCH_HOST,
        "/query/apps",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("apps.xml"),
        ),
    )

    aresponses.add(
        MATCH_HOST,
        "/query/active-app",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("active-app-roku.xml"),
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        await client.update()

        assert client.device
        assert isinstance(client.device, models.Device)


@pytest.mark.asyncio
async def test_launch(aresponses):
    """Test launch is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/launch/101?contentID=101",
        "POST",
        aresponses.Response(status=200, text="OK"),
        match_querystring=True,
    )

    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        await roku.launch("101")


@pytest.mark.asyncio
async def test_literal(aresponses):
    """Test literal is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/keypress/Lit_t",
        "POST",
        aresponses.Response(status=200, text="OK"),
    )

    aresponses.add(
        MATCH_HOST,
        "/keypress/Lit_h",
        "POST",
        aresponses.Response(status=200, text="OK"),
    )

    aresponses.add(
        MATCH_HOST,
        "/keypress/Lit_e",
        "POST",
        aresponses.Response(status=200, text="OK"),
    )

    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        await roku.literal("the")


@pytest.mark.asyncio
async def test_remote(aresponses):
    """Test remote is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/keypress/Home",
        "POST",
        aresponses.Response(status=200, text="OK"),
    )

    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        await roku.remote("home")


@pytest.mark.asyncio
async def test_remote_invalid_key():
    """Test remote with invalid key is handled correctly."""
    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        with pytest.raises(RokuError):
            await roku.remote("super")


@pytest.mark.asyncio
async def test_tune(aresponses):
    """Test tune is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/launch/tvinput.dtv?contentID=tvinput.dtv&ch=13.4",
        "POST",
        aresponses.Response(status=200, text="OK"),
        match_querystring=True,
    )

    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        await roku.tune("13.4")


@pytest.mark.asyncio
async def test_update(aresponses):
    """Test update method is handled correctly."""
    for _ in range(0, 2):
        aresponses.add(
            MATCH_HOST,
            "/query/device-info",
            "GET",
            aresponses.Response(
                status=200,
                headers={"Content-Type": "application/xml"},
                text=load_fixture("device-info.xml"),
            ),
        )

        aresponses.add(
            MATCH_HOST,
            "/query/apps",
            "GET",
            aresponses.Response(
                status=200,
                headers={"Content-Type": "application/xml"},
                text=load_fixture("apps.xml"),
            ),
        )

        aresponses.add(
            MATCH_HOST,
            "/query/active-app",
            "GET",
            aresponses.Response(
                status=200,
                headers={"Content-Type": "application/xml"},
                text=load_fixture("active-app-roku.xml"),
            ),
        )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        response = await client.update()

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.state, models.State)
        assert isinstance(response.apps, List)
        assert isinstance(response.channels, List)
        assert isinstance(response.app, models.Application)
        assert response.channel is None

        assert response.state.available
        assert not response.state.standby
        assert len(response.channels) == 0

        response = await client.update()

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.state, models.State)
        assert isinstance(response.apps, List)
        assert isinstance(response.channels, List)
        assert isinstance(response.app, models.Application)
        assert response.channel is None

        assert response.state.available
        assert not response.state.standby
        assert len(response.channels) == 0


@pytest.mark.asyncio
async def test_update_power_off(aresponses):
    """Test update method is handled correctly when power is off."""
    aresponses.add(
        MATCH_HOST,
        "/query/device-info",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("device-info-power-off.xml"),
        ),
    )

    aresponses.add(
        MATCH_HOST,
        "/query/apps",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("apps.xml"),
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        response = await client.update()

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.state, models.State)
        assert isinstance(response.apps, List)
        assert isinstance(response.channels, List)
        assert response.app is None
        assert response.channel is None

        assert response.state.available
        assert response.state.standby
        assert len(response.channels) == 0


@pytest.mark.asyncio
async def test_update_tv(aresponses):
    """Test update method is handled correctly for TVs."""
    aresponses.add(
        MATCH_HOST,
        "/query/device-info",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("device-info-tv.xml"),
        ),
    )

    aresponses.add(
        MATCH_HOST,
        "/query/apps",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("apps-tv.xml"),
        ),
    )

    aresponses.add(
        MATCH_HOST,
        "/query/active-app",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("active-app-tv.xml"),
        ),
    )

    aresponses.add(
        MATCH_HOST,
        "/query/tv-channels",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("tv-channels.xml"),
        ),
    )

    aresponses.add(
        MATCH_HOST,
        "/query/tv-active-channel",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("tv-active-channel.xml"),
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        response = await client.update()

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.state, models.State)
        assert isinstance(response.apps, List)
        assert isinstance(response.channels, List)
        assert isinstance(response.app, models.Application)
        assert isinstance(response.channel, models.Channel)

        assert response.state.available
        assert not response.state.standby
        assert len(response.channels) == 2


@pytest.mark.asyncio
async def test_update_tv_channels(aresponses):
    """Test update_tv_channels method is handled correctly for TVs."""
    aresponses.add(
        MATCH_HOST,
        "/query/device-info",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("device-info-tv.xml"),
        ),
    )

    aresponses.add(
        MATCH_HOST,
        "/query/apps",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("apps-tv.xml"),
        ),
    )

    aresponses.add(
        MATCH_HOST,
        "/query/active-app",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("active-app-tv.xml"),
        ),
    )

    aresponses.add(
        MATCH_HOST,
        "/query/tv-channels",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("tv-channels.xml"),
        ),
    )
    
    aresponses.add(
        MATCH_HOST,
        "/query/tv-channels",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("tv-channels-single.xml"),
        ),
    )

    aresponses.add(
        MATCH_HOST,
        "/query/tv-active-channel",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("tv-active-channel.xml"),
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        response = await client.update_tv_channels()

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.state, models.State)
        assert isinstance(response.apps, List)
        assert isinstance(response.channels, List)
        assert isinstance(response.app, models.Application)
        assert isinstance(response.channel, models.Channel)

        assert response.state.available
        assert not response.state.standby
        assert len(response.channels) == 2
        
        response = await client.update_tv_channels()

        assert isinstance(response.channels, List)
        assert len(response.channels) == 1


@pytest.mark.asyncio
async def test_get_active_app(aresponses):
    """Test _get_active_app method is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/query/active-app",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text="<other>value</other>",
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        with pytest.raises(RokuError):
            assert await client._get_active_app()


@pytest.mark.asyncio
async def test_get_apps(aresponses):
    """Test _get_apps method is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/query/apps",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text="<other>value</other>",
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        with pytest.raises(RokuError):
            assert await client._get_apps()


@pytest.mark.asyncio
async def test_get_apps_single_app(aresponses):
    """Test _get_apps method is handled correctly with single app."""
    aresponses.add(
        MATCH_HOST,
        "/query/apps",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("apps-single.xml"),
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        res = await client._get_apps()
        assert isinstance(res, List)
        assert len(res) == 1


@pytest.mark.asyncio
async def test_get_device_info(aresponses):
    """Test _get_device_info method is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/query/device-info",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text="<other>value</other>",
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        with pytest.raises(RokuError):
            assert await client._get_device_info()


@pytest.mark.asyncio
async def test_get_tv_active_channel(aresponses):
    """Test _get_tv_active_channel method is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/query/tv-active-channel",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text="<other>value</other>",
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        with pytest.raises(RokuError):
            assert await client._get_tv_active_channel()


@pytest.mark.asyncio
async def test_get_tv_channels(aresponses):
    """Test _get_tv_channels method is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/query/tv-channels",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text="<other>value</other>",
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        with pytest.raises(RokuError):
            assert await client._get_tv_channels()


@pytest.mark.asyncio
async def test_get_tv_channels_no_channels(aresponses):
    """Test _get_tv_channels method is handled correctly with no channels."""
    aresponses.add(
        MATCH_HOST,
        "/query/tv-channels",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("tv-channels-empty.xml"),
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        res = await client._get_tv_channels()
        assert isinstance(res, List)
        assert len(res) == 0


@pytest.mark.asyncio
async def test_get_tv_channels_single_channel(aresponses):
    """Test _get_tv_channels method is handled correctly with single channel."""
    aresponses.add(
        MATCH_HOST,
        "/query/tv-channels",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("tv-channels-single.xml"),
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        res = await client._get_tv_channels()
        assert isinstance(res, List)
        assert len(res) == 1
