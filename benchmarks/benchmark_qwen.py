"""Benchmark Qwen3-TTS through MLX-Audio on the local Apple Silicon machine."""

from __future__ import annotations

import argparse
import json
import platform
import resource
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import psutil
import soundfile as sf
from mlx_audio.tts.utils import load_model

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEXT = ROOT / "benchmarks" / "academic_excerpt.txt"
RESULTS = ROOT / "benchmarks" / "results"


@dataclass
class GenerationResult:
    label: str
    elapsed_seconds: float
    time_to_first_result_seconds: float
    audio_duration_seconds: float
    real_time_factor: float
    output_path: str


def machine_info() -> dict[str, Any]:
    """Collect enough machine metadata to make benchmark results comparable."""
    sw_vers = subprocess.run(
        ["sw_vers", "-productVersion"],
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "platform": platform.platform(),
        "macos_version": sw_vers,
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpu_count": psutil.cpu_count(),
        "memory_bytes": psutil.virtual_memory().total,
        "python": platform.python_version(),
    }


def sample_rate_for(model: Any, result: Any) -> int:
    """Read the sample rate across MLX-Audio model/result API variants."""
    for owner in (result, model, getattr(model, "config", None)):
        if owner is None:
            continue
        for name in ("sample_rate", "sampling_rate"):
            value = getattr(owner, name, None)
            if isinstance(value, int) and value > 0:
                return value
    return 24_000


def synthesize(
    model: Any,
    text: str,
    voice: str,
    output_path: Path,
    label: str,
) -> GenerationResult:
    """Generate one WAV and capture latency and RTF."""
    started = time.perf_counter()
    first_result_at: float | None = None
    chunks: list[np.ndarray] = []
    rate: int | None = None

    results = model.generate(text=text, voice=voice, lang_code="english")
    for result in results:
        if first_result_at is None:
            first_result_at = time.perf_counter()
        audio = np.asarray(result.audio, dtype=np.float32).squeeze()
        if audio.size:
            chunks.append(audio)
            rate = rate or sample_rate_for(model, result)

    finished = time.perf_counter()
    if not chunks or first_result_at is None:
        raise RuntimeError("MLX-Audio returned no audio")

    waveform = np.concatenate(chunks)
    rate = rate or 24_000
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, waveform, rate)

    elapsed = finished - started
    duration = len(waveform) / rate
    return GenerationResult(
        label=label,
        elapsed_seconds=round(elapsed, 4),
        time_to_first_result_seconds=round(first_result_at - started, 4),
        audio_duration_seconds=round(duration, 4),
        real_time_factor=round(elapsed / duration, 4),
        output_path=str(output_path.relative_to(ROOT)),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default="mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit",
    )
    parser.add_argument("--voice", default="Aiden")
    parser.add_argument("--text-file", type=Path, default=DEFAULT_TEXT)
    parser.add_argument("--max-characters", type=int, default=300)
    parser.add_argument("--warm-runs", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    text = args.text_file.read_text(encoding="utf-8").strip()
    if args.max_characters > 0 and len(text) > args.max_characters:
        text = text[: args.max_characters].rsplit(" ", 1)[0].rstrip(" ,;:") + "."
    slug = args.model.rsplit("/", 1)[-1]
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RESULTS / f"{timestamp}-{slug}"

    process = psutil.Process()
    rss_before = process.memory_info().rss
    load_started = time.perf_counter()
    model = load_model(args.model)
    load_elapsed = time.perf_counter() - load_started
    rss_after_load = process.memory_info().rss

    cold = synthesize(model, text, args.voice, run_dir / "cold.wav", "cold")
    warm_runs = [
        synthesize(
            model,
            text,
            args.voice,
            run_dir / f"warm-{run_number}.wav",
            f"warm-{run_number}",
        )
        for run_number in range(1, args.warm_runs + 1)
    ]
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    report = {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "model": args.model,
        "voice": args.voice,
        "text_file": str(args.text_file),
        "text_characters": len(text),
        "machine": machine_info(),
        "model_load_seconds": round(load_elapsed, 4),
        "rss_before_bytes": rss_before,
        "rss_after_load_bytes": rss_after_load,
        "rss_model_delta_bytes": max(0, rss_after_load - rss_before),
        "peak_rss_bytes": peak_rss,
        "generations": [asdict(cold), *(asdict(result) for result in warm_runs)],
    }
    report_path = run_dir / "result.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
