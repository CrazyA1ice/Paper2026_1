from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.path import Path as MplPath
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch
from matplotlib.transforms import ScaledTranslation


# Publication defaults: editable vector text and grayscale-safe styling.
mpl.rcParams["font.family"] = "sans-serif"
mpl.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Arial",
    "DejaVu Sans",
]
mpl.rcParams.update({"svg.fonttype": "none", "pdf.fonttype": 42})
mpl.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 7
plt.rcParams["axes.labelsize"] = 7
plt.rcParams["axes.titlesize"] = 8
plt.rcParams["xtick.labelsize"] = 6.5
plt.rcParams["ytick.labelsize"] = 6.5
plt.rcParams["legend.fontsize"] = 6.5
plt.rcParams["axes.spines.right"] = False
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["legend.frameon"] = False


ROOT = Path(__file__).resolve().parents[1]
FIGURE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = FIGURE_DIR / "exports"
SOURCE_DIR = FIGURE_DIR / "source_data"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DIR.mkdir(parents=True, exist_ok=True)

BLACK = "#111111"
DARK = "#444444"
MID = "#888888"
LIGHT = "#c8c8c8"
PALE = "#f2f2f2"


def load_alignment_helper():
    scripts_dir = os.environ.get("NATURE_FIGURE_SKILL_SCRIPTS")
    if not scripts_dir:
        raise RuntimeError(
            "Set NATURE_FIGURE_SKILL_SCRIPTS to the nature-figure scripts directory."
        )
    sys.path.insert(0, scripts_dir)
    from audit_panel_alignment import require_matplotlib_panel_alignment

    return require_matplotlib_panel_alignment


require_matplotlib_panel_alignment = load_alignment_helper()


def add_panel_label(ax, label: str) -> None:
    offset = ScaledTranslation(-9 / 72, 4 / 72, ax.figure.dpi_scale_trans)
    ax.text(
        0,
        1,
        label,
        transform=ax.transAxes + offset,
        fontsize=8,
        fontweight="bold",
        ha="left",
        va="bottom",
        color=BLACK,
    )


def export_figure(fig, stem: str, require_labels: bool) -> None:
    base = EXPORT_DIR / stem
    fig.canvas.draw()
    require_matplotlib_panel_alignment(
        fig,
        json_out=str(base) + ".alignment.json",
        overlay_svg=str(base) + ".alignment.svg",
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        require_panel_labels=require_labels,
        strict=True,
    )
    fig.savefig(str(base) + ".svg", bbox_inches="tight")
    fig.savefig(str(base) + ".pdf", bbox_inches="tight")
    fig.savefig(str(base) + ".png", dpi=600, bbox_inches="tight")
    fig.savefig(
        str(base) + ".tiff",
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)


def box(ax, x, y, w, h, text, *, face=PALE, dashed=False, fontsize=6.5):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.0015,rounding_size=0.010",
        linewidth=0.9,
        edgecolor=BLACK,
        facecolor=face,
        linestyle="--" if dashed else "-",
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize)
    return patch


def arrow(ax, start, end, *, dashed=False):
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={
            "arrowstyle": "-|>",
            "lw": 0.8,
            "color": DARK,
            "linestyle": "--" if dashed else "-",
            "mutation_scale": 7.0,
            "shrinkA": 2.5,
            "shrinkB": 3.5,
        },
    )


def routed_arrow(ax, points, *, dashed=False):
    """Draw one continuous polyline whose final segment carries the arrowhead."""
    style = "--" if dashed else "-"
    if len(points) < 2:
        raise ValueError("A routed arrow needs at least two points")
    path = MplPath(points, [MplPath.MOVETO] + [MplPath.LINETO] * (len(points) - 1))
    route = FancyArrowPatch(
        path=path,
        arrowstyle="-|>",
        mutation_scale=7.0,
        linewidth=0.8,
        linestyle=style,
        color=DARK,
        joinstyle="miter",
        capstyle="butt",
        zorder=2,
    )
    ax.add_patch(route)


