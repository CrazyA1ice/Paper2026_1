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
SOURCE_DIR_V2 = FIGURE_DIR / "source_data_v2"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
COLOR_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
GRAYSCALE_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DIR_V2.mkdir(parents=True, exist_ok=True)

BLACK = "#111111"
DARK = "#444444"
MID = "#888888"
LIGHT = "#c8c8c8"
PALE = "#f2f2f2"
OKABE_BLUE = "#0072B2"
OKABE_GREEN = "#009E73"
OKABE_ORANGE = "#D55E00"
MODEL_PURPLE = "#6A51A3"
FIXED_ORANGE = "#E69F00"
DEGRADE_RED = "#CC6677"
SCALE_COLORS = ["#0072B2", "#009E73", "#D55E00"]


def configure_scipilot_style() -> None:
    scripts_dir = os.environ.get("SCIPILOT_FIGURE_SKILL_SCRIPTS")
    if not scripts_dir:
        raise RuntimeError("Set SCIPILOT_FIGURE_SKILL_SCRIPTS for figure styling.")
    sys.path.insert(0, scripts_dir)
    from setup_style import setup_style

    setup_style(
        journal="general",
        lang="zh",
        use_sciplots=False,
        serif_for_zh=True,
        constrained_layout=False,
    )
    plt.rcParams.update({
        "font.size": 7,
        "axes.labelsize": 7,
        "axes.titlesize": 8,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6.5,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.8,
        "legend.frameon": False,
    })


configure_scipilot_style()


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
        fontfamily="Times New Roman",
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

    qa_scripts = os.environ.get("SCIPILOT_FIGURE_SKILL_SCRIPTS")
    if not qa_scripts:
        raise RuntimeError("Set SCIPILOT_FIGURE_SKILL_SCRIPTS for figure QA.")
    sys.path.insert(0, qa_scripts)
    from visual_qa import audit_layout, print_report, render_preview

    render_preview(fig, str(EXPORT_DIR / f"_qa_{stem}.png"), dpi=180)
    verdict = print_report(audit_layout(fig))
    if verdict == "FAIL":
        raise RuntimeError(f"SciPilot visual QA failed for {stem}")
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

    # Grayscale publication outputs derived from the exact color raster.
    color_png = Image.open(str(color_base) + ".png").convert("RGB")
    gray = color_png.convert("L")
    gray.save(str(gray_base) + ".png", dpi=(600, 600))
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
    ax_in.set_ylabel(r"OD 流量", fontsize=5.7)
    ax_in.yaxis.set_label_coords(-0.20, 0.5)
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
    ax_out.set_ylabel(r"OD 流量", fontsize=5.7)
    ax_out.yaxis.set_label_coords(-0.20, 0.5)
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


def figure_2_core_weight_pairing() -> None:
    """Eight-seed horizontal dumbbell plot for paired MSE comparisons."""
    data = pd.read_csv(SOURCE_DIR_V2 / "fig2_weight_pairing_8seeds.csv")
    fig, axes = plt.subplots(1, 2, figsize=(6.70, 3.28))
    dataset_specs = [
        ("abilene", "Abilene", 1.67),
        ("geant", "GÉANT", 4.68),
    ]

    for idx, (ax, (dataset, title, improvement)) in enumerate(zip(axes, dataset_specs)):
        sub = data[data.dataset == dataset].sort_values("seed")
        y = np.arange(len(sub))
        for yi, row in zip(y, sub.itertuples(index=False)):
            better = row.adaptive_mse < row.fixed_mse
            connector = OKABE_GREEN if better else DEGRADE_RED
            ax.plot([row.fixed_mse, row.adaptive_mse], [yi, yi],
                    color=connector, alpha=0.82, lw=1.8, zorder=1)
        ax.scatter(sub.fixed_mse, y, s=29, marker="s", facecolor=FIXED_ORANGE,
                   edgecolor="white", linewidth=0.55, label="固定等权", zorder=3)
        ax.scatter(sub.adaptive_mse, y, s=31, marker="o", facecolor=OKABE_BLUE,
                   edgecolor="white", linewidth=0.55, label="自适应权重", zorder=4)

        mean_fixed = float(sub.fixed_mse.mean())
        mean_adaptive = float(sub.adaptive_mse.mean())
        ax.axvline(mean_fixed, color=FIXED_ORANGE, lw=0.9, ls="--", alpha=0.9)
        ax.axvline(mean_adaptive, color=OKABE_BLUE, lw=0.9, ls=":", alpha=0.9)
        ax.set_yticks(y, [str(v) for v in sub.seed])
        ax.invert_yaxis()
        ax.set_xlabel("均方误差（MSE，越低越好）")
        ax.set_ylabel("随机种子")
        ax.set_title(title, pad=10, fontweight="bold", fontfamily="Times New Roman")
        ax.text(0.98, 0.04, f"8种子平均降低 {improvement:.2f}%", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=6.8, color=OKABE_BLUE,
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 1.2})
        ax.tick_params(direction="in", length=3.0, width=0.7)
        ax.grid(axis="x", color="#d9d9d9", linestyle="--", linewidth=0.55, alpha=0.7)
        ax.set_axisbelow(True)
        add_panel_label(ax, chr(ord("a") + idx))

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2,
               bbox_to_anchor=(0.5, 0.995), columnspacing=2.2)
    fig.subplots_adjust(left=0.10, right=0.985, bottom=0.18, top=0.82, wspace=0.30)
    export_figure(fig, "fig2_core_weight_pairing_v2", require_labels=True)



