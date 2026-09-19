from __future__ import annotations

from types import SimpleNamespace

import torch
from torch import nn

from external.lightts.models.LightTS import Model as OfficialLightTS


OFFICIAL_LIGHTTS_COMMIT = "4e938a1767106324dd753b2a44832bf870a0252e"
OFFICIAL_LIGHTTS_MODEL_SHA = "a2051e44d864ec4ec5e72e59660b98c30c93a902"


class LightTSAdapter(nn.Module):
    """Adapter for THUML's LightTS implementation.

    The model logic is kept in the vendored upstream file. This adapter only
    supplies the configuration expected by Time-Series-Library and exposes a
    single-tensor forecasting interface used by this project.
    """

    def __init__(
        self,
        input_len: int,
        pred_len: int,
        n_channels: int,
        d_model: int = 512,
        dropout: float = 0.1,
        chunk_size: int = 24,
    ):
        super().__init__()
        if input_len <= 0 or pred_len <= 0 or n_channels <= 0:
            raise ValueError("input_len, pred_len and n_channels must be positive")
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        config = SimpleNamespace(
            task_name="long_term_forecast",
            seq_len=input_len,
            pred_len=pred_len,
            d_model=d_model,
            enc_in=n_channels,
            dropout=dropout,
        )
        self.model = OfficialLightTS(config, chunk_size=chunk_size)
        self.experiment_config = {
            "source": "thuml/Time-Series-Library",
            "source_commit": OFFICIAL_LIGHTTS_COMMIT,
            "source_model_sha": OFFICIAL_LIGHTTS_MODEL_SHA,
            "d_model": d_model,
            "dropout": dropout,
            "chunk_size": chunk_size,
        }

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x, None, None, None)
