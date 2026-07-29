"""Tests for the macOS background-service lifecycle."""

import subprocess
from pathlib import Path

import pytest

from zotero_local_tts import service
from zotero_local_tts.service import LAUNCH_AGENT_LABEL, launch_agent_definition


def test_launch_agent_runs_installed_package_offline() -> None:
    definition = launch_agent_definition(Path("/private/project/.venv/bin/python"))

    assert definition["Label"] == LAUNCH_AGENT_LABEL
    assert definition["ProgramArguments"] == [
        "/private/project/.venv/bin/python",
        "-m",
        "zotero_local_tts.cli",
        "serve",
    ]
    assert definition["EnvironmentVariables"] == {
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
    }
    assert definition["RunAtLoad"] is True
    assert definition["KeepAlive"] == {"SuccessfulExit": False}
    assert str(definition["StandardErrorPath"]).endswith("bridge-error.log")


def test_uninstall_preserves_plist_when_bootout_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plist = tmp_path / "service.plist"
    plist.write_text("existing definition")
    monkeypatch.setattr(service, "LAUNCH_AGENT_PATH", plist)
    monkeypatch.setattr(service, "_require_macos", lambda: None)
    monkeypatch.setattr(
        service,
        "_launch_agent_status",
        lambda: subprocess.CompletedProcess([], 0, "state = running", ""),
    )
    monkeypatch.setattr(
        service.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 5, "", "not permitted"),
    )

    with pytest.raises(RuntimeError, match="could not stop"):
        service.uninstall_launch_agent()

    assert plist.exists()


def test_uninstall_removes_unloaded_plist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plist = tmp_path / "service.plist"
    plist.write_text("existing definition")
    monkeypatch.setattr(service, "LAUNCH_AGENT_PATH", plist)
    monkeypatch.setattr(service, "_require_macos", lambda: None)
    monkeypatch.setattr(
        service,
        "_launch_agent_status",
        lambda: subprocess.CompletedProcess([], 113, "", "not found"),
    )

    assert service.uninstall_launch_agent() is True
    assert not plist.exists()


def test_bootstrap_retries_transient_launchd_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    results = iter(
        [
            subprocess.CompletedProcess([], 5, "", "Input/output error"),
            subprocess.CompletedProcess([], 0, "", ""),
        ]
    )
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        del kwargs
        calls.append(command)
        return next(results)

    monkeypatch.setattr(service.subprocess, "run", fake_run)

    service._bootstrap_launch_agent("gui/501", attempts=2, retry_delay=0)

    assert len(calls) == 2
