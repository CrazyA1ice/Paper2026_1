from __future__ import annotations

from types import SimpleNamespace

import torch
from torch import nn

from external.pathformer.models.PathFormer import Model as OfficialPathformer


OFFICIAL_PATHFORMER_COMMIT = "ea85d82932215e171357da47b3bc82d502344758"
DEFAULT_PATCH_SIZE_LIST = (
    (16, 12, 8, 32),
    (12, 8, 6, 32),
    (8, 6, 16, 12),
)


class PathformerAdapter(nn.Module):
    """Adapter for the official Pathformer implementation.

    Defaults follow the official multivariate traffic configuration where
    applicable, while seq_len, pred_len and num_nodes come from this project's
    unified dataset/training protocol.
    """

    def __init__(
        self,
        input_len: int,
        pred_len: int,
        n_channels: int,
        device: torch.device | None = None,
        d_model: int = 16,
        d_ff: int = 128,
        layer_nums: int = 3,
        k: int = 2,
        residual_connection: int = 1,
        revin: int = 1,
        batch_norm: int = 0,
    ):
        super().__init__()
        if layer_nums != len(DEFAULT_PATCH_SIZE_LIST):
            raise ValueError(
                "The vendored traffic configuration currently expects "
                f"layer_nums={len(DEFAULT_PATCH_SIZE_LIST)}"
            )
        for layer_patches in DEFAULT_PATCH_SIZE_LIST:
            for patch in layer_patches:
                if input_len % patch != 0:
                    raise ValueError(
                        f"Pathformer patch size {patch} must divide input_len={input_len}"
                    )

        gpu = 0
        if device is not None and device.type == "cuda" and device.index is not None:
            gpu = device.index

        config = SimpleNamespace(
            layer_nums=layer_nums,
            num_nodes=n_channels,
            pred_len=pred_len,
            seq_len=input_len,
            k=k,
            num_experts_list=[len(patches) for patches in DEFAULT_PATCH_SIZE_LIST],
            patch_size_list=[list(patches) for patches in DEFAULT_PATCH_SIZE_LIST],
            d_model=d_model,
            d_ff=d_ff,
            residual_connection=residual_connection,
            revin=revin,
            gpu=gpu,
            batch_norm=batch_norm,
        )
        self.model = OfficialPathformer(config)
        self.experiment_config = {
            "source": "decisionintelligence/pathformer",
            "source_commit": OFFICIAL_PATHFORMER_COMMIT,
            "d_model": d_model,
            "d_ff": d_ff,
            "layer_nums": layer_nums,
            "k": k,
            "patch_size_list": [list(p) for p in DEFAULT_PATCH_SIZE_LIST],
            "residual_connection": residual_connection,
            "revin": revin,
            "batch_norm": batch_norm,
        }

    def forward(self, x: torch.Tensor):
        return self.model(x)
