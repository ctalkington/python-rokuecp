"""Tests for Roku."""
import asyncio

import pytest
from aiohttp import ClientSession
from rokuecp import Roku
from rokuecp.exceptions import RokuConnectionError, RokuError
from tests import patch_resolver_loop

HOSTNAME = "roku.local"
HOST = "192.168.1.86"
PORT = 8060

MATCH_HOST = f"{HOST}:{PORT}"
NON_STANDARD_PORT = 3333


@pytest.mark.asyncio
async def test_xml_request(aresponses):
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
async def test_text_xml_request(aresponses):
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
async def test_xml_request_parse_error(aresponses):
    """Test invalid XML response is handled correctly."""
    aresponses.add(
        MATCH_HOST,
        "/response/xml-parse-error",
        "GET",
        aresponses.Response(
            status=200, headers={"Content-Type": "application/xml"}, text="<!status>>",
        ),
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        with pytest.raises(RokuError):
            assert await client._request("response/xml-parse-error")


@pytest.mark.asyncio
async def test_text_request(aresponses):
    """Test non XML response is handled correctly."""
    aresponses.add(
        MATCH_HOST, "/response/text", "GET", aresponses.Response(status=200, text="OK"),
    )
    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        response = await client._request("response/text")
        assert response == "OK"


@pytest.mark.asyncio
async def test_internal_session(aresponses):
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
async def test_post_request(aresponses):
    """Test POST requests are handled correctly."""
    aresponses.add(
        MATCH_HOST, "/method/post", "POST", aresponses.Response(status=200, text="OK")
    )

    async with ClientSession() as session:
        client = Roku(HOST, session=session)
        response = await client._request("method/post", method="POST")
        assert response == "OK"


@pytest.mark.asyncio
async def test_request_port(aresponses):
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
async def test_timeout(aresponses):
    """Test request timeout from the API."""
    # Faking a timeout by sleeping
    async def response_handler(_):
        await asyncio.sleep(2)
        return aresponses.Response(body="Timeout!")

    aresponses.add(MATCH_HOST, "/timeout", "GET", response_handler)

    async with ClientSession() as session:
        client = Roku(HOST, session=session, request_timeout=1)
        with pytest.raises(RokuConnectionError):
            assert await client._request("timeout")


@pytest.mark.asyncio
async def test_client_error():
    """Test HTTP client error."""
    async with ClientSession() as session:
        client = Roku("#", session=session)
        with pytest.raises(RokuConnectionError), patch_resolver_loop(["#"]):
            assert await client._request("client/error", method="ABC")


@pytest.mark.asyncio
async def test_http_error404(aresponses):
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
async def test_http_error500(aresponses):
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
async def test_resolve_hostname(aresponses) -> None:
    """Test that hostnames are resolved before request."""
    aresponses.add(
        MATCH_HOST,
        "/support/hostname",
        "GET",
        aresponses.Response(status=200, text="OK"),
    )

    async with ClientSession() as session:
        with patch_resolver_loop([HOST]):
            client = Roku(HOSTNAME, session=session)
            assert await client._request("support/hostname")


@pytest.mark.asyncio
async def test_resolve_hostname_error() -> None:
    """Test that hostname resolution errors are handled."""
    async with ClientSession() as session:
        client = Roku(HOSTNAME, session=session)

        with pytest.raises(RokuConnectionError), patch_resolver_loop():
            await client._request("support/hostname-error")
