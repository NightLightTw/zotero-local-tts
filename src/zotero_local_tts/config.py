"""Configuration and local bearer-token management."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / "Library" / "Application Support" / "Zotero Local TTS"

VOICE_LOCALES = {
    "Aiden": "en-US",
    "Ryan": "en-US",
    "Vivian": "zh-CN",
    "Serena": "zh-CN",
    "Uncle_Fu": "zh-CN",
    "Dylan": "zh-CN",
    "Eric": "zh-CN",
    "Ono_Anna": "ja-JP",
    "Sohee": "ko-KR",
}

VOICE_LANGUAGES = {
    "Aiden": "english",
    "Ryan": "english",
    "Vivian": "chinese",
    "Serena": "chinese",
    "Uncle_Fu": "chinese",
    "Dylan": "chinese",
    "Eric": "chinese",
    "Ono_Anna": "japanese",
    "Sohee": "korean",
}

DEFAULT_VOICES = tuple(VOICE_LOCALES)


@dataclass(frozen=True)
class Settings:
    token: str
    host: str = "127.0.0.1"
    port: int = 8766
    max_text_characters: int = 2_000
    max_concurrency: int = 1
    model_alias: str = "qwen3-customvoice-1.7b-8bit"
    model_id: str = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit"
    voices: tuple[str, ...] = DEFAULT_VOICES
    allowed_origins: tuple[str, ...] = ()
    allowed_hosts: tuple[str, ...] = ("127.0.0.1", "localhost", "::1")


def load_or_create_token(path: Path | None = None) -> str:
    """Return a persistent per-install token stored with user-only permissions."""
    token_path = path or DEFAULT_DATA_DIR / "token"
    token_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    token_path.parent.chmod(0o700)
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(token_path, os.O_RDONLY | no_follow)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, encoding="utf-8") as token_file:
            token = token_file.read().strip()
        if token:
            return token
    except FileNotFoundError:
        pass

    token = secrets.token_urlsafe(32)
    descriptor = os.open(
        token_path,
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC | no_follow,
        0o600,
    )
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as token_file:
        token_file.write(token + "\n")
    return token


def default_settings() -> Settings:
    return Settings(token=load_or_create_token())
