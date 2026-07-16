# Zotero Local TTS — Product and Technical Specification

Status: Draft v0.1  
Last updated: 2026-07-17

## 1. Objective

Build an offline, natural-sounding read-aloud workflow for Zotero 9.0.6 on an
Apple M5 Mac with 24 GB unified memory. The initial use case is listening to
English academic papers. All document text and generated audio must remain on
the local machine.

The target quality is substantially better than operating-system voices and as
close as practical to a commercial neural TTS service, while preserving
reasonable start-up latency and continuous playback.

## 2. Selected technology

- Runtime: MLX-Audio on Apple Silicon
- Primary model: `mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit`
- Low-latency fallback: `mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit`
- Service boundary: HTTP on loopback only (`127.0.0.1`)
- Service: a thin, project-owned bridge in front of MLX-Audio
- TTS contract: stable project API with OpenAI-compatible `POST /v1/audio/speech`
- Client: Zotero 9 extension that reuses native Read Aloud where feasible; a
  temporary Zotero fork may be used only for early integration research
- Audio format for the MVP: WAV

## 3. Why this design

MLX-Audio uses Apple Silicon efficiently and exposes an OpenAI-compatible API,
which keeps the Zotero integration independent from a particular model. The
same extension should later be able to use another local backend without
rewriting document navigation or playback logic.

Qwen3-TTS CustomVoice 1.7B is the default for fixed high-quality voices. With 24 GB unified memory, it should
fit comfortably alongside Zotero and the local service. The 0.6B model remains
available when lower time-to-first-audio is more important than maximum voice
quality.

Zero-shot voice cloning is a later, separate mode using a Qwen3-TTS Base model.
CustomVoice, Base, and VoiceDesign are not interchangeable model variants and
must have separate cache identities and lifecycle policies.

## 4. Scope

### MVP

1. Start a local MLX-Audio service and load Qwen3-TTS.
2. Put a restricted local bridge in front of MLX-Audio and expose health,
   voice-listing, and speech-generation endpoints on loopback.
3. Complete a Zotero integration spike comparing native Read Aloud provider
   injection with a standalone extension player.
4. Generate English speech from selected or current text in Zotero.
5. Preserve native play, pause, stop, resume, prefetch, highlighting, and saved
   position behavior when the native integration path is selected.
6. Cache audio locally by model, voice, speed, normalization version, and text.
7. Provide conservative academic-text cleanup that can be disabled.
8. Package the Zotero side as an installable `.xpi` extension.

### Later phases

- Read from the current paragraph and continue through a document.
- Highlight the currently spoken sentence or paragraph.
- Restore the last listening position.
- Add configurable citation, footnote, URL, and bibliography handling.
- Add a Qwen3-TTS Base model and user-provided reference audio for zero-shot
  voice cloning, including explicit model-switch latency and memory handling.
- Add a settings UI for model, voice, speed, chunk size, and cache limits.
- Evaluate CosyVoice as an alternative backend.

### Non-goals for the MVP

- Mobile Zotero support.
- Cloud TTS providers.
- Training or fine-tuning a new model.
- Reading equations, tables, or charts semantically.
- Automatic voice cloning without explicit user-provided reference audio.
- Publishing model weights inside the extension.

## 5. Architecture

```text
Zotero 9 extension
  ├── injects a local provider into native Read Aloud when feasible
  ├── preserves native chunking, playback, prefetch, highlight, and position
  ├── applies optional versioned academic-text normalization
  └── calls the authenticated loopback TTS API
                  │
                  ▼
Project-owned local TTS bridge
  ├── exposes stable model aliases and voice metadata
  ├── validates origin, token, size, concurrency, model, and voice
  ├── calls MLX-Audio with offline mode enforced
  └── returns complete WAV audio
                  │
                  ▼
MLX-Audio
  ├── loads an allowlisted Qwen3-TTS model
  ├── generates WAV audio
  └── keeps only a bounded in-memory cache
```

Zotero's native Read Aloud implementation should own persistent audio caching,
document state, playback order, prefetch, highlighting, and saved position when
the provider-injection path proves compatible. The bridge owns model lifecycle,
validation, cancellation, and synthesis. Neither component should require an
internet connection after dependencies and pinned model weights are downloaded.

## 6. Academic-text normalization

Normalization must be conservative and versioned. The original text must never
be modified in Zotero.

Initial rules to evaluate:

- Rejoin line-break hyphenation such as `neuro-` + `science`.
- Normalize whitespace and repeated page artifacts.
- Optionally omit numeric citations such as `[12, 13]`.
- Optionally omit author-year citations such as `(Smith et al., 2024)`.
- Optionally omit DOI and URL strings.
- Detect repeated headers and footers when enough page context is available.
- Preserve abbreviations, decimal numbers, meaningful parentheses, and units.

Every destructive cleanup rule must have an independent setting and tests.

## 7. Chunking and playback

