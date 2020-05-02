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
        response = await client.update()

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.apps, List)

        response = await client.update()

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.apps, List)
