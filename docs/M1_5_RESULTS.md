# M1.5 Zotero native integration results

Date: 2026-07-17
Machine: Apple M5, 24 GB unified memory
Zotero: 9.0.6
Plugin: Zotero Local TTS 0.1.3

## Result

The native provider-injection spike passed. Zotero displayed
`Aiden (Qwen3-TTS, Local)` in Read Aloud, requested audio from the authenticated
loopback bridge, received WAV responses, and entered native playback. The
bridge logs showed one current-segment request followed by two successful
prefetch requests.

The working integration replaces only:

- `Zotero.Sync.APIClient.prototype.getReadAloudVoices`
- `Zotero.Sync.APIClient.prototype.getReadAloudAudio`

The original methods are retained and restored during plugin shutdown. The
plugin refuses to activate outside Zotero 9.0.x or if either expected method is
missing.

The final provider calls Zotero's original voice-list method and prepends Aiden
to its `standard` configurations. Existing Standard and Premium voices are
therefore preserved. If the metadata request fails, it falls back to an
Aiden-only response so offline local synthesis remains available.

## Zotero tier limitation

Zotero parses `standard`, `premium`, and `local` from its remote response, but
the 9.0.6 UI constructs the `Local` list only from browser/operating-system
voices. Remote voices marked `local` are discarded. Aiden must therefore be
declared as `standard`; its visible label includes `Local`, its credits per
minute are zero, and its audio still comes exclusively from `127.0.0.1:8766`.

## Installation findings

- Zotero 9 requires `applications.zotero.update_url` in `manifest.json`, even
  for a manually installed local XPI.
- Bootstrap sandboxes already inject `Services`; redeclaring it with a top-level
  `const` prevents the bootstrap file from loading.
- Updating a provider does not refresh voice data already held by an open
  Reader. Restart Zotero or reopen the Reader after a provider update.

## Verified behavior

- XPI installs and remains enabled after restart.
- The running prototype method is the plugin replacement, confirmed in the
  Zotero Browser Console.
- The Standard menu simultaneously shows Aiden and Zotero's original six
  Standard voices; the original Premium response remains untouched.
- Voice mode is `Standard` and voice is `Aiden (Qwen3-TTS, Local)`.
- Authenticated `POST /v1/audio/speech` requests returned HTTP 200 during
  current-segment playback and prefetch.
- Native play/pause controls work.
- No paper text or bearer token was written to application logs.

## Remaining work

- Add a macOS LaunchAgent or equivalent supported lifecycle so the bridge starts
  automatically and stays available after login.
- Add user-visible bridge-offline and synthesis-failure messages.
- Measure sentence-level gaps during a longer paper and tune segmentation if
  prefetch does not hide the current non-streaming generation latency.
- Verify cache reuse, saved position, and highlighting in a repeatable automated
  or manual acceptance script.
