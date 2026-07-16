"""TTS engine boundary used by the HTTP bridge."""

from __future__ import annotations

import io
import os
from typing import Any, Protocol

import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model


class TTSEngine(Protocol):
    def synthesize(self, text: str, model_id: str, voice: str, speed: float) -> bytes:
        """Return a complete WAV file."""
        ...


class UnconfiguredEngine:
    """Safe placeholder until the MLX adapter is enabled."""

    def synthesize(self, text: str, model_id: str, voice: str, speed: float) -> bytes:
        del text, model_id, voice, speed
        raise RuntimeError("MLX-Audio engine is not configured")


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
            raise RuntimeError(
                "The allowlisted model is not available in the local Hugging Face cache"
            ) from error
        self._model = model
        self._model_id = model_id
        return model

    def synthesize(self, text: str, model_id: str, voice: str, speed: float) -> bytes:
        model = self._load(model_id)
        chunks: list[np.ndarray] = []
        sample_rate = int(getattr(model, "sample_rate", 24_000))
        try:
            for result in model.generate(
                text=text,
                voice=voice,
                lang_code="english",
                speed=speed,
            ):
                audio = np.asarray(result.audio, dtype=np.float32).squeeze()
                if audio.size:
                    chunks.append(audio)
        except Exception as error:
            raise RuntimeError("MLX-Audio synthesis failed") from error
        if not chunks:
            raise RuntimeError("MLX-Audio returned no audio")

        output = io.BytesIO()
        sf.write(output, np.concatenate(chunks), sample_rate, format="WAV")
        return output.getvalue()
