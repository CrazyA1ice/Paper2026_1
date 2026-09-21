from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from src.data import SlidingWindowDataset, load_npz
from src.models import build_model


MODEL_LABELS = {
    "dlinear": "DLinear",
    "dlinear_scale_static": "固定等权多尺度",
    "dlinear_scale": "自适应多尺度",
}
DATA_PATHS = {
    "abilene": Path("data/processed/abilene_1hour.npz"),
    "geant": Path("data/processed/geant_1hour.npz"),
}


def split_prediction(output):
    return output[0] if isinstance(output, tuple) else output


def hardware_record(device: torch.device) -> dict[str, object]:
    record: dict[str, object] = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "device_type": device.type,
    }
    if device.type == "cuda":
        props = torch.cuda.get_device_properties(device)
        record.update(
            {
                "device_name": props.name,
                "cuda_runtime": torch.version.cuda,
                "total_memory_bytes": props.total_memory,
            }
        )
    else:
        record["device_name"] = platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown CPU")
        record["torch_num_threads"] = torch.get_num_threads()
    return record


@torch.inference_mode()
def benchmark_checkpoint(
    *,
    root: Path,
    dataset_name: str,
    model_name: str,
    seed: int,
    batch_size: int,
    warmup_steps: int,
    repeats: int,
    device: torch.device,
) -> dict[str, object]:
    arrays = load_npz(root / DATA_PATHS[dataset_name])
    dataset = SlidingWindowDataset(arrays["test"], input_len=96, pred_len=24)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    batches = [history.to(device) for history, _ in loader]
    n_channels = int(arrays["test"].shape[1])

    model = build_model(
        model_name,
        input_len=96,
        pred_len=24,
        n_channels=n_channels,
        device=device,
    ).to(device)
    checkpoint = root / "results" / dataset_name / f"{model_name}_seed{seed}" / "best_model.pt"
    model.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True))
    model.eval()
    parameters = sum(parameter.numel() for parameter in model.parameters())

    for step in range(warmup_steps):
        split_prediction(model(batches[step % len(batches)]))
    if device.type == "cuda":
        torch.cuda.synchronize(device)

    repeat_seconds = []
    for _ in range(repeats):
        if device.type == "cuda":
            start_event = torch.cuda.Event(enable_timing=True)
            end_event = torch.cuda.Event(enable_timing=True)
            start_event.record()
            for history in batches:
                split_prediction(model(history))
            end_event.record()
            torch.cuda.synchronize(device)
            repeat_seconds.append(start_event.elapsed_time(end_event) / 1000.0)
        else:
            started = time.perf_counter()
            for history in batches:
                split_prediction(model(history))
            repeat_seconds.append(time.perf_counter() - started)

    batch_count = len(batches)
    latency_ms = [seconds / batch_count * 1000 for seconds in repeat_seconds]
    throughput = [len(dataset) / seconds for seconds in repeat_seconds]
    return {
        "dataset": dataset_name,
        "model": model_name,
        "model_label": MODEL_LABELS[model_name],
        "seed": seed,
        "parameters": parameters,
        "test_windows": len(dataset),
        "batch_size": batch_size,
        "batch_count": batch_count,
        "warmup_steps": warmup_steps,
        "timed_repeats": repeats,
        "batch_latency_ms_mean": statistics.mean(latency_ms),
        "batch_latency_ms_sd": statistics.stdev(latency_ms),
        "throughput_samples_s_mean": statistics.mean(throughput),
        "throughput_samples_s_sd": statistics.stdev(throughput),
        "repeat_seconds": repeat_seconds,
        "checkpoint": str(checkpoint.relative_to(root)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--warmup-steps", type=int, default=20)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--output-dir", default="results/inference_benchmark")
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    parser.add_argument("--cpu-threads", type=int, default=1)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    if device.type == "cpu":
        torch.set_num_threads(args.cpu_threads)
        torch.set_num_interop_threads(1)
    torch.manual_seed(20260921)
    np.random.seed(20260921)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(20260921)

    rows = []
    for dataset_name in ("abilene", "geant"):
        for model_name in MODEL_LABELS:
            for seed in range(42, 50):
                print(f"benchmark dataset={dataset_name} model={model_name} seed={seed}", flush=True)
                rows.append(
                    benchmark_checkpoint(
                        root=root,
                        dataset_name=dataset_name,
                        model_name=model_name,
                        seed=seed,
                        batch_size=args.batch_size,
                        warmup_steps=args.warmup_steps,
                        repeats=args.repeats,
                        device=device,
                    )
                )

    raw = pd.DataFrame(rows)
    raw.to_csv(output_dir / "inference_benchmark_raw.csv", index=False)
    summary = (
        raw.groupby(["dataset", "model", "model_label", "parameters"], as_index=False)
        .agg(
            latency_ms_mean=("batch_latency_ms_mean", "mean"),
            latency_ms_sd_across_seeds=("batch_latency_ms_mean", "std"),
            throughput_samples_s_mean=("throughput_samples_s_mean", "mean"),
            throughput_samples_s_sd_across_seeds=("throughput_samples_s_mean", "std"),
            seeds=("seed", "count"),
        )
        .sort_values(["dataset", "parameters"])
    )
    summary.to_csv(output_dir / "inference_benchmark_summary.csv", index=False)
    metadata = {
        "scope": "checkpoint-only inference benchmark; no training",
        "timing_scope": "model forward passes on preloaded device tensors; data loading and host-to-device transfer excluded",
        "timing_backend": "CUDA events" if device.type == "cuda" else "time.perf_counter",
        "input_len": 96,
        "pred_len": 24,
        "batch_size": args.batch_size,
        "warmup_steps_per_checkpoint": args.warmup_steps,
        "timed_full_test_repeats_per_checkpoint": args.repeats,
        "seeds": list(range(42, 50)),
        "hardware": hardware_record(device),
    }
    (output_dir / "benchmark_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(summary.to_string(index=False), flush=True)
    print(json.dumps(metadata, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
