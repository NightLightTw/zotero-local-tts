"""Command-line entry point for the local bridge."""

import uvicorn

from .app import create_app
from .config import default_settings
from .engine import MLXAudioEngine


def main() -> None:
    settings = default_settings()
    uvicorn.run(
        create_app(engine=MLXAudioEngine(), settings=settings),
        host=settings.host,
        port=settings.port,
    )
