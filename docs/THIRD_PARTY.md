# Third-party components

This file records the current high-level runtime inventory and is not legal
advice. Exact Python versions are locked in `uv.lock`; a machine-readable SBOM
should be generated before a tagged binary release.

Project-owned source code and documentation are licensed under Apache-2.0.

| Component | Purpose | License | Distribution policy |
| --- | --- | --- | --- |
| MLX-Audio | Apple Silicon TTS runtime and API foundation | MIT | Installed dependency; preserve notices |
| Qwen3-TTS MLX weights | Offline TTS model | Apache-2.0 | Download separately; do not bundle in `.xpi` |
| Zotero | Host application and reader integration reference | AGPL-3.0 | Do not redistribute a modified app for the MVP |

Before a tagged binary release, generate a dependency inventory from the locked
environment. The exact default Hugging Face repository and snapshot are recorded
below.

## Currently validated model

- Repository: `mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit`
- Snapshot: `41d3337e8b7f2843a75841595fc14e4b9a7a4b96`
- License declared by model repository: Apache-2.0
- Local weight size: approximately 3.08 GB including tokenizer files
- Bundling policy: download separately into the user's Hugging Face cache
