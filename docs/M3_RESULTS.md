# M3 Background Service and Offline Error Validation

Date: 2026-07-18

Plugin: Zotero Local TTS 0.1.5

Host: Apple M5, 24 GB unified memory

Client: Zotero 9.0.6 on macOS

## Result

Version 0.1.5 replaced the manual bridge lifecycle with a per-user macOS
LaunchAgent. The installed job starts the project virtual environment directly,
sets both Hugging Face offline variables, listens only on `127.0.0.1:8766`, and
restarts after an unexpected process exit.

The Zotero plugin no longer maps every local failure to Zotero's `network`
category. A bridge, token, or model failure now produces a throttled local
diagnostic, while the native inline error uses `unknown` instead of incorrectly
instructing an offline user to check the internet connection.

## Automated validation

- `pytest`: 24 passed, 1 skipped in the fast suite.
- `ruff check .`: passed.
- `node --check zotero-plugin/bootstrap.js`: passed.
- XPI build: `dist/zotero-local-tts-0.1.5.xpi`.
- Live security probe: unauthenticated `/openapi.json` returned HTTP 404 and
  unauthenticated `/health` returned HTTP 401.
- Real cached-model integration: all nine allowlisted voices returned valid WAV
  responses with network-download modes disabled.

## Service validation

- `install-service` installed and loaded
  `io.github.nightlighttw.zotero-local-tts`.
- `service-status` reported `running`.
- `launchctl` showed `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`.
- `lsof` showed a single listener on `127.0.0.1:8766` and no external TCP
  connection owned by the bridge.
- After the bridge PID was terminated, launchd started a replacement process
  automatically and the authenticated health endpoint returned HTTP 200.
- Reinstall testing exposed a transient launchd post-bootout I/O error; the
  installer now retries `bootstrap` with bounded backoff.
- A real Aiden synthesis returned 24 kHz, mono, 16-bit PCM WAV audio.

## Zotero UI validation

The 0.1.5 XPI installed over 0.1.4 and remained enabled. In Zotero's native
Reader controls:

- Chinese displayed Vivian, Serena, Uncle Fu, Dylan, and Eric alongside the
  original Zotero Standard voices.
- Selecting Serena generated a local sample with HTTP 200 and no inline error.
- Switching to English (US) selected Aiden and generated local Read Aloud audio
  with HTTP 200.
- The final reviewed XPI was reinstalled and Ryan, Aiden, Serena, and Vivian
  each generated another local sample with HTTP 200.
- Playback changed from Play to Pause and back without a bridge or internet
  connection warning.

The final reviewed end state was Chinese, Vivian, Standard mode, idle with the
Play control shown, and the LaunchAgent still running.