def figure_1_method_schematic() -> None:
    fig, ax = plt.subplots(figsize=(7.09, 3.25))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Second-stage manuscript architecture: preprocessing, three temporal
    # resolutions, independent DLinear experts, sample-level routing and
    # adaptive weighted fusion. The former frequency-domain branch is removed.
    outer = FancyBboxPatch(
        (0.012, 0.028), 0.976, 0.944,
        boxstyle="round,pad=0.002,rounding_size=0.012",
        linewidth=0.9, edgecolor=BLACK, facecolor="white",
    )
    ax.add_patch(outer)

    title_bar = FancyBboxPatch(
        (0.03, 0.885), 0.94, 0.058,
        boxstyle="round,pad=0.002,rounding_size=0.010",
        linewidth=0.8, edgecolor=BLACK, facecolor="#dedede",
    )
    ax.add_patch(title_bar)
    ax.text(0.048, 0.914, "自适应多尺度网络流量预测框架",
            ha="left", va="center", fontsize=6.8)
    ax.plot([0.660, 0.690], [0.914, 0.914], color=DARK, lw=0.9)
    ax.text(0.700, 0.914, "特征流", ha="left", va="center", fontsize=5.0)
    ax.plot([0.790, 0.820], [0.914, 0.914], color=DARK, lw=0.9, ls="--")
    ax.text(0.830, 0.914, "权重控制", ha="left", va="center", fontsize=5.0)

    input_group = FancyBboxPatch(
        (0.032, 0.295), 0.145, 0.535,
        boxstyle="round,pad=0.002,rounding_size=0.01",
        linewidth=0.75, edgecolor=LIGHT, facecolor="#f7f7f7",
    )
    expert_group = FancyBboxPatch(
        (0.205, 0.295), 0.515, 0.535,
        boxstyle="round,pad=0.002,rounding_size=0.01",
        linewidth=0.75, edgecolor=LIGHT, facecolor="white",
    )
    fusion_group = FancyBboxPatch(
        (0.745, 0.295), 0.225, 0.535,
        boxstyle="round,pad=0.002,rounding_size=0.01",
        linewidth=0.75, edgecolor=LIGHT, facecolor="#f7f7f7",
    )
    router_group = FancyBboxPatch(
        (0.205, 0.075), 0.515, 0.165,
        boxstyle="round,pad=0.002,rounding_size=0.01",
        linewidth=0.75, edgecolor=LIGHT, facecolor=PALE,
    )
    ax.add_patch(input_group)
    ax.add_patch(expert_group)
    ax.add_patch(fusion_group)
    ax.add_patch(router_group)

    ax.text(0.047, 0.795, "输入与预处理", ha="left", va="center",
            fontsize=5.6, fontweight="bold")
    ax.text(0.220, 0.795, "多尺度专家", ha="left", va="center",
            fontsize=5.6, fontweight="bold")
    ax.text(0.760, 0.795, "自适应融合", ha="left", va="center",
            fontsize=5.6, fontweight="bold")
    ax.text(0.220, 0.210, "样本级路由器", ha="left", va="center",
            fontsize=5.4, fontweight="bold")

    box(ax, 0.052, 0.655, 0.105, 0.090, "OD流量窗口\n96 × C",
        face="white", fontsize=5.5)
    box(ax, 0.052, 0.525, 0.105, 0.080, "对数变换\nlog(1+x)",
        face="white", fontsize=5.2)
    box(ax, 0.052, 0.395, 0.105, 0.080, "训练集统计量\n标准化",
        face="#e2e2e2", fontsize=5.0)
    arrow(ax, (0.1045, 0.655), (0.1045, 0.605))
    arrow(ax, (0.1045, 0.525), (0.1045, 0.475))

    lane_specs = [
        (0.655, "尺度 1", "L=96", "原始分辨率", "DLinear E1", "Y(1)"),
        (0.535, "尺度 2", "L=48", "2点平均池化", "DLinear E2", "Y(2)"),
        (0.415, "尺度 4", "L=24", "4点平均池化", "DLinear E4", "Y(4)"),
    ]
    lane_left, lane_width, lane_height = 0.225, 0.475, 0.090
    for y, scale, length, pooling, expert, pred in lane_specs:
        lane = FancyBboxPatch(
            (lane_left, y), lane_width, lane_height,
            boxstyle="round,pad=0.0015,rounding_size=0.009",
            linewidth=0.75, edgecolor=BLACK,
            facecolor="#f1f1f1" if scale != "尺度 2" else "#e7e7e7",
        )
        ax.add_patch(lane)
        cy = y + lane_height / 2
        ax.text(0.265, cy, f"{scale}\n{length}", ha="center", va="center",
                fontsize=5.0, fontweight="bold")
        ax.text(0.380, cy, pooling, ha="center", va="center", fontsize=5.0)
        ax.text(0.545, cy, f"{expert}\n趋势/余项",
                ha="center", va="center", fontsize=5.0)
        ax.text(0.670, cy, pred, ha="center", va="center",
                fontsize=5.2, fontweight="bold")
        for x in (0.305, 0.455, 0.625):
            ax.plot([x, x], [y + 0.012, y + lane_height - 0.012],
                    color=LIGHT, lw=0.55)

    lane_centers = [y + lane_height / 2 for y, *_ in lane_specs]
    ax.plot([0.190, 0.190], [lane_centers[-1], lane_centers[0]],
            color=DARK, lw=0.8)
    arrow(ax, (0.157, 0.435), (0.190, 0.435))
    for cy in lane_centers:
        arrow(ax, (0.190, cy), (lane_left, cy))

    fusion_center = (0.815, 0.560)
    sigma = Ellipse(fusion_center, 0.052, 0.114, linewidth=0.9,
                    edgecolor=BLACK, facecolor="#d0d0d0")
    ax.add_patch(sigma)
    ax.text(*fusion_center, "Σ", ha="center", va="center",
            fontsize=7.0, fontweight="bold")
    ax.text(0.815, 0.645, "动态加权求和", ha="center", va="center",
            fontsize=5.0)
    for cy, end_y in zip(lane_centers, (0.590, 0.560, 0.530)):
        routed_arrow(ax, [(0.700, cy), (0.760, cy), (0.790, end_y)])
    box(ax, 0.870, 0.505, 0.082, 0.110, "预测输出\n24 × C",
        face="#c7c7c7", fontsize=5.4)
    arrow(ax, (0.841, 0.560), (0.870, 0.560))

    router_y, router_h = 0.105, 0.070
    box(ax, 0.315, router_y, 0.135, router_h,
        "μ | σ | last | diff", face="white", fontsize=5.0)
    box(ax, 0.485, router_y, 0.090, router_h,
        "MLP 4→16→3", face="#dddddd", fontsize=5.0)
    box(ax, 0.610, router_y, 0.090, router_h,
        "Softmax", face="white", fontsize=5.0)
    arrow(ax, (0.450, 0.140), (0.485, 0.140))
    arrow(ax, (0.575, 0.140), (0.610, 0.140))
    routed_arrow(ax, [(0.1045, 0.395), (0.1045, 0.140),
                      (0.315, 0.140)])

    box(ax, 0.765, 0.345, 0.100, 0.065, "α1 | α2 | α4",
        face="white", dashed=True, fontsize=5.0)
    routed_arrow(ax, [(0.700, 0.140), (0.735, 0.140),
                      (0.735, 0.377), (0.765, 0.377)], dashed=True)
    arrow(ax, (0.815, 0.410), (0.815, 0.503), dashed=True)

    fig.subplots_adjust(left=0.01, right=0.995, bottom=0.02, top=0.99)
    export_figure(fig, "fig1_method_schematic", require_labels=False)


