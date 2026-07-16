# ADR-0001: Reuse Zotero's native Read Aloud controller

Status: Proposed, pending executable spike  
Date: 2026-07-17

## Context

Zotero 9.0.6 already implements document segmentation, audio prefetch, persistent
audio caching, play/pause/stop behavior, paragraph navigation, spoken-text
highlighting, and saved reading position.

Inspection of the installed Zotero 9.0.6 application found a private reader
method named `_getReadAloudRemoteInterface(targetWindow)`. It returns an object
with `getVoices`, `getAudio`, `getCreditsRemaining`, and `resetCredits`. The
native implementation obtains remote voice metadata and audio, then caches
audio using a key derived from voice ID and segment text.

Zotero's documented extension surface does not currently expose a public TTS
provider-registration API. Depending on the private method therefore carries an
upgrade risk, but recreating the entire playback controller would duplicate a
large amount of user-facing behavior.

## Proposed decision

Prefer a Zotero extension that overrides or injects the private remote
interface and sends voice/audio requests to the authenticated local bridge.
Keep the override small, version-gated, and reversible.

The extension must fail closed: if the expected method or return contract is
missing, it must disable the local provider and show a compatibility error. It
must not alter or replace the Zotero application bundle.

## Spike exit criteria

1. A development extension can expose one local voice in the native voice UI.
2. Native Read Aloud can request and play a locally returned WAV Blob.
3. Native pause/resume, prefetch, cache, highlight, and saved position continue
   to work.
4. Uninstalling or disabling the extension restores the original method.
5. The override detects Zotero 9.0.6 explicitly and contains a contract test
   that will fail clearly on incompatible later releases.

## Fallback

If the private interface cannot be overridden safely from an extension, build a
standalone player using documented reader UI/event hooks. That alternative must
then explicitly implement and test navigation, highlighting, saved position,
prefetch, cancellation, and persistent caching.

## Consequences

- Far less playback and reader-state code if the spike succeeds.
- A small compatibility adapter will be required for each incompatible Zotero
  change until an official provider API exists.
- The local bridge should return complete WAV files for native Web Audio
  decoding. Raw PCM streaming remains out of scope for this path.
