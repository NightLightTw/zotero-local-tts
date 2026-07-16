"""Opt-in integration test against the locally cached MLX model."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from zotero_local_tts.app import create_app
from zotero_local_tts.config import Settings
from zotero_local_tts.engine import MLXAudioEngine


@pytest.mark.skipif(os.environ.get("RUN_MLX_INTEGRATION") != "1", reason="opt-in model test")
def test_cached_qwen_model_returns_wav_through_bridge() -> None:
    settings = Settings(
        token="integration-token",
        voices=("Aiden",),
        allowed_hosts=("testserver",),
    )
    client = TestClient(create_app(MLXAudioEngine(), settings))
    response = client.post(
        "/v1/audio/speech",
        headers={"Authorization": "Bearer integration-token"},
        json={
            "model": settings.model_alias,
            "voice": "Aiden",
            "input": "Reliable evidence requires careful measurement.",
            "response_format": "wav",
            "speed": 1.0,
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content.startswith(b"RIFF")
    assert len(response.content) > 1_000
