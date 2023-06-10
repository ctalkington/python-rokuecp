"""Tests for Roku."""
# pylint: disable=protected-access
import asyncio
from datetime import datetime, timedelta, timezone
from socket import gaierror
from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientError, ClientResponse, ClientSession
from aresponses import Response, ResponsesMockServer
from freezegun.api import FrozenDateTimeFactory

from rokuecp import Roku
from rokuecp.exceptions import (
    RokuConnectionError,
    RokuConnectionTimeoutError,
    RokuError,
)
from tests import fake_addrinfo_results

HOSTNAME = "roku.local"
HOST = "192.168.1.86"
PORT = 8060

MATCH_HOST = f"{HOST}:{PORT}"
NON_STANDARD_PORT = 3333


@pytest.mark.asyncio
async def test_xml_request(aresponses: ResponsesMockServer) -> None:
    """Test XML response is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/response/xml",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text="<status>OK</status>",
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        response = await client._request("response/xml")

        assert isinstance(response, dict)
        assert response["status"] == "OK"


@pytest.mark.asyncio
async def test_text_xml_request(aresponses: ResponsesMockServer) -> None:
    """Test (text) XML response is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/response/text-xml",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "text/xml"},
            text="<status>OK</status>",
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        response = await client._request("response/text-xml")

        assert isinstance(response, dict)
        assert response["status"] == "OK"


@pytest.mark.asyncio
async def test_xml_request_parse_error(aresponses: ResponsesMockServer) -> None:
    """Test invalid XML response is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/response/xml-parse-error",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text="<!status>>",
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        with pytest.raises(RokuError):
            assert await client._request("response/xml-parse-error")


@pytest.mark.asyncio
async def test_text_request(aresponses: ResponsesMockServer) -> None:
    """Test non XML response is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/response/text",
        "GET",
        aresponses.Response(status=200, text="OK"),
    )
    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        response = await client._request("response/text")
        assert response == "OK"


@pytest.mark.asyncio
async def test_internal_session(aresponses: ResponsesMockServer) -> None:
    """Test JSON response is handled correctly with internal session."""
    aresponses.add(
        MATCH_HOST,
        "/response/xml",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/xml"},
            text="<status>OK</status>",
        ),
    )

    async with Roku(HOST) as client:
        response = await client._request("response/xml")

        assert isinstance(response, dict)
        assert response["status"] == "OK"