def figure_2_core_weight_estimation() -> None:
    """Paired estimation plot using all eight seeds and real experiment results."""
    data = pd.read_csv(SOURCE_DIR_V2 / "fig2_weight_pairing_8seeds.csv")
    fig, axes = plt.subplots(
        2, 2, figsize=(6.70, 4.58),
        gridspec_kw={"height_ratios": [1.72, 1.00]}
    )

    # Muted publication palette selected by the author.
    palette = {
        "abilene": {"edge": "#1F5FAF", "point": "#4F91D8", "fill": "#8FB8E8"},
        "geant": {"edge": "#B94713", "point": "#EA7A2C", "fill": "#F2B07F"},
    }
    specs = [
        ("abilene", "Abilene", (0.181, 0.198), (-0.010, 0.010)),
        ("geant", "GÉANT", (0.388, 0.495), (-0.040, 0.060)),
    ]

    def kde_density(values: np.ndarray, grid: np.ndarray) -> np.ndarray:
        values = np.asarray(values, dtype=float)
        sd = float(np.std(values, ddof=1))
        bw = 1.06 * sd * (len(values) ** (-1 / 5)) if sd > 0 else 0.01
        span = max(float(np.ptp(values)), 1e-6)
        bw = max(bw, span / 8, 1e-5)
        z = (grid[:, None] - values[None, :]) / bw
        dens = np.exp(-0.5 * z * z).mean(axis=1) / (bw * np.sqrt(2 * np.pi))
        return dens

    for col, (dataset, title, top_ylim, bottom_ylim) in enumerate(specs):
        sub = data[data.dataset == dataset].sort_values("seed").reset_index(drop=True)
        fixed = sub.fixed_mse.to_numpy(dtype=float)
        adaptive = sub.adaptive_mse.to_numpy(dtype=float)
        diff = fixed - adaptive
        color = palette[dataset]

        # Top: paired raw MSE values.
        ax = axes[0, col]
        for fval, aval in zip(fixed, adaptive):
            ax.plot([0, 1], [fval, aval], color="#A8ADB3", lw=0.75, alpha=0.92, zorder=1)
        ax.scatter(
            np.zeros_like(fixed), fixed, s=32,
            facecolor=color["fill"], edgecolor=color["edge"], linewidth=0.85, zorder=3
        )
        ax.scatter(
            np.ones_like(adaptive), adaptive, s=32,
            facecolor=color["point"], edgecolor=color["edge"], linewidth=0.85, zorder=3
        )
        means = np.array([fixed.mean(), adaptive.mean()])
        sds = np.array([fixed.std(ddof=1), adaptive.std(ddof=1)])
        ax.errorbar(
            [0, 1], means, yerr=sds, fmt="D", ms=5.2,
            color=BLACK, mfc=BLACK, mec=BLACK, ecolor=BLACK,
            elinewidth=1.0, capsize=3.0, zorder=5
        )
        ax.set_xticks([0, 1], ["固定等权", "自适应权重"])
        ax.set_ylabel("均方误差（MSE）")
        ax.set_title(title, pad=9, fontweight="bold", fontfamily="Times New Roman", fontsize=10)
        ax.set_xlim(-0.24, 1.24)
        ax.set_ylim(*top_ylim)
        ax.tick_params(direction="in", length=3.0, width=0.7)
        add_panel_label(ax, chr(ord("a") + col))

        # Bottom: paired differences + half-density + mean 95% CI.
        axd = axes[1, col]
        y_grid = np.linspace(bottom_ylim[0], bottom_ylim[1], 260)
        dens = kde_density(diff, y_grid)
        width = 0.34 * dens / max(float(dens.max()), 1e-12)
        density_x = 0.46
        axd.fill_betweenx(
            y_grid, density_x, density_x + width,
            color=color["fill"], alpha=0.62, linewidth=0
        )

        # Deterministic horizontal jitter for the eight paired differences.
        jitter = np.linspace(-0.055, 0.055, len(diff))
        axd.scatter(
            0.36 + jitter, diff, s=25,
            facecolor=color["point"], edgecolor=color["edge"], linewidth=0.8, zorder=4
        )

        mean_diff = float(diff.mean())
        sem = float(diff.std(ddof=1) / np.sqrt(len(diff)))
        # t_0.975,7 = 2.364624251; kept explicit to avoid an extra SciPy dependency.
        half_ci = 2.364624251 * sem
        axd.errorbar(
            [0.88], [mean_diff], yerr=[[half_ci], [half_ci]],
            fmt="o", ms=5.1, color=BLACK, mfc=BLACK, mec=BLACK,
            ecolor=BLACK, elinewidth=1.0, capsize=3.0, zorder=5
        )
        axd.axhline(0.0, color="#555555", lw=0.75, ls="--", dashes=(4, 3), zorder=0)
        axd.set_xlim(0.08, 1.08)
        axd.set_ylim(*bottom_ylim)
        axd.set_xticks([])
        axd.set_xlabel("配对差值（固定等权 − 自适应权重）")
        axd.set_ylabel("ΔMSE")
        axd.tick_params(direction="in", length=3.0, width=0.7)

    fig.subplots_adjust(
        left=0.095, right=0.985, bottom=0.105, top=0.94,
        wspace=0.27, hspace=0.20
    )
    export_figure(fig, "fig2_core_weight_estimation", require_labels=True)

