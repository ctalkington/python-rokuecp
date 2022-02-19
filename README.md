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

## Setting up development environment

This Python project is fully managed using the [Poetry](https://python-poetry.org) dependency
manager. But also relies on the use of NodeJS for certain checks during
development.

You need at least:

- Python 3.9+
- [Poetry](https://python-poetry.org/docs/#installation)
- NodeJS 14+ (including NPM)

To install all packages, including all development requirements:

```bash
npm install
poetry install
```

As this repository uses the [pre-commit](https://pre-commit.com/) framework, all changes
are linted and tested with each commit. You can run all checks and tests
manually, using the following command:

```bash
poetry run pre-commit run --all-files
```

To run just the Python tests:

```bash
poetry run pytest
```