@pytest.mark.asyncio
async def test_post_request(aresponses: ResponsesMockServer) -> None:
    """Test POST requests are handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/method/post",
        "POST",
        aresponses.Response(status=200, text="OK"),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        response = await client._request("method/post", method="POST")
        assert response == "OK"


@pytest.mark.asyncio
async def test_request_port(aresponses: ResponsesMockServer) -> None:
    """Test the handling of non-standard API port."""
    aresponses.add(
        f"{HOST}:{NON_STANDARD_PORT}",
        "/support/port",
        "GET",
        aresponses.Response(status=200, text="OK"),
    )

    async with ClientSession() as session:
        client = Roku(host=HOST, port=NON_STANDARD_PORT, session=session)
        response = await client._request("support/port")
        assert response == "OK"


@pytest.mark.asyncio
async def test_timeout(aresponses: ResponsesMockServer) -> None:
    """Test request timeout from the API."""

    # Faking a timeout by sleeping
    async def response_handler(_: ClientResponse) -> Response:
        await asyncio.sleep(2)
        return aresponses.Response(body="Timeout!")

    aresponses.add(
        MATCH_HOST,
        "/timeout",
        "GET",
        response_handler,
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session, request_timeout=1)
        with pytest.raises(RokuConnectionTimeoutError):
            assert await client._request("timeout")


@pytest.mark.asyncio
async def test_client_error() -> None:
    """Test HTTP client error."""
    async with ClientSession() as session:
        session.request = AsyncMock(side_effect=ClientError)

        client = Roku(HOST, session=session)
        with pytest.raises(RokuConnectionError):
            assert await client._request("client/error", method="ABC")


@pytest.mark.asyncio
async def test_http_error404(aresponses: ResponsesMockServer) -> None:
    """Test HTTP 404 response handling."""
    aresponses.add(
        MATCH_HOST,
        "/http/404",
        "GET",
        aresponses.Response(text="Not Found!", status=404),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        with pytest.raises(RokuError):
            assert await client._request("http/404")


@pytest.mark.asyncio
async def test_http_error500(aresponses: ResponsesMockServer) -> None:
    """Test HTTP 500 response handling."""
    aresponses.add(
        MATCH_HOST,
        "/http/500",
        "GET",
        aresponses.Response(text="Internal Server Error", status=500),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        with pytest.raises(RokuError):
            assert await client._request("http/500")


@pytest.mark.asyncio
@pytest.mark.freeze_time("2022-03-27 00:00:00+00:00")
async def test_resolve_hostname(
    aresponses: ResponsesMockServer,
    resolver: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that hostnames are resolved before request."""
    resolver.return_value = fake_addrinfo_results([HOST])

    aresponses.add(
        MATCH_HOST,
        "/support/hostname",
        "GET",
        aresponses.Response(status=200, text="OK"),
    )

    aresponses.add(
        f"192.168.1.68:{PORT}",
        "/support/hostname",
        "GET",
        aresponses.Response(status=200, text="OK"),
    )

    async with ClientSession() as session:
        client = Roku(HOSTNAME, session=session)
        assert await client._request("support/hostname")

        dns = client.get_dns_state()
        assert dns["enabled"]
        assert dns["hostname"] == HOSTNAME
        assert dns["ip_address"] == HOST
        assert dns["resolved_at"] == datetime(2022, 3, 27, 0, 0)  # noqa: DTZ001

        freezer.tick(delta=timedelta(hours=3))
        resolver.return_value = fake_addrinfo_results(["192.168.1.68"])
        assert await client._request("support/hostname")

        dns = client.get_dns_state()
        assert dns["enabled"]
        assert dns["hostname"] == HOSTNAME
        assert dns["ip_address"] == "192.168.1.68"
        assert dns["resolved_at"] == datetime(2022, 3, 27, 3, 0)  # noqa: DTZ001


@pytest.mark.asyncio
@pytest.mark.freeze_time("2022-03-27 00:00:00+00:00")
async def test_resolve_hostname_multiple_clients(
    aresponses: ResponsesMockServer,
    resolver: AsyncMock,
) -> None:
    """Test that hostnames are resolved before request with multiple clients."""
    aresponses.add(
        MATCH_HOST,
        "/support/hostname",
        "GET",
        aresponses.Response(status=200, text="OK"),
    )

    aresponses.add(
        f"192.168.1.99:{PORT}",
        "/support/hostname",
        "GET",
        aresponses.Response(status=200, text="OK"),
    )

    async with ClientSession() as session:
        resolver.return_value = fake_addrinfo_results([HOST])
        client = Roku(HOSTNAME, session=session)
        assert await client._request("support/hostname")

        dns = client.get_dns_state()
        assert dns["enabled"]
        assert dns["hostname"] == HOSTNAME
        assert dns["ip_address"] == HOST
        assert dns["resolved_at"] == datetime(2022, 3, 27, 0, 0)  # noqa: DTZ001

        resolver.return_value = fake_addrinfo_results(["192.168.1.99"])
        client2 = Roku("roku.dev", session=session)
        assert await client2._request("support/hostname")

        dns2 = client2.get_dns_state()
        assert dns2["enabled"]
        assert dns2["hostname"] == "roku.dev"
        assert dns2["ip_address"] == "192.168.1.99"
        assert dns2["resolved_at"] == datetime(2022, 3, 27, 0, 0)  # noqa: DTZ001


@pytest.mark.asyncio
async def test_resolve_hostname_error(resolver: AsyncMock) -> None:
    """Test that hostname resolution errors are handled."""
    resolver.side_effect = gaierror

    async with ClientSession() as session:
        client = Roku(HOSTNAME, session=session)

        with pytest.raises(RokuConnectionError):
            await client._request("support/hostname-error")