def candidate_1_representative_horizon_error() -> None:
    """Visual candidate only: per-step error for the saved representative case."""
    data = pd.read_csv(SOURCE_DIR / "fig5_representative_forecast.csv")
    horizon = data["forecast_hour"].to_numpy()
    dlinear_error = np.abs(data["dlinear_seed42"] - data["truth"]).to_numpy()
    adaptive_error = np.abs(
        data["adaptive_multiscale_seed42"] - data["truth"]
    ).to_numpy()
    source = pd.DataFrame({
        "forecast_hour": horizon,
        "dlinear_absolute_error": dlinear_error,
        "adaptive_absolute_error": adaptive_error,
        "adaptive_better": adaptive_error < dlinear_error,
        "evidence_scope": "representative window, seed 42, channel 29",
    })
    source.to_csv(SOURCE_DIR_V2 / "candidate1_representative_horizon_error.csv", index=False)

    print("Candidate 1 profile:", {
        "n_horizons": int(len(source)),
        "dlinear_mean_abs_error": float(dlinear_error.mean()),
        "adaptive_mean_abs_error": float(adaptive_error.mean()),
        "adaptive_better_steps": int((adaptive_error < dlinear_error).sum()),
    })
    fig, ax = plt.subplots(figsize=(6.70, 2.90))
    ax.plot(horizon, dlinear_error, color=MODEL_PURPLE, lw=1.35, ls="--",
            marker="s", ms=3.2, mfc="white", mec=MODEL_PURPLE,
            label="DLinear")
    ax.plot(horizon, adaptive_error, color=OKABE_BLUE, lw=1.45, ls="-",
            marker="o", ms=3.2, mfc=OKABE_BLUE, mec="white", mew=0.45,
            label="自适应多尺度")
    better = adaptive_error <= dlinear_error
    ax.fill_between(horizon, dlinear_error, adaptive_error, where=better,
                    color=OKABE_GREEN, alpha=0.16, interpolate=True,
                    label="自适应误差较低")
    ax.fill_between(horizon, dlinear_error, adaptive_error, where=~better,
                    color=DEGRADE_RED, alpha=0.14, interpolate=True,
                    label="自适应误差较高")
    ax.set_xlabel("预测步长（h）")
    ax.set_ylabel("绝对误差（标准化尺度）")
    ax.set_xticks([1, 4, 8, 12, 16, 20, 24])
    ax.set_xlim(1, 24)
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", color="#d9d9d9", ls="--", lw=0.55, alpha=0.7)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", ncol=2, columnspacing=1.2, handlelength=2.4)
    fig.subplots_adjust(left=0.11, right=0.985, bottom=0.20, top=0.95)
    export_figure(fig, "candidate1_representative_horizon_error", require_labels=False)


