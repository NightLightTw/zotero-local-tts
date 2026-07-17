"""Opt-in integration test against the locally cached MLX model."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from zotero_local_tts.app import create_app
from zotero_local_tts.config import DEFAULT_VOICES, Settings
from zotero_local_tts.engine import MLXAudioEngine


@pytest.mark.skipif(os.environ.get("RUN_MLX_INTEGRATION") != "1", reason="opt-in model test")
def test_cached_qwen_model_returns_all_nine_voices_through_bridge() -> None:
    settings = Settings(
        token="integration-token",
        allowed_hosts=("testserver",),
    )
    client = TestClient(create_app(MLXAudioEngine(), settings))
    native_samples = {
        "Aiden": "Reliable evidence requires careful measurement.",
        "Ryan": "Scientific results should be clear and reproducible.",
        "Vivian": "可靠的证据需要仔细测量。",
        "Serena": "科学结果应该清楚并且可以重现。",
        "Uncle_Fu": "这是一段本地生成的中文语音。",
        "Dylan": "研究方法需要经过严格验证。",
        "Eric": "这项实验提供了新的研究证据。",
        "Ono_Anna": "信頼できる証拠には慎重な測定が必要です。",
        "Sohee": "신뢰할 수 있는 증거에는 세심한 측정이 필요합니다.",
    }

    assert tuple(native_samples) == DEFAULT_VOICES
    for voice, text in native_samples.items():
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": "Bearer integration-token"},
            json={
                "model": settings.model_alias,
                "voice": voice,
                "input": text,
                "response_format": "wav",
                "speed": 1.0,
            },
        )
        assert response.status_code == 200, voice
        assert response.headers["content-type"] == "audio/wav"
        assert response.content.startswith(b"RIFF")
        assert len(response.content) > 1_000
