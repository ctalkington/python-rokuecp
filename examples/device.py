# pylint: disable=W0621
"""Asynchronous Python client for IPP."""
import asyncio

from rokuecp import Roku


async def main():
    """Show example of connecting to your IPP print server."""
    async with Roku("192.168.1.81") as roku:
        # Get Roku Device Info
        device = await roku.update()
        print(device.info)

        await roku.remote("poweron")
        await roku.remote("home")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
