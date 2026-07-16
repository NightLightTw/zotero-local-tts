# M0 benchmark results

Date: 2026-07-17  
Machine: Apple M5, 24 GB unified memory, macOS 26.5.2  
Runtime: Python 3.12.10, MLX-Audio 0.4.5

## Qwen3-TTS CustomVoice 1.7B 8-bit

- Model: `mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit`
- Snapshot: `41d3337e8b7f2843a75841595fc14e4b9a7a4b96`
- Voice: `Aiden`
- Benchmark text: 299 characters of public, synthetic academic prose
- Model load time: 1.21 seconds from the local cache
- Model RSS increase after load: 3.18 GB
- Five-run warm mean synthesis time: 9.45 seconds
- Five-run warm mean generated-audio duration: approximately 20 seconds
- Five-run warm mean RTF: 0.470
- Five-run warm mean time to first non-streaming result: 9.43 seconds

An RTF of 0.470 means the model generates audio at roughly 2.1 times playback
speed on this machine. Memory use is comfortably inside the project target.

The non-streaming first-result latency does not meet the one-second target. This
metric represents a complete generated segment, not true time-to-first-sample.
The next latency work is therefore:

1. Measure MLX-Audio's `stream=True` output with 100- and 300-character chunks.
2. Measure Zotero native prefetch using complete WAV responses.
3. Prefer shorter native segments if prefetch hides synthesis time adequately.
4. Consider a streaming player only if WAV plus native prefetch fails.

## Offline bridge verification

The project-owned authenticated bridge was tested with both
`HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`. It loaded the cached model,
accepted an allowlisted request, generated audio, and returned a valid WAV
response. The integration test is opt-in because it loads several gigabytes of
model state.

## 0.6B status

The 0.6B comparison is pending. The initial Hugging Face metadata request became
stuck establishing an IPv6 connection before any model files were downloaded,
so it was stopped without changing the 1.7B result. The comparison should be
retried when Hub connectivity is stable; it is not required to proceed with the
primary 1.7B integration spike.
