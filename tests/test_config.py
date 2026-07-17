"""Tests for local secret management."""

import os
import stat

import pytest

from zotero_local_tts.config import load_or_create_token


def test_token_is_persistent_and_user_only(tmp_path) -> None:
    token_path = tmp_path / "private" / "token"
    first = load_or_create_token(token_path)
    second = load_or_create_token(token_path)

    assert first == second
    assert len(first) >= 32
    assert stat.S_IMODE(token_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(token_path.parent.stat().st_mode) == 0o700


def test_existing_token_permissions_are_repaired(tmp_path) -> None:
    token_path = tmp_path / "private" / "token"
    token_path.parent.mkdir(mode=0o755)
    token_path.write_text("existing-token\n")
    token_path.chmod(0o644)

    assert load_or_create_token(token_path) == "existing-token"
    assert stat.S_IMODE(token_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(token_path.parent.stat().st_mode) == 0o700


@pytest.mark.skipif(not hasattr(os, "O_NOFOLLOW"), reason="O_NOFOLLOW is unavailable")
def test_refuses_symlinked_token_file(tmp_path) -> None:
    target = tmp_path / "target"
    target.write_text("do-not-read\n")
    token_path = tmp_path / "private" / "token"
    token_path.parent.mkdir()
    token_path.symlink_to(target)

    with pytest.raises(OSError):
        load_or_create_token(token_path)

    assert target.read_text() == "do-not-read\n"
