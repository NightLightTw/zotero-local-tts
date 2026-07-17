# ADR-0001: Reuse Zotero's native Read Aloud controller

Status: Accepted
Date: 2026-07-17

## Context

Zotero 9.0.6 already implements document segmentation, audio prefetch, persistent
audio caching, play/pause/stop behavior, paragraph navigation, spoken-text
highlighting, and saved reading position.

Inspection of the installed Zotero 9.0.6 application found that the private
reader interface dynamically calls `Zotero.Sync.APIClient.prototype` methods
`getReadAloudVoices()` and `getReadAloudAudio()`. The native implementation then
caches audio using a key derived from voice ID and segment text.

Zotero's documented extension surface does not currently expose a public TTS
provider-registration API. Depending on the private method therefore carries an
upgrade risk, but recreating the entire playback controller would duplicate a
large amount of user-facing behavior.

## Proposed decision

Use a Zotero extension that temporarily replaces only those two APIClient
prototype methods and sends audio requests to the authenticated local bridge.
This is smaller than replacing `_getReadAloudRemoteInterface()` itself. Save the
original functions and restore them when the extension shuts down, but only if
the installed functions are still ours.

Zotero 9.0.6 accepts `local` in a remote voice response but excludes remote
`local` voices from the UI; that tier is populated exclusively from browser/OS
speech synthesis. The local Qwen voices are therefore declared in the
`standard` tier and labelled as local. They use zero credits and never contact
Zotero's TTS endpoint. Each of the nine built-in speakers is registered only
for its native-language locale. The extension merges this configuration into
Zotero's original response rather than replacing it, preserving the built-in
Standard and Premium voices. If the original voice listing is unavailable, the
local voice configuration remains usable as a fallback.

The extension must fail closed: if the expected method or return contract is
missing, it must disable the local provider and show a compatibility error. It
must not alter or replace the Zotero application bundle.

## Spike result

The spike passed on Zotero 9.0.6. The extension exposed Aiden, returned complete
WAV Blobs, entered native playback, and triggered Zotero's two-ahead prefetch.
Play/pause and the native Reader UI remained active. The implementation is
version-gated to Zotero 9.0.x, contains a runtime contract check, and restores
the original methods on disable, uninstall, or upgrade.

## Fallback

If the private interface cannot be overridden safely from an extension, build a
standalone player using documented reader UI/event hooks. That alternative must
then explicitly implement and test navigation, highlighting, saved position,
prefetch, cancellation, and persistent caching.

## Consequences

- Far less playback and reader-state code than a standalone player.
- A small compatibility adapter will be required for each incompatible Zotero
  change until an official provider API exists.
- The local bridge should return complete WAV files for native Web Audio
  decoding. Raw PCM streaming remains out of scope for this path.
- The UI category says `Standard` even though the provider is entirely local.
- Listing voices still uses Zotero's original metadata request so the plugin can
  preserve built-in cloud voices; no paper text is included in that request.
