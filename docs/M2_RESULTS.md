# M2 — Nine-voice Zotero validation

Date: 2026-07-18
Machine: Apple M5, 24 GB unified memory
Zotero: 9.0.6
Plugin: Zotero Local TTS 0.1.4

## Result

The 0.1.4 XPI installed over 0.1.3, remained enabled after a Zotero restart,
and exposed all nine Qwen3-TTS CustomVoice speakers only in their configured
native-language menus:

- English (United States): Aiden and Ryan
- Chinese: Vivian, Serena, Uncle Fu, Dylan, and Eric
- Japanese: Ono Anna
- Korean: Sohee

Zotero's six original Standard English voices remained visible alongside the
two local English voices. Its original cloud voice response was not replaced.

## Playback verification

- Vivian was selected from the Chinese menu and played through Zotero's native
  Read Aloud controls.
- Sohee was selected from the Korean menu and played through the same controls.
- The authenticated loopback bridge returned HTTP 200 for both voices.
- No paper text or bearer token appeared in application logs.
- After testing, the Reader was restored to English (United States), Aiden, and
  a paused state.

The test bridge was stopped after validation. Normal use still requires the
user to start the bridge as described in the README.
