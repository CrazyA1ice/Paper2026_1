from __future__ import annotations

from collections.abc import Sequence

import torch
from torch import nn
from torch.nn import functional as F

from .pathformer_adapter import PathformerAdapter


class MovingAverage(nn.Module):
    """Centered moving average with endpoint replication."""

    def __init__(self, kernel_size: int = 25):
        super().__init__()
        if kernel_size % 2 == 0:
            raise ValueError("kernel_size must be odd")
        self.kernel_size = kernel_size

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        pad = (self.kernel_size - 1) // 2
        x_channels_first = x.transpose(1, 2)
        padded = F.pad(x_channels_first, (pad, pad), mode="replicate")
        return F.avg_pool1d(padded, self.kernel_size, stride=1).transpose(1, 2)


class DLinear(nn.Module):
    """Shared-weight DLinear: trend and residual are forecast separately."""

    def __init__(self, input_len: int, pred_len: int, kernel_size: int = 25):
        super().__init__()
        self.moving_average = MovingAverage(kernel_size)
        self.seasonal_linear = nn.Linear(input_len, pred_len)
        self.trend_linear = nn.Linear(input_len, pred_len)

        nn.init.constant_(self.seasonal_linear.weight, 1.0 / input_len)
        nn.init.constant_(self.trend_linear.weight, 1.0 / input_len)
        nn.init.zeros_(self.seasonal_linear.bias)
        nn.init.zeros_(self.trend_linear.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        trend = self.moving_average(x)
        seasonal = x - trend
        seasonal_forecast = self.seasonal_linear(seasonal.transpose(1, 2))
        trend_forecast = self.trend_linear(trend.transpose(1, 2))
        return (seasonal_forecast + trend_forecast).transpose(1, 2)


class FITSStyleFrequencyBlock(nn.Module):
    """Learned low-pass gate inspired by FITS, returning a filtered history."""

    def __init__(self, input_len: int, cut_ratio: float = 0.5):
        super().__init__()
        n_frequencies = input_len // 2 + 1
        self.cut_frequency = max(2, int(n_frequencies * cut_ratio))
        self.logits = nn.Parameter(torch.full((self.cut_frequency,), 3.0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        mean = x.mean(dim=1, keepdim=True)
        std = x.std(dim=1, keepdim=True, unbiased=False).clamp_min(1e-5)
        normalized = (x - mean) / std

        spectrum = torch.fft.rfft(normalized, dim=1)
        filtered = torch.zeros_like(spectrum)
        gate = torch.sigmoid(self.logits).view(1, -1, 1)
        filtered[:, : self.cut_frequency] = spectrum[:, : self.cut_frequency] * gate
        reconstructed = torch.fft.irfft(filtered, n=x.size(1), dim=1)
        return reconstructed * std + mean


class FrequencyDLinear(nn.Module):
    def __init__(self, input_len: int, pred_len: int, cut_ratio: float = 0.5):
        super().__init__()
        self.frequency = FITSStyleFrequencyBlock(input_len, cut_ratio)
        self.backbone = DLinear(input_len, pred_len)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(self.frequency(x))


class FITSForecaster(nn.Module):
    """Compact implementation of the original FITS frequency interpolation idea."""

    def __init__(self, input_len: int, pred_len: int, cut_ratio: float = 0.5):
        super().__init__()
        self.input_len = input_len
        self.pred_len = pred_len
        available = input_len // 2 + 1
        self.cut_frequency = max(2, int(available * cut_ratio))
        ratio = (input_len + pred_len) / input_len
        self.output_frequency = max(2, int(self.cut_frequency * ratio))
        self.frequency_upsampler = nn.Linear(
            self.cut_frequency, self.output_frequency
        ).to(torch.cfloat)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        mean = x.mean(dim=1, keepdim=True)
        variance = x.var(dim=1, keepdim=True, unbiased=False).clamp_min(1e-5)
        normalized = (x - mean) / variance.sqrt()
        low_spectrum = torch.fft.rfft(normalized, dim=1)[:, : self.cut_frequency]
        upsampled = self.frequency_upsampler(low_spectrum.transpose(1, 2)).transpose(1, 2)

        total_len = self.input_len + self.pred_len
        target_spectrum = torch.zeros(
            x.size(0), total_len // 2 + 1, x.size(2),
            dtype=upsampled.dtype, device=x.device,
        )
        target_spectrum[:, : self.output_frequency] = upsampled
        reconstructed = torch.fft.irfft(target_spectrum, n=total_len, dim=1)
        reconstructed = reconstructed * (total_len / self.input_len)
        reconstructed = reconstructed * variance.sqrt() + mean
        return reconstructed[:, -self.pred_len :]


class ScaleRouter(nn.Module):
    """Generate one set of scale weights for each input sample."""

    def __init__(self, n_scales: int, hidden_size: int = 16):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(4, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, n_scales),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        differences = x[:, 1:] - x[:, :-1]
        statistics = torch.stack(
            [
                x.mean(dim=(1, 2)),
                x.std(dim=(1, 2), unbiased=False),
                x[:, -1].mean(dim=1),
                differences.abs().mean(dim=(1, 2)),
            ],
            dim=1,
        )
        return torch.softmax(self.network(statistics), dim=1)


class MultiScaleDLinear(nn.Module):
    """Light multi-scale experts with fixed or sample-adaptive fusion weights."""

    def __init__(
        self,
        input_len: int,
        pred_len: int,
        scales: Sequence[int] = (1, 2, 4),
        use_frequency: bool = False,
        adaptive: bool = True,
        cut_ratio: float = 0.5,
    ):
        super().__init__()
        self.scales = tuple(scales)
        if any(input_len % scale != 0 for scale in self.scales):
            raise ValueError("input_len must be divisible by every scale")
        self.adaptive = adaptive
        self.experts = nn.ModuleList(
            [DLinear(input_len // scale, pred_len) for scale in self.scales]
        )
        self.frequency_blocks = nn.ModuleList(
            [
                FITSStyleFrequencyBlock(input_len // scale, cut_ratio)
                if use_frequency
                else nn.Identity()
                for scale in self.scales
            ]
        )
        self.router = ScaleRouter(len(self.scales)) if adaptive else None

    @staticmethod
    def _downsample(x: torch.Tensor, scale: int) -> torch.Tensor:
        if scale == 1:
            return x
        return F.avg_pool1d(x.transpose(1, 2), kernel_size=scale, stride=scale).transpose(1, 2)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        forecasts = []
        for scale, frequency, expert in zip(
            self.scales, self.frequency_blocks, self.experts
        ):
            scaled = self._downsample(x, scale)
            forecasts.append(expert(frequency(scaled)))
        stacked = torch.stack(forecasts, dim=1)

        if self.router is None:
            weights = torch.full(
                (x.size(0), len(self.scales)),
                1.0 / len(self.scales), device=x.device, dtype=x.dtype,
            )
        else:
            weights = self.router(x)
        output = (stacked * weights[:, :, None, None]).sum(dim=1)
        return output, weights


def build_model(
    name: str,
    input_len: int,
    pred_len: int,
    cut_ratio: float = 0.5,
    n_channels: int | None = None,
    device: torch.device | None = None,
) -> nn.Module:
    if name == "dlinear":
        return DLinear(input_len, pred_len)
    if name == "fits":
        return FITSForecaster(input_len, pred_len, cut_ratio)
    if name == "dlinear_freq":
        return FrequencyDLinear(input_len, pred_len, cut_ratio)
    if name == "dlinear_scale":
        return MultiScaleDLinear(input_len, pred_len, use_frequency=False)
    if name == "dlinear_scale_static":
        return MultiScaleDLinear(
            input_len, pred_len, use_frequency=False, adaptive=False
        )
    if name == "proposed":
        return MultiScaleDLinear(
            input_len, pred_len, use_frequency=True, cut_ratio=cut_ratio
        )
    if name == "proposed_static":
        return MultiScaleDLinear(
            input_len, pred_len, use_frequency=True, adaptive=False,
            cut_ratio=cut_ratio,
        )
    if name == "pathformer":
        if n_channels is None:
            raise ValueError("n_channels is required for Pathformer")
        return PathformerAdapter(
            input_len=input_len,
            pred_len=pred_len,
            n_channels=n_channels,
            device=device,
        )
    raise ValueError(f"Unknown model: {name}")
