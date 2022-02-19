"""Tests for Roku."""
# pylint: disable=protected-access
import pytest
from aiohttp import ClientSession
from aresponses import ResponsesMockServer
from rokuecp import Roku, RokuError, models

from . import load_fixture

HOST = "192.168.1.86"
PORT = 8060

MATCH_HOST = f"{HOST}:{PORT}"
ICON_BASE = f"http://{MATCH_HOST}/query/icon"


@pytest.mark.asyncio
async def test_loop() -> None:
    """Test loop usage is handled correctly."""
    async with Roku(HOST) as roku:
        assert isinstance(roku, Roku)


@pytest.mark.asyncio
async def test_app_icon_url() -> None:
    """Test app_icon_url is handled correctly."""
    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        assert roku.app_icon_url("101") == f"{ICON_BASE}/101"


@pytest.mark.asyncio
async def test_device(aresponses: ResponsesMockServer) -> None:
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
async def test_launch(aresponses: ResponsesMockServer) -> None:
    """Test launch is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/launch/101",
        "POST",
        aresponses.Response(status=200),
    )

    aresponses.add(
        MATCH_HOST,
        "/launch/102?contentID=deeplink",
        "POST",
        aresponses.Response(status=200),
        match_querystring=True,
    )

    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        await roku.launch("101")
        await roku.launch("102", {"contentID": "deeplink"})


@pytest.mark.asyncio
async def test_play_on_roku(aresponses: ResponsesMockServer) -> None:
    """Test play_on_roku is handled correctly."""
    video_url = "http://example.com/video file÷awe.mp4?v=2"
    encoded = "http%3A%2F%2Fexample.com%2Fvideo+file%C3%B7awe.mp4%3Fv%3D2"

    aresponses.add(
        MATCH_HOST,
        f"/input/15985?t=v&u={encoded}",
        "POST",
        aresponses.Response(status=200),
        match_querystring=True,
    )

    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        await roku.play_on_roku(video_url)


@pytest.mark.asyncio
async def test_literal(aresponses: ResponsesMockServer) -> None:
    """Test literal is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/keypress/Lit_t",
        "POST",
        aresponses.Response(status=200),
    )

    aresponses.add(
        MATCH_HOST,
        "/keypress/Lit_h",
        "POST",
        aresponses.Response(status=200),
    )

    aresponses.add(
        MATCH_HOST,
        "/keypress/Lit_e",
        "POST",
        aresponses.Response(status=200),
    )

    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        await roku.literal("the")


@pytest.mark.asyncio
async def test_remote(aresponses: ResponsesMockServer) -> None:
    """Test remote is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/keypress/Home",
        "POST",
        aresponses.Response(status=200),
    )

    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        await roku.remote("home")


@pytest.mark.asyncio
async def test_remote_invalid_key() -> None:
    """Test remote with invalid key is handled correctly."""
    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        with pytest.raises(RokuError):
            await roku.remote("super")


@pytest.mark.asyncio
async def test_remote_search(aresponses: ResponsesMockServer) -> None:
    """Test remote search keypress is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/search/browse",
        "POST",
        aresponses.Response(status=200),
    )

    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        await roku.remote("search")


@pytest.mark.asyncio
async def test_search(aresponses: ResponsesMockServer) -> None:
    """Test search is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/search/browse?keyword=test",
        "POST",
        aresponses.Response(status=200, text="OK"),
        match_querystring=True,
    )

    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        await roku.search("test")


@pytest.mark.asyncio
async def test_tune(aresponses: ResponsesMockServer) -> None:
    """Test tune is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/launch/tvinput.dtv?ch=13.4",
        "POST",
        aresponses.Response(status=200, text="OK"),
        match_querystring=True,
    )

    async with ClientSession() as session:
        roku = Roku(HOST, session=session)
        await roku.tune("13.4")


