from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from cesnet_tszoo.configs import TimeBasedConfig
from cesnet_tszoo.datasets import Abilene, GEANT
from cesnet_tszoo.utils.enums import DatasetType


DATASET_SPECS = {
    "abilene": {
        "factory": Abilene,
        "feature": "matrix_avg_realOD",
        "default_output": "data/processed/abilene_1hour.npz",
    },
    "geant": {
        "factory": GEANT,
        "feature": "avg_matrix_bandwidth_kbs",
        "default_output": "data/processed/geant_1hour.npz",
    },
}


def extract_matrix(raw: np.ndarray, feature_name: str) -> np.ndarray:
    """Convert TS-Zoo matrix output into a regular [time, OD-channel] array."""
    if raw.dtype.names:
        if feature_name not in raw.dtype.names:
            raise ValueError(
                f"{feature_name} missing from fields: {raw.dtype.names}"
            )
        raw = raw[feature_name]
    raw = np.asarray(raw)
    if raw.ndim >= 4 and raw.shape[0] == 1:
        raw = raw[0]
    if raw.ndim < 2:
        raise ValueError(f"Unexpected matrix array shape: {raw.shape}")
    return raw.reshape(raw.shape[0], -1).astype(np.float64)


def prepare_dataset(
    dataset_name: str,
    data_root: str,
    output: str | None,
    aggregation: str,
    train_ratio: float,
    val_ratio: float,
) -> Path:
    dataset_name = dataset_name.lower()
    if dataset_name not in DATASET_SPECS:
        raise ValueError(f"Unsupported dataset: {dataset_name}")

    spec = DATASET_SPECS[dataset_name]
    dataset = spec["factory"].get_dataset(
        data_root=data_root,
        subset="matrix",
        aggregation=aggregation,
        dataset_type=DatasetType.TIME_BASED,
    )
    config = TimeBasedConfig(
        ts_ids=1.0,
        train_time_period=1.0,
        features_to_take=[spec["feature"]],
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
    values = extract_matrix(
        dataset.get_train_numpy(workers=0),
        spec["feature"],
    )
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    values = np.maximum(values, 0.0)

    n_times = len(values)
    train_end = int(n_times * train_ratio)
    val_end = int(n_times * (train_ratio + val_ratio))
    if not (0 < train_end < val_end < n_times):
        raise ValueError("Ratios must create non-empty chronological splits")

    # Keep the same preprocessing protocol on every dataset:
    # log1p -> chronological split -> train-only channel standardization.
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

    output_path = Path(output or spec["default_output"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        train=normalized[:train_end].astype(np.float32),
        val=normalized[train_end:val_end].astype(np.float32),
        test=normalized[val_end:].astype(np.float32),
        mean=mean.astype(np.float32),
        std=std.astype(np.float32),
        active_indices=np.flatnonzero(active_mask).astype(np.int64),
        original_shape=np.asarray(values.shape, dtype=np.int64),
        dataset=np.asarray(dataset_name),
        feature=np.asarray(spec["feature"]),
        aggregation=np.asarray(aggregation),
        train_ratio=np.asarray(train_ratio, dtype=np.float32),
        val_ratio=np.asarray(val_ratio, dtype=np.float32),
    )

    print(f"Saved: {output_path}")
    print(
        f"Dataset: {dataset_name}; feature: {spec['feature']}; "
        f"aggregation: {aggregation}"
    )
    print(
        f"Original shape: {values.shape}; active OD channels: "
        f"{active_mask.sum()}"
    )
    print(
        f"Chronological split rows: train={train_end}, "
        f"val={val_end - train_end}, test={n_times - val_end}"
    )
    return output_path


def build_parser(default_dataset: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        choices=sorted(DATASET_SPECS),
        default=default_dataset or "abilene",
    )
    parser.add_argument("--data-root", default="data/raw")
    parser.add_argument("--output", default=None)
    parser.add_argument("--aggregation", default="1_hour")
    parser.add_argument("--train-ratio", type=float, default=0.6)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    return parser


def main(default_dataset: str | None = None) -> None:
    args = build_parser(default_dataset).parse_args()
    prepare_dataset(
        dataset_name=args.dataset,
        data_root=args.data_root,
        output=args.output,
        aggregation=args.aggregation,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
    )


if __name__ == "__main__":
    main()
