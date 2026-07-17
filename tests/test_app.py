"""Security and contract tests for the local HTTP bridge."""

from __future__ import annotations

import io
import wave

from fastapi.testclient import TestClient

from zotero_local_tts.app import create_app
from zotero_local_tts.config import Settings

TOKEN = "test-token"


class FakeEngine:
    def synthesize(self, text: str, model_id: str, voice: str, speed: float) -> bytes:
        del text, model_id, voice, speed
        output = io.BytesIO()
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(24_000)
            wav.writeframes(b"\x00\x00" * 240)
        return output.getvalue()


def client() -> TestClient:
    settings = Settings(token=TOKEN, voices=("Aiden",), allowed_hosts=("testserver",))
    return TestClient(create_app(FakeEngine(), settings))


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def valid_payload() -> dict[str, object]:
    return {
        "model": "qwen3-customvoice-1.7b-8bit",
        "voice": "Aiden",
        "input": "A short academic sentence.",
        "response_format": "wav",
        "speed": 1.0,
    }


def test_requires_bearer_token() -> None:
    response = client().get("/health")
    assert response.status_code == 401


def test_rejects_unlisted_host_even_with_valid_token() -> None:
    response = client().get(
        "/health",
        headers={**auth_headers(), "Host": "attacker.example"},
    )
    assert response.status_code == 400


def test_rejects_browser_origin_by_default() -> None:
    response = client().get(
        "/health",
        headers={**auth_headers(), "Origin": "https://example.com"},
    )
    assert response.status_code == 403


def test_lists_only_allowlisted_voices() -> None:
    response = client().get("/v1/voices", headers=auth_headers())
    assert response.status_code == 200
    assert [voice["id"] for voice in response.json()["voices"]] == ["Aiden"]


def test_returns_wav_audio() -> None:
    response = client().post(
        "/v1/audio/speech",
        headers=auth_headers(),
        json=valid_payload(),
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content.startswith(b"RIFF")


def test_rejects_unlisted_model_and_voice() -> None:
    payload = valid_payload()
    payload["model"] = "arbitrary-model"
    assert (
        client().post("/v1/audio/speech", headers=auth_headers(), json=payload).status_code == 400
    )

    payload = valid_payload()
    payload["voice"] = "arbitrary-voice"
    assert (
        client().post("/v1/audio/speech", headers=auth_headers(), json=payload).status_code == 400
    )


def test_rejects_oversized_text() -> None:
    payload = valid_payload()
    payload["input"] = "x" * 2_001
    response = client().post(
        "/v1/audio/speech",
        headers=auth_headers(),
        json=payload,
    )
    assert response.status_code == 413


def test_rejects_unimplemented_synthesis_speed() -> None:
    payload = valid_payload()
    payload["speed"] = 1.2
    response = client().post(
        "/v1/audio/speech",
        headers=auth_headers(),
        json=payload,
    )
    assert response.status_code == 400