@pytest.mark.asyncio
async def test_update(aresponses: ResponsesMockServer) -> None:
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
        repeat=2,
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
        repeat=2,
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
        repeat=2,
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        response = await client.update()

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.state, models.State)
        assert isinstance(response.apps, list)
        assert isinstance(response.channels, list)
        assert isinstance(response.app, models.Application)
        assert response.channel is None
        assert response.media is None

        assert response.state.available
        assert not response.state.standby
        assert len(response.channels) == 0

        response = await client.update()

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.state, models.State)
        assert isinstance(response.apps, list)
        assert isinstance(response.channels, list)
        assert isinstance(response.app, models.Application)
        assert response.channel is None
        assert response.media is None

        assert response.state.available
        assert not response.state.standby
        assert len(response.channels) == 0


@pytest.mark.asyncio
async def test_update_media_state(aresponses: ResponsesMockServer) -> None:
    """Test update method is handled correctly with pluto app."""
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
            text=load_fixture("active-app-pluto.xml"),
        ),
    )

    aresponses.add(
        MATCH_HOST,
        "/query/media-player",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("media-player-pluto-play.xml"),
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        response = await client.update()

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.media, models.MediaState)
        assert isinstance(response.state, models.State)
        assert isinstance(response.apps, list)
        assert isinstance(response.channels, list)
        assert isinstance(response.app, models.Application)
        assert response.channel is None

        assert response.state.available
        assert not response.state.standby
        assert len(response.channels) == 0

        assert not response.media.live
        assert not response.media.paused
        assert response.media.duration == 6496
        assert response.media.position == 38


@pytest.mark.asyncio
async def test_update_power_off(aresponses: ResponsesMockServer) -> None:
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
        assert isinstance(response.apps, list)
        assert isinstance(response.channels, list)
        assert response.app is None
        assert response.channel is None
        assert response.media is None

        assert response.state.available
        assert response.state.standby
        assert len(response.channels) == 0


@pytest.mark.asyncio
async def test_update_standby(aresponses: ResponsesMockServer) -> None:
    """Test update method is handled correctly when device transitions to standby."""
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
        repeat=2,
    )

    aresponses.add(
        MATCH_HOST,
        "/query/active-app",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("active-app-pluto.xml"),
        ),
    )

    aresponses.add(
        MATCH_HOST,
        "/query/media-player",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("media-player-pluto-play.xml"),
        ),
    )

    aresponses.add(
        MATCH_HOST,
        "/query/device-info",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("device-info-standby.xml"),
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        response = await client.update()

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.media, models.MediaState)
        assert isinstance(response.state, models.State)
        assert isinstance(response.apps, list)
        assert isinstance(response.channels, list)
        assert isinstance(response.app, models.Application)
        assert response.channel is None

        assert response.state.available
        assert not response.state.standby
        assert len(response.channels) == 0

        assert not response.media.live
        assert not response.media.paused
        assert response.media.duration == 6496
        assert response.media.position == 38

        response = await client.update()

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.state, models.State)
        assert isinstance(response.apps, list)
        assert isinstance(response.channels, list)
        assert response.app is None
        assert response.channel is None
        assert response.media is None

        assert response.state.available
        assert response.state.standby
        assert len(response.channels) == 0


