from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from matplotlib.path import Path as MplPath
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch
from matplotlib.transforms import ScaledTranslation


# Publication defaults: editable vector text and grayscale-safe styling.
mpl.rcParams["font.family"] = "serif"
mpl.rcParams["font.serif"] = [
    "Times New Roman",
    "SimSun",
    "Songti SC",
    "Noto Serif CJK SC",
    "Noto Serif CJK JP",
    "Liberation Serif",
    "DejaVu Serif",
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
plt.rcParams["xtick.direction"] = "in"
plt.rcParams["ytick.direction"] = "in"


ROOT = Path(__file__).resolve().parents[1]
FIGURE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = FIGURE_DIR / "exports"
COLOR_EXPORT_DIR = EXPORT_DIR / "color"
GRAYSCALE_EXPORT_DIR = EXPORT_DIR / "grayscale"
SOURCE_DIR = FIGURE_DIR / "source_data"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
COLOR_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
GRAYSCALE_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
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
    """Export publication figures in both color and grayscale.

    The manuscript uses the color version. The grayscale version is kept in
    exports/grayscale for journals that require monochrome printing.
    Figure numbers/titles are never baked into the figure body; they belong
    to the Word caption below the image.
    """
    base = EXPORT_DIR / stem
    color_base = COLOR_EXPORT_DIR / f"{stem}_color"
    gray_base = GRAYSCALE_EXPORT_DIR / f"{stem}_grayscale"

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

    # Legacy paths retained for compatibility with existing manuscript scripts.
    fig.savefig(str(base) + ".svg", bbox_inches="tight")
    fig.savefig(str(base) + ".pdf", bbox_inches="tight")
    fig.savefig(str(base) + ".png", dpi=600, bbox_inches="tight")
    fig.savefig(
        str(base) + ".tiff",
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )

    # Color publication outputs.
    fig.savefig(str(color_base) + ".svg", bbox_inches="tight")
    fig.savefig(str(color_base) + ".pdf", bbox_inches="tight")
    fig.savefig(str(color_base) + ".png", dpi=600, bbox_inches="tight")
    fig.savefig(
        str(color_base) + ".jpg",
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"quality": 95, "subsampling": 0},
    )

    # Grayscale publication outputs derived from the exact color raster.
    color_png = Image.open(str(color_base) + ".png").convert("RGB")
    gray = color_png.convert("L")
    gray.save(str(gray_base) + ".png", dpi=(600, 600))
    gray.save(str(gray_base) + ".jpg", quality=95, subsampling=0, dpi=(600, 600))
    gray.save(str(gray_base) + ".tiff", compression="tiff_lzw", dpi=(600, 600))

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
    """Publication Figure 1: adaptive multiscale network-traffic predictor.

    The visual structure follows the user-selected scientific diagram:
    input matrix -> multiscale construction -> DLinear experts ->
    adaptive weighted fusion -> prediction, with the sample-level router
    beneath the main path. No figure number, title, or explanatory caption
    is embedded in the image body.
    """
    fig, ax = plt.subplots(figsize=(7.09, 4.05))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Deterministic illustrative matrices; these explain tensor flow only.
    rng = np.random.default_rng(7)
    in_mat = rng.normal(0, 0.35, (16, 24))
    in_mat[7:10, 13:] += np.linspace(0.4, 1.8, 11)
    out_mat = rng.normal(0, 0.25, (16, 12))
    out_mat[7:10, 5:] += np.linspace(0.3, 1.5, 7)

    def panel(x, y, w, h, title, edge="#333333", face="#fafafa", dashed=False):
        p = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.002,rounding_size=0.007",
            linewidth=0.8, edgecolor=edge, facecolor=face,
            linestyle="--" if dashed else "-"
        )
        ax.add_patch(p)
        ax.text(x + w/2, y + h - 0.035, title, ha="center", va="center",
                fontsize=6.2, fontweight="bold")
        return p

    # Main five blocks.
    panel(0.012, 0.365, 0.168, 0.555, "输入时序数据")
    panel(0.193, 0.365, 0.205, 0.555, "多尺度序列构造",
          edge="#4a90e2", face="#f5f9ff", dashed=True)
    panel(0.410, 0.365, 0.205, 0.555, "DLinear 尺度专家",
          edge="#e86a6a", face="#fff7f7", dashed=True)
    panel(0.627, 0.365, 0.178, 0.555, "自适应加权融合",
          edge="#9a78d0", face="#faf7ff", dashed=True)
    panel(0.818, 0.365, 0.170, 0.555, "预测结果")

    # Heatmaps with inward ticks and explicit axis labels.
    ax_in = ax.inset_axes([0.045, 0.565, 0.105, 0.245])
    ax_in.imshow(in_mat, aspect="auto", cmap="RdBu_r", interpolation="nearest")
    ax_in.set_xticks([0, 6, 12, 18, 23], ["1", "", "…", "", "96"])
    ax_in.set_yticks([0, 7, 15], ["1", "…", r"$C$"])
    ax_in.set_xlabel(r"时间步 $t$", fontsize=5.7)
    ax_in.set_ylabel(r"OD 流量", fontsize=5.7)\n    ax_in.yaxis.set_label_coords(-0.20, 0.5)
    ax_in.tick_params(direction="in", labelsize=5.2, width=0.6, length=2)
    for s in ax_in.spines.values():
        s.set_linewidth(0.6)

    ax.text(0.096, 0.455, r"$X\in\mathbb{R}^{96\times C}$",
            ha="center", va="center", fontsize=6.2)
    ax.text(0.096, 0.410, "（96个历史时间点，", ha="center", va="center", fontsize=5.5)
    ax.text(0.096, 0.378, r"$C$个OD流量）", ha="center", va="center", fontsize=5.5)

    ax_out = ax.inset_axes([0.850, 0.565, 0.106, 0.245])
    ax_out.imshow(out_mat, aspect="auto", cmap="RdBu_r", interpolation="nearest")
    ax_out.set_xticks([0, 3, 6, 9, 11], ["1", "", "…", "", "24"])
    ax_out.set_yticks([0, 7, 15], ["1", "…", r"$C$"])
    ax_out.set_xlabel(r"预测时间步 $t$", fontsize=5.7)
    ax_out.set_ylabel(r"OD 流量", fontsize=5.7)\n    ax_out.yaxis.set_label_coords(-0.20, 0.5)
    ax_out.tick_params(direction="in", labelsize=5.2, width=0.6, length=2)
    for s in ax_out.spines.values():
        s.set_linewidth(0.6)

    ax.text(0.903, 0.455, r"$\hat{Y}\in\mathbb{R}^{24\times C}$",
            ha="center", va="center", fontsize=6.2)
    ax.text(0.903, 0.410, "（预测未来24个时间点，", ha="center", va="center", fontsize=5.5)
    ax.text(0.903, 0.378, r"$C$个OD流量）", ha="center", va="center", fontsize=5.5)

    # Scale lanes.
    lane_y = [0.735, 0.575, 0.415]
    lane_face = ["#eef6ff", "#f1f8ef", "#fff3ea"]
    lane_edge = ["#3c78c6", "#58a45c", "#e78b4d"]
    lane_titles = [
        ("尺度 1（原始分辨率）", r"$L=96$", r"$X^{(1)}\in\mathbb{R}^{96\times C}$"),
        ("尺度 2（2点平均池化）", r"$L=48$", r"$X^{(2)}\in\mathbb{R}^{48\times C}$"),
        ("尺度 4（4点平均池化）", r"$L=24$", r"$X^{(4)}\in\mathbb{R}^{24\times C}$"),
    ]
    for y, face, edge, texts in zip(lane_y, lane_face, lane_edge, lane_titles):
        p = FancyBboxPatch((0.213, y), 0.166, 0.125,
                           boxstyle="round,pad=0.002,rounding_size=0.008",
                           linewidth=0.75, edgecolor=edge, facecolor=face)
        ax.add_patch(p)
        ax.text(0.296, y+0.091, texts[0], ha="center", va="center", fontsize=5.6)
        ax.text(0.296, y+0.058, texts[1], ha="center", va="center", fontsize=5.8)
        ax.text(0.296, y+0.024, texts[2], ha="center", va="center", fontsize=5.6)

    # Experts.
    expert_titles = [
        ("DLinear E1", r"$\hat{Y}^{(1)}\in\mathbb{R}^{24\times C}$"),
        ("DLinear E2", r"$\hat{Y}^{(2)}\in\mathbb{R}^{24\times C}$"),
        ("DLinear E4", r"$\hat{Y}^{(4)}\in\mathbb{R}^{24\times C}$"),
    ]
    for y, (name, pred) in zip(lane_y, expert_titles):
        p = FancyBboxPatch((0.430, y), 0.166, 0.125,
                           boxstyle="round,pad=0.002,rounding_size=0.008",
                           linewidth=0.75, edgecolor="#d85a5a", facecolor="#fff9f9")
        ax.add_patch(p)
        ax.text(0.513, y+0.091, name, ha="center", va="center",
                fontsize=5.9, fontweight="bold")
        ax.text(0.513, y+0.058, "趋势项 + 余项", ha="center", va="center", fontsize=5.5)
        ax.text(0.513, y+0.024, pred, ha="center", va="center", fontsize=5.6)

    # Main flow arrows.
    for y in [0.797, 0.637, 0.477]:
        arrow(ax, (0.180, y), (0.213, y))
        arrow(ax, (0.379, y), (0.430, y))

    routed_arrow(ax, [(0.596, 0.797), (0.620, 0.797), (0.620, 0.690), (0.645, 0.690)])
    arrow(ax, (0.596, 0.637), (0.645, 0.637))
    routed_arrow(ax, [(0.596, 0.477), (0.620, 0.477), (0.620, 0.540), (0.645, 0.540)])
    arrow(ax, (0.773, 0.610), (0.818, 0.610))

    # Adaptive fusion box.
    fusion = FancyBboxPatch((0.645, 0.485), 0.128, 0.250,
                            boxstyle="round,pad=0.002,rounding_size=0.008",
                            linewidth=0.8, edgecolor="#6750a4", facecolor="#fbf9ff")
    ax.add_patch(fusion)
    ax.text(0.709, 0.695, "动态加权求和", ha="center", va="center",
            fontsize=5.9, fontweight="bold")
    ax.text(0.709, 0.630,
            r"$\hat{Y}=\sum_{s\in\{1,2,4\}}\alpha_s\hat{Y}^{(s)}$",
            ha="center", va="center", fontsize=6.1)
    ax.text(0.709, 0.565, r"$\alpha_1+\alpha_2+\alpha_4=1$",
            ha="center", va="center", fontsize=5.8)
    ax.text(0.709, 0.525, r"$\alpha_s\geq0$",
            ha="center", va="center", fontsize=5.8)

    # Router panel.
    rp = FancyBboxPatch((0.215, 0.075), 0.575, 0.225,
                        boxstyle="round,pad=0.002,rounding_size=0.008",
                        linewidth=0.8, edgecolor="#5ba65b", facecolor="#f7fbf5",
                        linestyle="--")
    ax.add_patch(rp)
    ax.text(0.503, 0.265, "样本级自适应尺度路由器",
            ha="center", va="center", fontsize=6.2, fontweight="bold")

    router_boxes = [
        (0.238, 0.110, 0.180, 0.120, "统计特征提取",
         r"$f=[\mu\mid\sigma\mid\mathrm{last}\mid\mathrm{diff}]$" + "\n" + r"$f\in\mathbb{R}^{4}$"),
        (0.448, 0.110, 0.135, 0.120, "全连接层",
         r"$4\rightarrow16\rightarrow3$" + "\n" + "ReLU"),
        (0.612, 0.110, 0.155, 0.120, "Softmax 归一化",
         r"$\alpha=[\alpha_1,\alpha_2,\alpha_4]$" + "\n" + r"$\alpha\in\mathbb{R}^{3}$"),
    ]
    for x, y, w, h, title, body in router_boxes:
        p = FancyBboxPatch((x, y), w, h,
                           boxstyle="round,pad=0.002,rounding_size=0.007",
                           linewidth=0.7, edgecolor="#333333", facecolor="white")
        ax.add_patch(p)
        ax.text(x+w/2, y+h-0.032, title, ha="center", va="center",
                fontsize=5.6, fontweight="bold")
        ax.text(x+w/2, y+0.050, body, ha="center", va="center", fontsize=5.5)

    arrow(ax, (0.418, 0.170), (0.448, 0.170))
    arrow(ax, (0.583, 0.170), (0.612, 0.170))

    # Dashed weight-control path from input to router and router to fusion.
    routed_arrow(ax, [(0.095, 0.365), (0.095, 0.170), (0.215, 0.170)], dashed=True)
    ax.text(0.120, 0.208, "计算统计特征", ha="left", va="center", fontsize=5.4)
    routed_arrow(ax, [(0.690, 0.230), (0.690, 0.420), (0.709, 0.485)], dashed=True)
    ax.text(0.700, 0.385, r"自适应权重 $\alpha_1,\alpha_2,\alpha_4$",
            ha="left", va="center", fontsize=5.2)

    # Legend inside the figure body, but no figure title/caption.
    arrow(ax, (0.830, 0.185), (0.875, 0.185))
    ax.text(0.886, 0.185, "数据流", ha="left", va="center", fontsize=5.4)
    arrow(ax, (0.830, 0.135), (0.875, 0.135), dashed=True)
    ax.text(0.886, 0.135, "权重控制", ha="left", va="center", fontsize=5.4)

    fig.subplots_adjust(left=0.005, right=0.995, bottom=0.01, top=0.995)
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