- Split on sentence boundaries, then combine short sentences.
- Initial target: 1–3 sentences or approximately 250–500 characters per chunk.
- Generate the current chunk immediately and prefetch at least one subsequent
  chunk.
- Never split inside abbreviations, decimals, URLs, or common academic initials
  when avoidable.
- Stop must cancel queued work and propagate cancellation to active bridge
  inference; pause must retain the current queue.
- Changing voice, model, speed, or normalization settings invalidates queued
  audio but does not delete unrelated cache entries.

## 8. Local API contract

Required endpoints:

```text
GET  /health
GET  /v1/voices
POST /v1/audio/speech
```

Minimum synthesis request:

```json
{
  "model": "qwen3-customvoice-1.7b-8bit",
  "voice": "Aiden",
  "input": "Text to read aloud.",
  "response_format": "wav",
  "speed": 1.0
}
```

The bridge must bind to `127.0.0.1`, require a per-install random bearer token,
validate `Host` and `Origin`, and reject unexpectedly large or concurrent
requests. It must allowlist model aliases and voices, reject arbitrary local
reference-audio paths, and prevent runtime model downloads. The token and
configuration files must be readable only by the current user.

## 9. Performance targets

These are product targets to validate on the actual M5/24 GB machine, not claims
about the model:

- Benchmark public samples of approximately 100, 300, and 500 characters.
- Run each sample once cold and at least five times warm.
- Warm time-to-first-audio: <= 1.0 second for the 300-character sample.
- Cold model start: <= 30 seconds.
- Sustained generation: faster than real-time at 1.0x playback.
- Inter-chunk audible gap after prefetch: <= 150 ms.
- Combined TTS process peak resident memory: <= 10 GB, with macOS memory
  pressure remaining green during the benchmark.
- Playback must remain responsive while synthesis runs.
- A 30-minute continuous test must have no unbounded memory growth, stuck
  generation, or recurring long inter-chunk gaps.

If the 1.7B model misses the warm-latency target, test 4-bit quantization and
the 0.6B model before changing the architecture.

## 10. Privacy and security

- Bind only to loopback unless the user explicitly changes the configuration.
- Require bearer authentication and strict model/voice allowlists.
- Set Hugging Face offline mode during normal service operation.
- Do not log full document text by default.
- Do not include paper text in error telemetry.
- Store generated audio under a user-local cache directory, not in the Git
  repository or Zotero attachment storage.
- Provide a clear-cache command and configurable size limit.
- Keep reference voice samples local and require explicit opt-in before use.
- Do not clone a person's voice without permission.

## 11. Acceptance criteria

The MVP is complete when:

1. A clean installation can start the local service using documented commands.
2. Zotero 9.0.6 can send selected English text to the service from the reader.
3. The extension can play, pause, resume, and stop generated audio.
4. A multi-paragraph sample plays without recurring long pauses between every
   sentence.
5. No network request leaves the machine during normal synthesis.
6. Restarting Zotero does not require reinstalling the extension.
7. The test suite covers chunking and every enabled destructive normalization
   rule.
8. Setup, removal, model storage, and cache-clearing instructions are documented.
9. The provider integration is tested on Zotero 9.0.6 and one later available
   Zotero 9.0.x release before declaring compatibility.
10. With networking disabled, the installed service starts and synthesizes; an
    observed synthesis run produces no DNS or HTTP traffic and no log contains
    full input text.
11. The repository records exact dependency locks, model revision, source,
    license, and required notices; distributions contain no model weights or
    reference voice recordings.

## 12. Milestones

### M0 — Model benchmark

- Install MLX-Audio in an isolated environment.
- Benchmark Qwen3-TTS 1.7B 8-bit and 0.6B with the same English paper excerpt.
- Record cold start, warm first-audio latency, RTF, memory use, and subjective
  listening notes.
- Select the default model and voice.

### M1 — Local service

- Lock the API contract.
- Add model lifecycle, validation, caching, and health reporting.
- Add automated API tests.

### M1.5 — Zotero native integration spike

- Inspect Zotero 9.0.6 native Read Aloud provider injection behavior.
- Prototype local implementations of voice listing and audio retrieval.
- Compare private native-provider injection against a standalone player.
- Record the chosen path and upgrade risk in an architecture decision record.

### M2 — Zotero integration prototype

- Read selected text.
- Implement playback controls and a two-chunk queue.
- Validate behavior against Zotero 9.0.6.

### M3 — Installable extension

- Package as `.xpi`.
- Add preferences and error handling.
- Document installation and removal.

### M4 — Academic listening quality

- Add tested normalization options.
- Add position tracking and current-text highlighting.
- Conduct a long-paper listening test.

## 13. Open decisions

- Whether another Qwen voice materially improves on the accepted `Aiden`
  baseline during long-form listening; this is not an MVP blocker.
- Whether the official Zotero reader exposes enough stable extension hooks for
  full read-position synchronization without patching Zotero itself.
- Whether WAV plus native prefetch meets the latency target; true PCM streaming
  is a separate architecture only if that test fails.