def candidate_2_router_weight_distribution_8seeds() -> None:
    """Window distributions plus independent seed means for both datasets."""
    scale_values = [1, 2, 4]
    scale_labels = ["尺度1", "尺度2", "尺度4"]
    records = []
    for dataset in ["abilene", "geant"]:
        for seed in range(42, 50):
            path = ROOT / "results" / dataset / f"dlinear_scale_seed{seed}" / "router_weights.csv"
            weights = pd.read_csv(path, header=None).to_numpy(dtype=float)
            if weights.shape[1] != 3 or not np.allclose(weights.sum(axis=1), 1.0, atol=1e-5):
                raise ValueError(f"Invalid router weights: {path}")
            for scale_idx, scale in enumerate(scale_values):
                for window_idx, value in enumerate(weights[:, scale_idx]):
                    records.append({
                        "dataset": dataset,
                        "seed": seed,
                        "test_window_index": window_idx,
                        "scale": scale,
                        "router_weight": float(value),
                    })
    data = pd.DataFrame(records)
    data.to_csv(SOURCE_DIR_V2 / "candidate2_router_weight_distribution_8seeds.csv", index=False)
    seed_means = (data.groupby(["dataset", "seed", "scale"], as_index=False)
                      .router_weight.mean())
    print("Candidate 2 profile:", {
        "n_rows": int(len(data)),
        "n_seeds": int(data.seed.nunique()),
        "datasets": data.dataset.unique().tolist(),
        "weight_min": float(data.router_weight.min()),
        "weight_max": float(data.router_weight.max()),
    })

    fig, axes = plt.subplots(1, 2, figsize=(6.70, 3.12), sharey=True)
    rng = np.random.default_rng(20260920)
    for panel_idx, (ax, dataset, title) in enumerate(
        zip(axes, ["abilene", "geant"], ["Abilene", "GÉANT"])
    ):
        groups = [
            data[(data.dataset == dataset) & (data.scale == scale)].router_weight.to_numpy()
            for scale in scale_values
        ]
        violin = ax.violinplot(groups, positions=[1, 2, 3], widths=0.72,
                               showmeans=False, showmedians=True, showextrema=True)
        for body, color in zip(violin["bodies"], SCALE_COLORS):
            body.set_facecolor(color)
            body.set_edgecolor(color)
            body.set_alpha(0.30)
            body.set_linewidth(0.9)
        for key in ["cbars", "cmins", "cmaxes", "cmedians"]:
            violin[key].set_color(BLACK)
            violin[key].set_linewidth(0.8)
        for pos, scale, color in zip([1, 2, 3], scale_values, SCALE_COLORS):
            vals = seed_means[(seed_means.dataset == dataset) &
                              (seed_means.scale == scale)].router_weight.to_numpy()
            jitter = rng.uniform(-0.075, 0.075, len(vals))
            ax.scatter(pos + jitter, vals, s=22, color=color, edgecolor="white",
                       linewidth=0.5, alpha=0.95, zorder=4)
        ax.axhline(1 / 3, color=MID, lw=0.85, ls="--", zorder=0)
        ax.set_xticks([1, 2, 3], scale_labels)
        ax.set_xlabel("时间尺度")
        ax.set_title(title, pad=9, fontweight="bold", fontfamily="Times New Roman")
        ax.set_xlim(0.55, 3.45)
        ax.set_ylim(0, 0.82)
        ax.grid(axis="y", color="#dddddd", ls="--", lw=0.5, alpha=0.65)
        ax.set_axisbelow(True)
        add_panel_label(ax, chr(ord("a") + panel_idx))
    axes[0].set_ylabel("样本级路由权重")
    axes[1].text(0.98, 0.04, "小提琴：测试窗口分布\n圆点：8个随机种子的均值",
                 transform=axes[1].transAxes, ha="right", va="bottom", fontsize=6.3,
                 bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 1.4})
    fig.subplots_adjust(left=0.09, right=0.99, bottom=0.18, top=0.88, wspace=0.14)
    export_figure(fig, "candidate2_router_weight_distribution_8seeds", require_labels=True)


