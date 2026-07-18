# Zotero Local TTS

Natural, private Read Aloud for Zotero 9 using Qwen3-TTS and MLX on Apple
Silicon.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Platform: Apple Silicon](https://img.shields.io/badge/Platform-Apple%20Silicon-black.svg)](#requirements)
[![Zotero: 9.0.x](https://img.shields.io/badge/Zotero-9.0.x-cc2936.svg)](#compatibility-and-current-limitations)

Zotero Local TTS connects Zotero's native PDF Read Aloud controls to a local
Qwen3-TTS model. Zotero still handles sentence navigation, highlighting,
play/pause, playback speed, caching, and prefetch. When a Qwen3-TTS local voice
is selected, the paper text and generated audio stay on your Mac.

> [!IMPORTANT]
> This is an early, tested prototype for Zotero 9.0.x on Apple Silicon. It uses
> private Zotero APIs. The included macOS LaunchAgent keeps the local bridge
> available after installation and across logins.

## Contents

- [Requirements](#requirements)
- [Quick start](#quick-start)
- [How it works](#how-it-works)
- [Privacy and security](#privacy-and-security)
- [Performance](#performance-on-the-validated-mac)
- [Compatibility and limitations](#compatibility-and-current-limitations)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Roadmap](#roadmap)
- [License](#license)

## Why use it?

- Higher-quality English speech than typical operating-system voices.
- Offline synthesis after the one-time model download.
- Native Zotero Read Aloud controls instead of a separate audio player.
- An authenticated loopback API bound to `127.0.0.1`.
- No model weights, paper text, audio, or bearer tokens stored in this repo.

## Requirements

- An Apple Silicon Mac. The validated machine is an M5 with 24 GB memory.
- macOS and Zotero 9.0.x. The validated Zotero version is 9.0.6.
- Python 3.12 and [uv](https://docs.astral.sh/uv/).
- Node.js 20 or newer for the plugin runtime-contract test.
- About 3.1 GB of free space for the default model, plus the Python environment.
- Internet access for cloning, initial dependency/model downloads, and Zotero's
  optional cloud voices or update checks. Qwen3-TTS local voices work offline
  after setup.

Intel Macs, Windows, Linux, Zotero 8, and Zotero 10 are not currently
supported.

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/NightLightTw/zotero-local-tts.git
cd zotero-local-tts
uv sync --no-editable
```

The non-editable installation verifies the same wheel contents used by the
command-line entry point and avoids macOS file-sync metadata issues with
editable-install `.pth` files.

### 2. Download the model once

```bash
uv run --no-sync hf download \
  mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit \
  --revision 41d3337e8b7f2843a75841595fc14e4b9a7a4b96
```

The normal bridge runs with Hugging Face and Transformers offline modes
enabled, so it will fail closed rather than downloading a model unexpectedly.

### 3. Build the Zotero plugin

```bash
./scripts/build-xpi.sh
```

The command prints the path to an XPI such as
`dist/zotero-local-tts-0.1.5.xpi`.

### 4. Install the plugin

In Zotero:

1. Open **Tools → Plugins**.
2. Open **Tools for all plugins** (the gear menu).
3. Choose **Install Plugin From File…**.
4. Select the XPI from this repository's `dist/` directory.
5. Confirm that **Zotero Local TTS** is enabled.

### 5. Install and start the local bridge

```bash
uv run --no-sync zotero-local-tts install-service
```

This installs a per-user macOS LaunchAgent, starts the bridge immediately, and
restarts it after login or an unexpected exit. It always enables Hugging Face
and Transformers offline modes. The terminal does not need to remain open.
The LaunchAgent records the current `.venv` Python as an absolute path, so keep
this checkout at the same location. Before moving the project, uninstall the
service and reinstall it from the new location.

On its first start, the bridge creates a random bearer token at:

```text
~/Library/Application Support/Zotero Local TTS/token
```

The directory is restricted to mode `0700` and the token to `0600`. Confirm the
background service is loaded with:

```bash
uv run --no-sync zotero-local-tts service-status
```

For development, the foreground bridge remains available as
`uv run --no-sync zotero-local-tts serve`.

### 6. Select a local voice in Zotero

Open a PDF, start Read Aloud, then choose:

- **Voice Mode:** Standard
- **Language:** choose English, Chinese, Japanese, or Korean
- **Voice:** choose one of the Qwen3-TTS voices listed for that language

Zotero 9.0.6 reserves its `Local` mode for browser/operating-system voices and
discards remote-provider voices marked `local`. The plugin therefore appears
under `Standard`, but it uses zero Zotero credits and sends synthesis requests
only to `127.0.0.1`. The nine built-in speakers are restricted to their native
language menus: Aiden/Ryan for English; Vivian/Serena/Uncle Fu/Dylan/Eric for
Chinese; Ono Anna for Japanese; and Sohee for Korean. Zotero's existing
Standard and Premium voices remain available when Zotero's voice metadata is
reachable; selecting one of them uses Zotero's original cloud behavior.

## How it works

```text
Zotero PDF Reader
  └─ native sentence selection, playback, speed, cache, highlight, prefetch
       │
       │ authenticated POST /v1/audio/speech
       ▼
Local bridge on 127.0.0.1:8766
  └─ validates host, origin, token, model, voice, and size; serializes inference
       │
       ▼
MLX-Audio + Qwen3-TTS CustomVoice 1.7B 8-bit
  └─ returns a complete WAV file to Zotero
```

The Zotero plugin temporarily replaces two private API-client methods:

- `Zotero.Sync.APIClient.prototype.getReadAloudVoices`
- `Zotero.Sync.APIClient.prototype.getReadAloudAudio`

Disabling, upgrading, or uninstalling the plugin restores the original methods.
The application bundle and Zotero database are not modified.

## Privacy and security

| Boundary | Behavior |
| --- | --- |
| Network binding | Loopback only: `127.0.0.1:8766` |
| Authentication | Per-install random bearer token |
| Browser requests | Origins rejected by default |
| Model loading | Allowlisted model and offline-only normal operation |
| Voice selection | Nine allowlisted speakers, restricted to native-language menus |
| Input size | Maximum 2,000 characters per request |
| Logs | Paper text and bearer tokens are not logged |
| Audio | Returned to Zotero as WAV; not committed to this repository |

Zotero may independently fetch its original voice metadata and check the
plugin's GitHub update URL. Paper text is not included in those requests. If you
select a Zotero cloud voice instead of a Qwen3-TTS local voice, Zotero's normal
cloud TTS privacy behavior applies. Do not clone or distribute another person's
voice without permission.

The update URL becomes functional when a tagged GitHub Release publishes its
XPI and `updates.json`; source installations do not depend on it.

## Performance on the validated Mac

Qwen3-TTS CustomVoice 1.7B 8-bit, Aiden, Apple M5 with 24 GB memory:

| Metric | Result |
| --- | ---: |
| Model load from local cache | 1.21 s |
| Additional resident memory after load | 3.18 GB |
| Warm synthesis, 299 characters | 9.45 s |
| Generated audio duration | about 20 s |
| Real-time factor | 0.470 (about 2.1× real time) |

The bridge currently returns complete WAV files rather than streaming samples.
Zotero's native two-segment prefetch worked in the integration test, but long
paper listening and sentence-gap tuning remain ongoing work.

## Compatibility and current limitations

- The plugin is version-gated to Zotero 9.0.x and tested on 9.0.6.
- It uses private Zotero APIs that may change without notice.
- English academic papers remain the primary validated listening workflow; all
  nine built-in voices are available in their native-language menus.
- Zotero does not expose an extension point for third-party voices in its true
  `Local` tier, so Qwen3-TTS voices must appear in `Standard` on Zotero 9.0.x.
- Zotero's inline failure text is limited to its built-in error categories; the
  plugin displays a separate local diagnostic for bridge, token, or model errors.
- Voice cloning, streaming, academic-text cleanup, and cache
  management are planned rather than complete.

## Troubleshooting

### Local voices do not appear

- Confirm **Zotero Local TTS 0.1.5** is enabled under **Tools → Plugins**.
- Restart Zotero after installing or updating the XPI; an already-open Reader
  can retain its previous voice list.
- Choose **Voice Mode: Standard**, not Local.

### Read Aloud shows a local bridge or synthesis error

- Confirm the background service is loaded:

  ```bash
  uv run --no-sync zotero-local-tts service-status
  ```

- Check `~/Library/Application Support/Zotero Local TTS/bridge-error.log`.
- Check the authenticated health endpoint without printing the token:

  ```bash
  token=$(<"$HOME/Library/Application Support/Zotero Local TTS/token")
  curl --fail --silent --show-error \
    -H "Authorization: Bearer $token" \
    http://127.0.0.1:8766/health
  ```

- If the bridge says the model is unavailable, repeat the one-time model
  download command from Quick Start.

### Port 8766 is already in use

Only run one bridge instance. Find the existing process with:

```bash
lsof -nP -iTCP:8766 -sTCP:LISTEN
```

## Remove the prototype

1. Pause Read Aloud and stop/remove the background service:

   ```bash
   uv run --no-sync zotero-local-tts uninstall-service
   ```

2. Open **Tools → Plugins** in Zotero.
3. Disable or remove **Zotero Local TTS**.

If the checkout or `.venv` was removed before running the uninstaller, use the
macOS fallback and then remove the stale plist:

```bash
launchctl bootout "gui/$(id -u)/io.github.nightlighttw.zotero-local-tts"
rm -f ~/Library/LaunchAgents/io.github.nightlighttw.zotero-local-tts.plist
```

The original Zotero Read Aloud methods are restored when the plugin shuts down.
The downloaded model, local token, and bridge logs remain on disk until removed
manually.

## Documentation

- [Product and technical specification](docs/SPEC.md)
- [M5 model benchmark](docs/M0_RESULTS.md)
- [Zotero native integration results](docs/M1_5_RESULTS.md)
- [Nine-voice Zotero validation](docs/M2_RESULTS.md)
- [Background service and offline error validation](docs/M3_RESULTS.md)
- [Architecture decision: reuse native Read Aloud](docs/ADR-0001-zotero-read-aloud-integration.md)
- [Third-party components and model revision](docs/THIRD_PARTY.md)

## Development

Run the complete fast test and lint suite:

```bash
uv sync --no-editable
uv run --no-sync pytest -q
uv run --no-sync ruff check .
node --check zotero-plugin/bootstrap.js
./scripts/build-xpi.sh
```

Run the real model integration test after downloading the pinned model:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 RUN_MLX_INTEGRATION=1 \
  uv run --no-sync pytest -q tests/test_integration_mlx.py
```

Generated audio, model weights, XPI files, wheels, tokens, and private paper
content are intentionally ignored by Git.

## Project layout

```text
zotero-local-tts/
├── src/zotero_local_tts/   # Authenticated bridge and MLX engine
├── zotero-plugin/          # Zotero bootstrap extension source
├── scripts/                # XPI build tooling
├── tests/                  # API, security, packaging, and model tests
├── benchmarks/             # Public benchmark input and runner
└── docs/                   # Specification, decisions, and test results
```

## Roadmap

- Long-paper gap, cache, highlighting, and saved-position validation.
- Conservative, optional academic-text normalization.
- Streaming evaluation if native WAV prefetch is insufficient.
- Qwen3-TTS Base support for explicitly authorized zero-shot voice cloning.

## License

Project-owned source code and documentation are licensed under the
[Apache License 2.0](LICENSE). Model weights and dependencies retain their own
licenses and are not redistributed in the plugin; see
[docs/THIRD_PARTY.md](docs/THIRD_PARTY.md).

## Acknowledgements

Built on [MLX-Audio](https://github.com/Blaizzy/mlx-audio),
[Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS), and
[Zotero](https://www.zotero.org/).
