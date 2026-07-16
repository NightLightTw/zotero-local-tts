"""Authenticated loopback HTTP bridge."""

from __future__ import annotations

import asyncio
import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .config import Settings, default_settings
from .engine import TTSEngine, UnconfiguredEngine


class SpeechRequest(BaseModel):
    model: str
    voice: str
    input: str = Field(min_length=1)
    response_format: str = "wav"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


def create_app(
    engine: TTSEngine | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    settings = settings or default_settings()
    engine = engine or UnconfiguredEngine()
    semaphore = asyncio.Semaphore(settings.max_concurrency)
    app = FastAPI(title="Zotero Local TTS", docs_url=None, redoc_url=None)

    async def authorize(
        request: Request,
        authorization: Annotated[str | None, Header()] = None,
        origin: Annotated[str | None, Header()] = None,
    ) -> None:
        host = request.url.hostname or ""
        if host not in settings.allowed_hosts:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Host header")
        if origin and origin not in settings.allowed_origins:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Origin is not allowed")
        expected = f"Bearer {settings.token}"
        if not authorization or not secrets.compare_digest(authorization, expected):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid bearer token")

    auth = Depends(authorize)

    @app.get("/health", dependencies=[auth])
    async def health() -> dict[str, str]:
        return {"status": "ok", "model": settings.model_alias}

    @app.get("/v1/voices", dependencies=[auth])
    async def voices() -> dict[str, list[dict[str, str]]]:
        return {
            "voices": [
                {
                    "id": voice,
                    "name": voice,
                    "language": "en",
                    "model": settings.model_alias,
                }
                for voice in settings.voices
            ]
        }

    @app.post("/v1/audio/speech", dependencies=[auth])
    async def speech(payload: SpeechRequest) -> Response:
        if payload.model != settings.model_alias:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Model is not allowlisted")
        if payload.voice not in settings.voices:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Voice is not allowlisted")
        if payload.response_format != "wav":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only WAV is supported")
        if payload.speed != 1.0:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Synthesis speed control is not implemented; use client playback rate",
            )
        if len(payload.input) > settings.max_text_characters:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "Text is too long")

        async with semaphore:
            try:
                audio = await asyncio.to_thread(
                    engine.synthesize,
                    payload.input,
                    settings.model_id,
                    payload.voice,
                    1.0,
                )
            except RuntimeError as error:
                raise HTTPException(
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                    "Local synthesis is unavailable",
                ) from error
        return Response(audio, media_type="audio/wav")

    return app
