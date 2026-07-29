"""Unit tests for MLX-Audio generation profiles."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from zotero_local_tts.config import ACADEMIC_PROFILE, DEFAULT_PROFILE
from zotero_local_tts.engine import ACADEMIC_INSTRUCT, MLXAudioEngine, SynthesisError


class RecordingModel:
    sample_rate = 24_000

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def generate(self, **kwargs: object):
        self.calls.append(kwargs)
        yield SimpleNamespace(audio=np.zeros(240, dtype=np.float32))


class RunawayModel(RecordingModel):
    def generate(self, **kwargs: object):
        self.calls.append(kwargs)
        max_tokens = int(kwargs["max_tokens"])
        yield SimpleNamespace(
            audio=np.zeros(round(max_tokens / 12.5 * self.sample_rate), dtype=np.float32)
        )


def configured_engine(model: RecordingModel) -> MLXAudioEngine:
    engine = MLXAudioEngine()
    engine._model = model
    engine._model_id = "test-model"
    return engine


def test_standard_profile_preserves_sampling_defaults_and_adds_safety_limit() -> None:
    model = RecordingModel()

    configured_engine(model).synthesize(
        "A standard sentence.", "test-model", "Ryan", 1.0, DEFAULT_PROFILE
    )

    assert model.calls == [
        {
            "text": "A standard sentence.",
            "voice": "Ryan",
            "lang_code": "english",
            "speed": 1.0,
            "max_tokens": 192,
        }
    ]


def test_academic_profile_constrains_ryan_generation() -> None:
    model = RecordingModel()

    configured_engine(model).synthesize(
        "An academic sentence.", "test-model", "Ryan", 1.0, ACADEMIC_PROFILE
    )

    assert model.calls == [
        {
            "text": "An academic sentence.",
            "voice": "Ryan",
            "lang_code": "english",
            "speed": 1.0,
            "instruct": ACADEMIC_INSTRUCT,
            "temperature": 0.7,
            "top_k": 40,
            "top_p": 0.9,
            "repetition_penalty": 1.05,
            "max_tokens": 192,
        }
    ]


def test_engine_rejects_unknown_profile() -> None:
    with pytest.raises(SynthesisError) as error:
        configured_engine(RecordingModel()).synthesize(
            "A sentence.", "test-model", "Ryan", 1.0, "unknown"
        )

    assert error.value.reason == "profile_unconfigured"


@pytest.mark.parametrize("profile", [DEFAULT_PROFILE, ACADEMIC_PROFILE])
def test_profiles_reject_generation_that_hits_safety_ceiling(profile: str) -> None:
    with pytest.raises(SynthesisError) as error:
        configured_engine(RunawayModel()).synthesize(
            "A sentence.", "test-model", "Ryan", 1.0, profile
        )

    assert error.value.reason == "generation_limit_reached"
