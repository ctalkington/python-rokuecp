# Python: Roku (ECP) Client

Asynchronous Python client for Roku devices using the [External Control Protocol](https://developer.roku.com/docs/developer-program/debugging/external-control-api.md).

## About

This package allows you to monitor and control Roku devices.

## Installation

```bash
pip install rokuecp
```

## Usage

```python
import asyncio

from rokuecp import Roku


async def main():
    """Show example of connecting to your Roku device."""
    async with Roku("192.168.1.100") as roku:
        print(roku)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
```
