import torch

from src.models import build_model


def test_all_model_output_shapes():
    x = torch.randn(2, 96, 12)
    for name in (
        "dlinear", "fits", "dlinear_freq", "dlinear_scale",
        "dlinear_scale_static", "proposed", "proposed_static",
    ):
        output = build_model(name, 96, 24)(x)
        prediction = output[0] if isinstance(output, tuple) else output
        assert prediction.shape == (2, 24, 12)


def test_router_weights_sum_to_one():
    x = torch.randn(3, 96, 12)
    _, weights = build_model("proposed", 96, 24)(x)
    assert torch.allclose(weights.sum(dim=1), torch.ones(3), atol=1e-6)


def test_static_scale_weights_are_uniform():
    x = torch.randn(3, 96, 12)
    _, weights = build_model("dlinear_scale_static", 96, 24)(x)
    assert torch.allclose(weights, torch.full((3, 3), 1 / 3), atol=1e-6)


def test_proposed_uses_requested_cut_ratio():
    model = build_model("proposed", 96, 24, cut_ratio=0.25)
    assert model.frequency_blocks[0].cut_frequency == 12
