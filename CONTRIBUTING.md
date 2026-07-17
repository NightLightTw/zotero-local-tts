# Contributing

Thanks for helping improve Zotero Local TTS.

## Development setup

The supported development environment is an Apple Silicon Mac with Python 3.12
and `uv`:

```bash
git clone https://github.com/NightLightTw/zotero-local-tts.git
cd zotero-local-tts
uv sync --no-editable
uv run pytest -q
uv run ruff check .
node --check zotero-plugin/bootstrap.js
./scripts/build-xpi.sh
```

The real-model test is opt-in and requires the pinned model to be present in the
local Hugging Face cache:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 RUN_MLX_INTEGRATION=1 \
  uv run pytest -q tests/test_integration_mlx.py
```

## Pull requests

- Keep changes focused and document user-visible behavior.
- Add tests for security boundaries, API changes, or destructive text cleanup.
- Preserve the Zotero version gate and reversible method restoration.
- Do not commit model weights, generated audio, bearer tokens, API keys, or
  copyrighted/private paper text.
- Record new runtime components and model revisions in
  `docs/THIRD_PARTY.md`.

Use synthetic or clearly redistributable text and audio in tests and benchmarks.
