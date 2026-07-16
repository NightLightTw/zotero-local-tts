# Zotero Local TTS

Local, privacy-first text-to-speech for Zotero 9 using Qwen3-TTS on Apple Silicon.

The project is currently in the specification and prototyping phase. See
[`docs/SPEC.md`](docs/SPEC.md) for the agreed scope, architecture, and acceptance
criteria.

## Development setup

```bash
uv sync
uv run pytest -q
uv run ruff check .
```

The 1.7B model has been validated through the authenticated bridge in fully
offline mode. The command below runs the opt-in integration test after the model
has been downloaded once:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 RUN_MLX_INTEGRATION=1 \
  uv run pytest -q tests/test_integration_mlx.py
```

See [`docs/M0_RESULTS.md`](docs/M0_RESULTS.md) for the first M5 benchmark and
[`docs/ADR-0001-zotero-read-aloud-integration.md`](docs/ADR-0001-zotero-read-aloud-integration.md)
for the proposed Zotero integration strategy.

## Target environment

- Mac with Apple M5 and 24 GB unified memory
- macOS on Apple Silicon
- Zotero 9.0.6
- MLX-Audio
- Qwen3-TTS CustomVoice 1.7B 8-bit, with a 0.6B fallback

## Planned repository layout

```text
zotero-local-tts/
├── docs/                 # Specification and architecture decisions
├── server/               # Local OpenAI-compatible TTS bridge
├── zotero-plugin/        # Zotero 9 extension
├── tests/                # Integration and text-normalization tests
└── samples/              # Non-copyrighted evaluation text and local outputs
```

No model weights, generated audio, API keys, or copyrighted papers should be
committed to this repository.
