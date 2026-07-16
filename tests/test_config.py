"""Tests for local secret management."""

import stat

from zotero_local_tts.config import load_or_create_token


def test_token_is_persistent_and_user_only(tmp_path) -> None:
    token_path = tmp_path / "private" / "token"
    first = load_or_create_token(token_path)
    second = load_or_create_token(token_path)

    assert first == second
    assert len(first) >= 32
    assert stat.S_IMODE(token_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(token_path.parent.stat().st_mode) == 0o700