def figure_2_main_ablation() -> None:
    data = pd.read_csv(ROOT / "results" / "ablation_mean_std.csv")
    order = ["dlinear", "fits", "dlinear_freq", "proposed", "dlinear_scale"]
    display = {
        "dlinear": "DLinear",
        "fits": "FITS",
        "dlinear_freq": "DLinear + 频域门控",
        "proposed": "频域门控 + 自适应尺度",
        "dlinear_scale": "自适应多尺度（本文方法）",
    }
    data = data.set_index("model").loc[order].reset_index()
    data.to_csv(SOURCE_DIR / "fig2_main_ablation.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(7.09, 2.65), sharey=True)
    y = np.arange(len(data))[::-1]
    panels = [("mse_mean", "mse_std", "均方误差（MSE）", (0.181, 0.207)),
              ("mae_mean", "mae_std", "平均绝对误差（MAE）", (0.158, 0.207))]
    for idx, (ax, (mean_col, sd_col, title, xlim)) in enumerate(zip(axes, panels)):
        for yi, row in zip(y, data.itertuples(index=False)):
            is_main = row.model == "dlinear_scale"
            marker = "D" if is_main else "o"
            face = BLACK if is_main else "white"
            ax.errorbar(
                getattr(row, mean_col),
                yi,
                xerr=getattr(row, sd_col),
                fmt=marker,
                ms=5 if is_main else 4,
                mfc=face,
                mec=BLACK if is_main else MID,
                ecolor=BLACK if is_main else MID,
                color=BLACK if is_main else MID,
                elinewidth=0.8,
                capsize=2,
                capthick=0.8,
                zorder=3 if is_main else 2,
            )
        baseline = float(data.loc[data.model == "dlinear", mean_col].iloc[0])
        ax.axvline(baseline, color=LIGHT, lw=0.8, ls="--", zorder=0)
        ax.set_title(title)
        ax.set_xlabel("误差值（均值 ± 随机种子标准差）")
        ax.set_xlim(*xlim)
        ax.set_ylim(-0.6, len(data) - 0.4)
        ax.tick_params(axis="y", length=0)
        add_panel_label(ax, chr(ord("a") + idx))
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([display[m] for m in data.model])
    for tick, model in zip(axes[0].get_yticklabels(), data.model):
        if model == "dlinear_scale":
            tick.set_fontweight("bold")
    axes[1].tick_params(labelleft=False)
    fig.subplots_adjust(left=0.34, right=0.98, bottom=0.22, top=0.88, wspace=0.22)
    export_figure(fig, "fig2_main_ablation", require_labels=True)


def figure_3_weight_ablation() -> None:
    weight = pd.read_csv(ROOT / "results" / "recommended_analysis" / "weight_all_runs.csv")
    final = pd.read_csv(ROOT / "results" / "recommended_analysis" / "final_cut075_all_runs.csv")
    configs = [
        ("无频域门控", weight, "dlinear_scale_static", "dlinear_scale"),
        ("频域门控，r = 0.50", weight, "proposed_static", "proposed"),
        ("频域门控，r = 0.75", final, "proposed_static", "proposed_adaptive"),
    ]
    source_rows = []
    fig, axes = plt.subplots(1, 3, figsize=(7.09, 2.55), sharey=True)
    for panel_idx, (ax, (title, frame, fixed_name, adaptive_name)) in enumerate(zip(axes, configs)):
        pivot = frame[frame.model.isin([fixed_name, adaptive_name])].pivot(
            index="seed", columns="model", values="mse"
        )
        fixed = pivot[fixed_name].to_numpy(dtype=float)
        adaptive = pivot[adaptive_name].to_numpy(dtype=float)
        seeds = pivot.index.to_numpy(dtype=int)
        for seed, fval, aval in zip(seeds, fixed, adaptive):
            ax.plot([0, 1], [fval, aval], color=MID, lw=0.8, marker="o", ms=3)
            source_rows.append(
                {"setting": title, "seed": seed, "fixed_mse": fval, "adaptive_mse": aval}
            )
        means = [fixed.mean(), adaptive.mean()]
        sds = [fixed.std(ddof=1), adaptive.std(ddof=1)]
        ax.errorbar(
            [0, 1], means, yerr=sds, fmt="D", ms=4.5, color=BLACK,
            mfc=BLACK, ecolor=BLACK, capsize=2.5, lw=1.1, zorder=4,
        )
        ax.set_xticks([0, 1], ["固定等权", "自适应权重"])
        ax.set_title(title)
        ax.set_xlim(-0.35, 1.35)
        ax.set_ylim(0.180, 0.207)
        add_panel_label(ax, chr(ord("a") + panel_idx))
    axes[0].set_ylabel("均方误差（MSE）")
    pd.DataFrame(source_rows).to_csv(SOURCE_DIR / "fig3_weight_ablation.csv", index=False)
    fig.subplots_adjust(left=0.09, right=0.99, bottom=0.20, top=0.86, wspace=0.18)
    export_figure(fig, "fig3_weight_ablation", require_labels=True)


def figure_4_frequency_sensitivity() -> None:
    data = pd.read_csv(ROOT / "results" / "recommended_analysis" / "frequency_mean_std.csv")
    data.to_csv(SOURCE_DIR / "fig4_frequency_sensitivity.csv", index=False)
    display = {
        "dlinear_freq": "DLinear + 频域门控",
        "proposed": "频域门控 + 自适应多尺度",
    }
    styles = {
        "dlinear_freq": {"color": MID, "ls": "--", "marker": "o", "mfc": "white"},
        "proposed": {"color": BLACK, "ls": "-", "marker": "s", "mfc": BLACK},
    }
    panels = [("mse_mean", "mse_std", "均方误差（MSE）", (0.183, 0.211)),
              ("mae_mean", "mae_std", "平均绝对误差（MAE）", (0.163, 0.204))]
    fig, axes = plt.subplots(1, 2, figsize=(7.09, 2.65))
    for panel_idx, (ax, (mean_col, sd_col, title, ylim)) in enumerate(zip(axes, panels)):
        for model in ["dlinear_freq", "proposed"]:
            sub = data[data.model == model].sort_values("cut_ratio")
            st = styles[model]
            ax.errorbar(
                sub.cut_ratio,
                sub[mean_col],
                yerr=sub[sd_col],
                label=display[model],
                color=st["color"],
                linestyle=st["ls"],
                marker=st["marker"],
                markerfacecolor=st["mfc"],
                markeredgecolor=st["color"],
                markersize=4,
                linewidth=1.1,
                elinewidth=0.8,
                capsize=2,
            )
        ax.set_xticks([0.25, 0.50, 0.75])
        ax.set_xlabel("频率保留比例 r")
        ax.set_ylabel("误差值（均值 ± 随机种子标准差）")
        ax.set_ylim(*ylim)
        ax.set_title(title)
        add_panel_label(ax, chr(ord("a") + panel_idx))
    axes[0].legend(loc="upper right")
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.22, top=0.88, wspace=0.28)
    export_figure(fig, "fig4_frequency_sensitivity", require_labels=True)


