from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from cesnet_tszoo.configs import TimeBasedConfig
from cesnet_tszoo.datasets import Abilene
from cesnet_tszoo.utils.enums import DatasetType


def extract_matrix(raw: np.ndarray) -> np.ndarray:
    """Convert TS-Zoo output into a regular [time, OD-channel] array."""
    if raw.dtype.names:
        if "matrix_avg_realOD" not in raw.dtype.names:
            raise ValueError(f"matrix_avg_realOD missing from fields: {raw.dtype.names}")
        raw = raw["matrix_avg_realOD"]
    raw = np.asarray(raw)
    if raw.ndim >= 4 and raw.shape[0] == 1:
        raw = raw[0]
    if raw.ndim < 2:
        raise ValueError(f"Unexpected Abilene array shape: {raw.shape}")
    return raw.reshape(raw.shape[0], -1).astype(np.float64)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="data/raw")
    parser.add_argument("--output", default="data/processed/abilene_1hour.npz")
    parser.add_argument("--aggregation", default="1_hour")
    parser.add_argument("--train-ratio", type=float, default=0.6)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    args = parser.parse_args()

    dataset = Abilene.get_dataset(
        data_root=args.data_root,
        subset="matrix",
        aggregation=args.aggregation,
        dataset_type=DatasetType.TIME_BASED,
    )
    config = TimeBasedConfig(
        ts_ids=1.0,
        train_time_period=1.0,
        features_to_take=["matrix_avg_realOD"],
        default_values=0,
        include_time=False,
        include_ts_id=False,
        train_workers=0,
        val_workers=0,
        test_workers=0,
        all_workers=0,
        init_workers=0,
        random_state=42,
    )
    dataset.set_dataset_config_and_initialize(config, workers=0)
    values = extract_matrix(dataset.get_train_numpy(workers=0))
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    values = np.maximum(values, 0.0)

    n_times = len(values)
    train_end = int(n_times * args.train_ratio)
    val_end = int(n_times * (args.train_ratio + args.val_ratio))
    if not (0 < train_end < val_end < n_times):
        raise ValueError("Ratios must create non-empty chronological splits")

    # log1p reduces the extreme right skew typical of byte/traffic volumes.
    logged = np.log1p(values)
    train_logged = logged[:train_end]
    channel_std = train_logged.std(axis=0)
    active_mask = channel_std > 1e-8
    if not active_mask.any():
        raise ValueError("No non-constant OD channels found")
    logged = logged[:, active_mask]

    mean = logged[:train_end].mean(axis=0)
    std = logged[:train_end].std(axis=0)
    std[std < 1e-8] = 1.0
    normalized = (logged - mean) / std

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output,
        train=normalized[:train_end].astype(np.float32),
        val=normalized[train_end:val_end].astype(np.float32),
        test=normalized[val_end:].astype(np.float32),
        mean=mean.astype(np.float32),
        std=std.astype(np.float32),
        active_indices=np.flatnonzero(active_mask).astype(np.int64),
        original_shape=np.asarray(values.shape, dtype=np.int64),
    )
    print(f"Saved: {output}")
    print(f"Original shape: {values.shape}; active OD channels: {active_mask.sum()}")
    print(
        f"Chronological split rows: train={train_end}, "
        f"val={val_end - train_end}, test={n_times - val_end}"
    )


if __name__ == "__main__":
    main()
