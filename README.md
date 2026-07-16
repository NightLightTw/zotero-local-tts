# Zotero Local TTS

Local, privacy-first text-to-speech for Zotero 9 using Qwen3-TTS on Apple Silicon.

The authenticated local bridge and a native Zotero Read Aloud provider spike
are working on the target M5/24 GB machine. See [`docs/SPEC.md`](docs/SPEC.md)
for the agreed scope, architecture, and remaining acceptance criteria.

## Development setup

```bash
uv sync
uv run pytest -q
uv run ruff check .
```

If Python reports that it skipped hidden `.pth` files on macOS, clear the
accidental Finder flag and retry:

```bash
chflags nohidden .venv/lib/python3.12/site-packages/*.pth
```

## Run the local bridge

After the model has been downloaded once, normal operation is fully offline:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run zotero-local-tts
```

The first run creates a bearer token at
`~/Library/Application Support/Zotero Local TTS/token`. Keep the bridge running
while using Read Aloud.

## Build and install the Zotero plugin

```bash
./scripts/build-xpi.sh
```

In Zotero, open **Tools → Plugins → Tools for all plugins → Install Plugin From
File…** and select `dist/zotero-local-tts-0.1.2.xpi`. In a PDF, open Read Aloud
options and select:

- Voice Mode: **Standard**
- Voice: **Aiden (Qwen3-TTS, Local)**

Zotero reserves its `Local` voice mode for operating-system voices, so the
project-owned local provider must appear under `Standard`. This categorization
does not change privacy or billing: synthesis stays on `127.0.0.1` and uses no
Zotero credits.

The 1.7B model has been validated through the authenticated bridge in fully
offline mode. The command below runs the opt-in integration test after the model
has been downloaded once:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 RUN_MLX_INTEGRATION=1 \
  uv run pytest -q tests/test_integration_mlx.py
```

See [`docs/M0_RESULTS.md`](docs/M0_RESULTS.md) for the first M5 benchmark,
[`docs/M1_5_RESULTS.md`](docs/M1_5_RESULTS.md) for the Zotero integration test,
and
[`docs/ADR-0001-zotero-read-aloud-integration.md`](docs/ADR-0001-zotero-read-aloud-integration.md)
for the selected Zotero integration strategy.

## Target environment

- Mac with Apple M5 and 24 GB unified memory
- macOS on Apple Silicon
- Zotero 9.0.6
- MLX-Audio
- Qwen3-TTS CustomVoice 1.7B 8-bit, with a 0.6B fallback

## Repository layout

```text
zotero-local-tts/
├── docs/                 # Specification and architecture decisions
├── src/                  # Local authenticated TTS bridge and MLX engine
├── scripts/              # XPI build tooling
├── zotero-plugin/        # Zotero 9 extension
├── tests/                # Integration and text-normalization tests
└── benchmarks/           # Non-copyrighted benchmark inputs and ignored outputs
```

No model weights, generated audio, API keys, or copyrighted papers should be
committed to this repository.