def figure_5_representative_forecast() -> None:
    dlinear_file = ROOT / "results" / "dlinear_seed42" / "predictions.npz"
    adaptive_file = ROOT / "results" / "dlinear_scale_seed42" / "predictions.npz"
    dlinear = np.load(dlinear_file)
    adaptive = np.load(adaptive_file)
    truth = adaptive["truth"]
    if not np.allclose(truth, dlinear["truth"]):
        raise ValueError("Prediction files do not share identical test targets")

    window_mae = np.abs(adaptive["prediction"] - truth).mean(axis=(1, 2))
    median_mae = float(np.median(window_mae))
    window_idx = int(np.argmin(np.abs(window_mae - median_mae)))
    channel_sd = truth[window_idx].std(axis=0)
    eligible = np.flatnonzero(channel_sd > 1e-8)
    eligible_sd = channel_sd[eligible]
    channel_idx = int(eligible[np.argmin(np.abs(eligible_sd - np.median(eligible_sd)))])

    horizon = np.arange(1, truth.shape[1] + 1)
    source = pd.DataFrame(
        {
            "forecast_hour": horizon,
            "truth": truth[window_idx, :, channel_idx],
            "dlinear_seed42": dlinear["prediction"][window_idx, :, channel_idx],
            "adaptive_multiscale_seed42": adaptive["prediction"][window_idx, :, channel_idx],
        }
    )
    source.to_csv(SOURCE_DIR / "fig5_representative_forecast.csv", index=False)
    selection = {
        "seed": 42,
        "window_index_zero_based": window_idx,
        "channel_index_zero_based": channel_idx,
        "selection_rule": (
            "选择自适应模型MAE最接近813个测试窗口中位数的窗口；再从该窗口中选择"
            "24小时真实值标准差最接近非恒定通道中位数的通道。"
        ),
        "selected_window_mae": float(window_mae[window_idx]),
    }
    (SOURCE_DIR / "fig5_selection.json").write_text(
        json.dumps(selection, indent=2), encoding="utf-8"
    )

    fig, ax = plt.subplots(figsize=(4.72, 2.55))
    ax.plot(horizon, source.truth, color=BLACK, lw=1.4, label="真实值")
    ax.plot(
        horizon, source.adaptive_multiscale_seed42, color=DARK, lw=1.1,
        marker="s", ms=2.8, markevery=3, label="自适应多尺度",
    )
    ax.plot(
        horizon, source.dlinear_seed42, color=MID, lw=1.0, ls="--",
        marker="o", mfc="white", ms=2.8, markevery=3, label="DLinear",
    )
    ax.set_xlabel("预测时长（h）")
    ax.set_ylabel("标准化流量")
    ax.set_xticks([1, 6, 12, 18, 24])
    ax.legend(loc="best")
    ax.set_title("中位误差代表性测试窗口")
    fig.subplots_adjust(left=0.15, right=0.98, bottom=0.22, top=0.86)
    export_figure(fig, "fig5_representative_forecast", require_labels=False)


