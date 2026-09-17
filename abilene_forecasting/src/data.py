from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset


class SlidingWindowDataset(Dataset):
    """Convert a T x C time series into (history, future) sample pairs."""

    def __init__(self, values: np.ndarray, input_len: int, pred_len: int):
        values = np.asarray(values, dtype=np.float32)
        if values.ndim != 2:
            raise ValueError(f"Expected values with shape [time, channel], got {values.shape}")
        self.values = torch.from_numpy(np.ascontiguousarray(values))
        self.input_len = input_len
        self.pred_len = pred_len
        self.n_windows = len(values) - input_len - pred_len + 1
        if self.n_windows <= 0:
            raise ValueError(
                f"Split has {len(values)} rows, fewer than input_len + pred_len "
                f"({input_len + pred_len})."
            )

    def __len__(self) -> int:
        return self.n_windows

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        middle = index + self.input_len
        end = middle + self.pred_len
        return self.values[index:middle], self.values[middle:end]


def load_npz(path: str | Path) -> dict[str, np.ndarray]:
    with np.load(path) as data:
        return {key: data[key] for key in data.files}


def inverse_traffic_transform(
    normalized: np.ndarray, mean: np.ndarray, std: np.ndarray
) -> np.ndarray:
    """Undo channel-wise z-score and log1p transforms."""
    log_values = normalized * std.reshape(1, 1, -1) + mean.reshape(1, 1, -1)
    return np.maximum(np.expm1(log_values), 0.0)

