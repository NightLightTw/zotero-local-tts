"""Command-line entry point for the bridge and its background service."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def serve() -> None:
    import uvicorn

    from .app import create_app
    from .config import default_settings
    from .engine import MLXAudioEngine

    settings = default_settings()
    uvicorn.run(
        create_app(engine=MLXAudioEngine(), settings=settings),
        host=settings.host,
        port=settings.port,
    )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="zotero-local-tts")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("serve", "install-service", "uninstall-service", "service-status"),
        default="serve",
    )
    args = parser.parse_args(argv)

    if args.command == "serve":
        serve()
        return

    from .service import install_launch_agent, launch_agent_is_running, uninstall_launch_agent

    if args.command == "install-service":
        path = install_launch_agent()
        print(f"Installed and started {path}")
    elif args.command == "uninstall-service":
        removed = uninstall_launch_agent()
        message = (
            "Stopped and removed the background service"
            if removed
            else "Service was not installed"
        )
        print(message)
    else:
        print("running" if launch_agent_is_running() else "not running")


if __name__ == "__main__":
    main()