@pytest.mark.asyncio
async def test_update_tv(aresponses: ResponsesMockServer) -> None:
    """Test update method is handled correctly for TVs."""
    for _ in range(0, 2):
        aresponses.add(
            MATCH_HOST,
            "/query/device-info",
            "GET",
            aresponses.Response(
                status=200,
                headers={"Content-Type": "application/xml"},
                text=load_fixture("device-info-7820x.xml"),
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
            "/query/tv-active-channel",
            "GET",
            aresponses.Response(
                status=200,
                headers={"Content-Type": "application/xml"},
                text=load_fixture("tv-active-channel.xml"),
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

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        response = await client.update()

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.state, models.State)
        assert isinstance(response.apps, list)
        assert isinstance(response.channels, list)
        assert isinstance(response.app, models.Application)
        assert isinstance(response.channel, models.Channel)
        assert response.media is None

        assert response.state.available
        assert not response.state.standby
        assert len(response.channels) == 2

        response = await client.update(True)

        assert response
        assert isinstance(response.info, models.Info)
        assert isinstance(response.state, models.State)
        assert isinstance(response.apps, list)
        assert isinstance(response.channels, list)
        assert isinstance(response.app, models.Application)
        assert isinstance(response.channel, models.Channel)
        assert response.media is None

        assert response.state.available
        assert not response.state.standby
        assert len(response.channels) == 1


@pytest.mark.asyncio
async def test_get_active_app(aresponses: ResponsesMockServer) -> None:
    """Test _get_active_app method is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/query/active-app",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("active-app-amazon.xml"),
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        assert await client._get_active_app()


@pytest.mark.asyncio
async def test_get_active_app_invalid(aresponses: ResponsesMockServer) -> None:
    """Test _get_active_app method is handled correctly with invalid data."""
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
async def test_get_apps(aresponses: ResponsesMockServer) -> None:
    """Test _get_apps method is handled correctly."""
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
        res = await client._get_apps()
        assert isinstance(res, list)
        assert len(res) == 8


@pytest.mark.asyncio
async def test_get_apps_invalid(aresponses: ResponsesMockServer) -> None:
    """Test _get_apps method is handled correctly with invalid data."""
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
async def test_get_apps_single_app(aresponses: ResponsesMockServer) -> None:
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
        assert isinstance(res, list)
        assert len(res) == 1


@pytest.mark.asyncio
async def test_get_device_info(aresponses: ResponsesMockServer) -> None:
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
async def test_get_media_state_close(aresponses: ResponsesMockServer) -> None:
    """Test _get_media_state method is handled correctly with closed media."""
    aresponses.add(
        MATCH_HOST,
        "/query/media-player",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("media-player-close.xml"),
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        assert await client._get_media_state()


@pytest.mark.asyncio
async def test_get_media_state_invalid(aresponses: ResponsesMockServer) -> None:
    """Test _get_media_state method is handled correctly with invalid data."""
    aresponses.add(
        MATCH_HOST,
        "/query/media-player",
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
            assert await client._get_media_state()


@pytest.mark.asyncio
async def test_get_media_state_live(aresponses: ResponsesMockServer) -> None:
    """Test _get_media_state method is handled correctly with live media."""
    aresponses.add(
        MATCH_HOST,
        "/query/media-player",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("media-player-pluto-live.xml"),
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        assert await client._get_media_state()


@pytest.mark.asyncio
async def test_get_media_state_pause(aresponses: ResponsesMockServer) -> None:
    """Test _get_media_state method is handled correctly with paused media."""
    aresponses.add(
        MATCH_HOST,
        "/query/media-player",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("media-player-pluto-pause.xml"),
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        assert await client._get_media_state()


@pytest.mark.asyncio
async def test_get_media_state_play(aresponses: ResponsesMockServer) -> None:
    """Test _get_media_state method is handled correctly with playing media."""
    aresponses.add(
        MATCH_HOST,
        "/query/media-player",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text=load_fixture("media-player-pluto-play.xml"),
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        assert await client._get_media_state()


@pytest.mark.asyncio
async def test_get_tv_active_channel(aresponses: ResponsesMockServer) -> None:
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
async def test_get_tv_channels(aresponses: ResponsesMockServer) -> None:
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
async def test_get_tv_channels_no_channels(aresponses: ResponsesMockServer) -> None:
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
        assert isinstance(res, list)
        assert len(res) == 0


@pytest.mark.asyncio
async def test_get_tv_channels_single_channel(aresponses: ResponsesMockServer) -> None:
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
        assert isinstance(res, list)
        assert len(res) == 1