def figure_6_router_weight_distribution() -> None:
    scale_labels = ["尺度1\n（L = 96）", "尺度2\n（L = 48）", "尺度4\n（L = 24）"]
    source_rows = []
    fig, axes = plt.subplots(1, 3, figsize=(7.09, 2.65), sharey=True)

    for panel_idx, (ax, seed) in enumerate(zip(axes, [42, 43, 44])):
        file = ROOT / "results" / f"dlinear_scale_seed{seed}" / "router_weights.csv"
        weights = pd.read_csv(file, header=None).to_numpy(dtype=float)
        if weights.shape[1] != 3:
            raise ValueError(f"Unexpected router weight shape: {weights.shape}")
        if not np.allclose(weights.sum(axis=1), 1.0, atol=1e-5):
            raise ValueError(f"Router weights do not sum to one for seed {seed}")

        for sample_idx, row in enumerate(weights):
            for scale, value in zip([1, 2, 4], row):
                source_rows.append(
                    {
                        "seed": seed,
                        "test_window_index": sample_idx,
                        "scale": scale,
                        "router_weight": value,
                    }
                )

        violin = ax.violinplot(
            [weights[:, idx] for idx in range(3)],
            positions=[1, 2, 3],
            widths=0.72,
            showmeans=False,
            showmedians=True,
            showextrema=True,
        )
        for body in violin["bodies"]:
            body.set_facecolor(LIGHT)
            body.set_edgecolor(BLACK)
            body.set_linewidth(0.8)
            body.set_alpha(1.0)
        for key in ["cbars", "cmins", "cmaxes", "cmedians"]:
            violin[key].set_color(BLACK)
            violin[key].set_linewidth(0.9)

        ax.axhline(1 / 3, color=MID, lw=0.8, ls="--", zorder=0)
        ax.set_xticks([1, 2, 3], scale_labels)
        ax.set_xlim(0.5, 3.5)
        ax.set_ylim(0, 0.82)
        ax.set_title(f"随机种子 {seed}")
        add_panel_label(ax, chr(ord("a") + panel_idx))

    axes[0].set_ylabel("样本级路由权重")
    pd.DataFrame(source_rows).to_csv(
        SOURCE_DIR / "fig6_router_weight_distribution.csv", index=False
    )
    fig.subplots_adjust(left=0.09, right=0.99, bottom=0.24, top=0.86, wspace=0.18)
    export_figure(fig, "fig6_router_weight_distribution", require_labels=True)


def main() -> None:
    figure_1_method_schematic()
    figure_2_main_ablation()
    figure_3_weight_ablation()
    figure_4_frequency_sensitivity()
    figure_5_representative_forecast()
    figure_6_router_weight_distribution()
    print(f"Figures exported to: {EXPORT_DIR}")


if __name__ == "__main__":
    main()
