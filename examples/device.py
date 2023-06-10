# pylint: disable=W0621
"""Asynchronous Python client for Roku."""
import asyncio

from rokuecp import Roku


async def main() -> None:
    """Show example of connecting to your Roku."""
    async with Roku("192.168.1.61") as roku:
        # Get Roku Device Info
        device = await roku.update()
        print(device.info)

        await roku.remote("poweron")
        await asyncio.sleep(2)
        await roku.remote("home")

        # Open Netflix
        await asyncio.sleep(2)
        await roku.launch("12")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
