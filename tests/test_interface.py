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

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        await client.update()

        assert client.device
        assert isinstance(client.device, models.Device)


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
        assert isinstance(response.apps, List)
        assert isinstance(response.channels, List)

        response = await client.update()

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.apps, List)
        assert isinstance(response.channels, List)


@pytest.mark.asyncio
async def test_update_tv(aresponses):
    """Test update method is handled correctly for TVs"""
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
        assert isinstance(response.apps, List)
        assert isinstance(response.channels, List)


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
