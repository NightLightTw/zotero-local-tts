"""TTS engine boundary used by the HTTP bridge."""

from __future__ import annotations

import io
import os
from typing import Any, Protocol

import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

from .config import ACADEMIC_PROFILE, DEFAULT_PROFILE, VOICE_LANGUAGES

ACADEMIC_INSTRUCT = (
    "Calm, neutral academic narration. Maintain a steady pace, restrained pitch "
    "variation, consistent volume, and clear articulation."
)

GENERATION_PROFILES: dict[str, dict[str, Any]] = {
    DEFAULT_PROFILE: {},
    ACADEMIC_PROFILE: {
        "instruct": ACADEMIC_INSTRUCT,
        "temperature": 0.7,
        "top_k": 40,
        "top_p": 0.9,
        "repetition_penalty": 1.05,
    },
}


def _generation_options(profile: str, text: str) -> dict[str, Any]:
    options = GENERATION_PROFILES.get(profile)
    if options is None:
        raise SynthesisError(
            "profile_unconfigured",
            "The requested synthesis profile is not configured",
        )
    resolved = dict(options)
    # Qwen can occasionally miss its end token. A length-aware ceiling keeps
    # one Zotero sentence from becoming minutes of repetitive audio, regardless
    # of whether it uses the standard or academic sampling profile.
    resolved["max_tokens"] = min(512, max(192, len(text) * 2))
    return resolved


class SynthesisError(RuntimeError):
    """A synthesis failure with a safe, non-document diagnostic reason."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


class TTSEngine(Protocol):
    def synthesize(
        self, text: str, model_id: str, voice: str, speed: float, profile: str
    ) -> bytes:
        """Return a complete WAV file."""
        ...


class UnconfiguredEngine:
    """Safe placeholder until the MLX adapter is enabled."""

    def synthesize(
        self, text: str, model_id: str, voice: str, speed: float, profile: str
    ) -> bytes:
        del text, model_id, voice, speed, profile
        raise SynthesisError("engine_unconfigured", "MLX-Audio engine is not configured")


class MLXAudioEngine:
    """Lazy, offline-only MLX-Audio adapter returning complete WAV files."""

    def __init__(self) -> None:
        self._model: Any | None = None
        self._model_id: str | None = None

    def _load(self, model_id: str) -> Any:
        if self._model is not None and self._model_id == model_id:
            return self._model
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        try:
            model = load_model(model_id)
        except Exception as error:
            raise SynthesisError(
                "model_unavailable",
                "The allowlisted model is not available in the local Hugging Face cache",
            ) from error
        self._model = model
        self._model_id = model_id
        return model

    def synthesize(
        self, text: str, model_id: str, voice: str, speed: float, profile: str
    ) -> bytes:
        model = self._load(model_id)
        language = VOICE_LANGUAGES.get(voice)
        if language is None:
            raise SynthesisError(
                "voice_language_unconfigured",
                "The requested voice has no configured native language",
            )
        generation_options = _generation_options(profile, text)
        chunks: list[np.ndarray] = []
        sample_rate = int(getattr(model, "sample_rate", 24_000))
        try:
            for result in model.generate(
                text=text,
                voice=voice,
                lang_code=language,
                speed=speed,
                **generation_options,
            ):
                audio = np.asarray(result.audio, dtype=np.float32).squeeze()
                if audio.size:
                    chunks.append(audio)
        except Exception as error:
            raise SynthesisError("generation_failed", "MLX-Audio synthesis failed") from error
        if not chunks:
            raise SynthesisError("empty_audio", "MLX-Audio returned no audio")

        waveform = np.concatenate(chunks)
        max_tokens = generation_options.get("max_tokens")
        if max_tokens is not None:
            duration = waveform.size / sample_rate
            generation_ceiling = float(max_tokens) / 12.5
            if duration >= generation_ceiling * 0.95:
                raise SynthesisError(
                    "generation_limit_reached",
                    "MLX-Audio did not finish synthesis within the safe generation limit",
                )

        output = io.BytesIO()
        sf.write(output, waveform, sample_rate, format="WAV")
        return output.getvalue()
