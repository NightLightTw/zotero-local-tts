"""macOS LaunchAgent lifecycle for the local bridge."""

from __future__ import annotations

import os
import plistlib
import subprocess
import sys
import time
from pathlib import Path

from .config import DEFAULT_DATA_DIR

LAUNCH_AGENT_LABEL = "io.github.nightlighttw.zotero-local-tts"
LAUNCH_AGENT_PATH = (
    Path.home() / "Library" / "LaunchAgents" / f"{LAUNCH_AGENT_LABEL}.plist"
)


def _require_macos() -> None:
    if sys.platform != "darwin":
        raise RuntimeError("The background-service installer currently supports macOS only")


def launch_agent_definition(python_executable: Path | None = None) -> dict[str, object]:
    """Return a launchd definition that runs the installed package offline."""
    # Do not resolve the virtual-environment symlink: invoking its target would
    # lose the venv's installed packages.
    executable = python_executable or Path(sys.executable)
    return {
        "Label": LAUNCH_AGENT_LABEL,
        "ProgramArguments": [
            str(executable),
            "-m",
            "zotero_local_tts.cli",
            "serve",
        ],
        "EnvironmentVariables": {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
        },
        "RunAtLoad": True,
        "KeepAlive": {"SuccessfulExit": False},
        "ThrottleInterval": 10,
        "StandardOutPath": str(DEFAULT_DATA_DIR / "bridge.log"),
        "StandardErrorPath": str(DEFAULT_DATA_DIR / "bridge-error.log"),
    }


def _service_target() -> str:
    return f"gui/{os.getuid()}/{LAUNCH_AGENT_LABEL}"


def _launch_agent_status() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["launchctl", "print", _service_target()],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def _bootout_launch_agent() -> bool:
    """Stop the loaded job, preserving its plist if launchctl fails."""
    if _launch_agent_status().returncode != 0:
        return False
    result = subprocess.run(
        ["launchctl", "bootout", _service_target()],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "no error detail"
        raise RuntimeError(
            f"launchctl could not stop {LAUNCH_AGENT_LABEL} "
            f"(exit {result.returncode}: {detail})"
        )
    return True


def _bootstrap_launch_agent(
    domain: str, attempts: int = 3, retry_delay: float = 0.25
) -> None:
    """Load the job, retrying launchd's transient post-bootout I/O error."""
    for attempt in range(attempts):
        result = subprocess.run(
            ["launchctl", "bootstrap", domain, str(LAUNCH_AGENT_PATH)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            return
        if attempt + 1 < attempts:
            time.sleep(retry_delay * (attempt + 1))
    detail = result.stderr.strip() or "no error detail"
    raise RuntimeError(
        f"launchctl could not load {LAUNCH_AGENT_LABEL} "
        f"after {attempts} attempts (exit {result.returncode}: {detail})"
    )


def install_launch_agent() -> Path:
    """Install and immediately start the per-user LaunchAgent."""
    _require_macos()
    DEFAULT_DATA_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    DEFAULT_DATA_DIR.chmod(0o700)
    LAUNCH_AGENT_PATH.parent.mkdir(mode=0o755, parents=True, exist_ok=True)

    temporary_path = LAUNCH_AGENT_PATH.with_suffix(".plist.tmp")
    temporary_path.write_bytes(plistlib.dumps(launch_agent_definition(), sort_keys=False))
    temporary_path.chmod(0o644)
    try:
        _bootout_launch_agent()
        temporary_path.replace(LAUNCH_AGENT_PATH)
        domain = f"gui/{os.getuid()}"
        _bootstrap_launch_agent(domain)
        subprocess.run(
            ["launchctl", "kickstart", "-k", _service_target()],
            check=True,
        )
    finally:
        temporary_path.unlink(missing_ok=True)
    return LAUNCH_AGENT_PATH


def uninstall_launch_agent() -> bool:
    """Stop and remove the per-user LaunchAgent, if installed."""
    _require_macos()
    existed = LAUNCH_AGENT_PATH.exists()
    was_loaded = _bootout_launch_agent()
    LAUNCH_AGENT_PATH.unlink(missing_ok=True)
    return existed or was_loaded


def launch_agent_is_running() -> bool:
    """Return whether launchd currently has the bridge job loaded and running."""
    _require_macos()
    result = _launch_agent_status()
    return result.returncode == 0 and "state = running" in result.stdout
