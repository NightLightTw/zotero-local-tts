# M0 model benchmark

The benchmark keeps a model loaded across all generations. Model loading is
timed separately, followed by one cold generation and five warm generations of
the same approximately 300-character sample.

```bash
uv sync --no-editable

uv run --no-sync python benchmarks/benchmark_qwen.py \
  --model mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit

uv run --no-sync python benchmarks/benchmark_qwen.py \
  --model mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit
```

Generated audio and machine-readable JSON are written to `benchmarks/results/`
and ignored by Git. Listen to representative cold and warm WAV files from both
model runs before selecting the default model; latency alone is not the product
goal.

The reported `time_to_first_result_seconds` measures the first audio result
yielded by MLX-Audio's Python generator. It is not necessarily the same as true
streaming time-to-first-sample. The current HTTP bridge returns complete WAV
files; streaming remains a separate future evaluation.
