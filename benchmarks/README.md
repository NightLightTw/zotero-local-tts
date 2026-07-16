# M0 model benchmark

The benchmark keeps a model loaded across all generations. Model loading is
timed separately, followed by one cold generation and five warm generations of
the same approximately 300-character sample.

```bash
uv sync

uv run python benchmarks/benchmark_qwen.py \
  --model mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit

uv run python benchmarks/benchmark_qwen.py \
  --model mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit
```

Generated audio and machine-readable JSON are written to `benchmarks/results/`
and ignored by Git. Listen to both WAV files before selecting the default model;
latency alone is not the product goal.

The reported `time_to_first_result_seconds` measures the first audio result
yielded by MLX-Audio's Python generator. It is not necessarily the same as true
streaming time-to-first-sample, which will be measured separately when the local
HTTP service is implemented.