def figure_3_router_weight_dynamics() -> None:
    """Representative router dynamics for the objectively fixed seed 42."""
    fig, axes = plt.subplots(1, 2, figsize=(6.70, 3.05), sharey=True)
    dataset_specs = [
        ("abilene", "Abilene"),
        ("geant", "GÉANT"),
    ]
    colors = [OKABE_BLUE, OKABE_GREEN, OKABE_ORANGE]
    linestyles = ["-", "--", "-."]
    labels = [r"$\alpha_1$", r"$\alpha_2$", r"$\alpha_4$"]
    source_rows = []

    for idx, (ax, (dataset, title)) in enumerate(zip(axes, dataset_specs)):
        path = ROOT / "results" / dataset / "dlinear_scale_seed42" / "router_weights.csv"
        weights = pd.read_csv(path, header=None).to_numpy(dtype=float)
        if weights.shape[1] != 3:
            raise ValueError(f"Unexpected router weight shape for {dataset}: {weights.shape}")
        if not np.allclose(weights.sum(axis=1), 1.0, atol=1e-5):
            raise ValueError(f"Router weights do not sum to one for {dataset}")

        count = min(150, len(weights))
        x = np.arange(1, count + 1)
        for col in range(3):
            ax.plot(
                x,
                weights[:count, col],
                color=colors[col],
                linestyle=linestyles[col],
                lw=1.25,
                label=labels[col],
            )
        ax.axhline(1 / 3, color=MID, lw=0.8, ls=":", zorder=0)
        ax.set_xlim(1, count)
        ax.set_ylim(0, 0.72)
        ax.set_xticks([1, 30, 60, 90, 120, 150])
        ax.set_xlabel("测试窗口索引（前150个）")
        ax.set_title(title, pad=10, fontweight="bold", fontfamily="Times New Roman")
        ax.tick_params(direction="out", length=3.0, width=0.7)
        ax.grid(axis="y", color="#dedede", linestyle="--", linewidth=0.5, alpha=0.65)
        ax.set_axisbelow(True)
        add_panel_label(ax, chr(ord("a") + idx))

        for row_idx in range(count):
            source_rows.append({
                "dataset": dataset,
                "seed": 42,
                "test_window_index": row_idx,
                "alpha_1": float(weights[row_idx, 0]),
                "alpha_2": float(weights[row_idx, 1]),
                "alpha_4": float(weights[row_idx, 2]),
            })

    axes[0].set_ylabel("样本级路由权重")
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", ncol=3,
               bbox_to_anchor=(0.5, 0.985), frameon=False, columnspacing=1.8)
    pd.DataFrame(source_rows).to_csv(
        SOURCE_DIR_V2 / "fig3_router_seed42_first150.csv", index=False
    )
    fig.subplots_adjust(left=0.09, right=0.99, bottom=0.19, top=0.80, wspace=0.15)
    export_figure(fig, "fig3_router_weight_dynamics", require_labels=True)


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
    figure_2_core_weight_pairing()
    figure_3_router_weight_dynamics()
    candidate_1_representative_horizon_error()
    candidate_2_router_weight_distribution_8seeds()
    print(f"Figures exported to: {EXPORT_DIR}")


if __name__ == "__main__":
    main()
