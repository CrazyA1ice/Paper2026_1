"""Three legible restylings of the manuscript's existing method schematic."""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT = Path(__file__).resolve().parent
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial", "DejaVu Sans"],
    "font.size": 7.2,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "axes.unicode_minus": False,
})

STYLES = {
    "A_refined": {
        "ink": "#17313D", "muted": "#526672", "line": "#AEBEC5",
        "outer": "#DCE6E9", "fill": "#FFFFFF", "router_fill": "#F3F8F7",
        "scale": ("#3D7EA6", "#4D9B83", "#C77C4B"),
        "expert": "#DCE9EC", "fusion": "#E8F2F1", "accent": "#267C85",
    },
    "B_labeled_cards": {
        "ink": "#1C3040", "muted": "#526577", "line": "#9EADBA",
        "outer": "#BFCBD2", "fill": "#FBFCFD", "router_fill": "#EDF5F7",
        "scale": ("#377DAB", "#548F8B", "#B47A56"),
        "expert": "#EDF1F5", "fusion": "#DDEFF1", "accent": "#237D8B",
    },
    "C_mono_accent": {
        "ink": "#27313A", "muted": "#5A626B", "line": "#AAB1B7",
        "outer": "#BFC5C9", "fill": "#FFFFFF", "router_fill": "#F3F5F5",
        "scale": ("#697C8A", "#697C8A", "#697C8A"),
        "expert": "#F0F2F3", "fusion": "#E9F0F0", "accent": "#257F84",
    },
}


def box(ax, x, y, w, h, edge, face, radius=1.5, lw=0.9):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.0,rounding_size={radius}",
        linewidth=lw, edgecolor=edge, facecolor=face,
    )
    ax.add_patch(patch)
    return patch


def arrow(ax, start, end, color, dashed=False, lw=1.0):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=7.5,
        linewidth=lw, linestyle="--" if dashed else "-", color=color,
        connectionstyle="arc3,rad=0", shrinkA=1, shrinkB=1,
    ))


def text(ax, x, y, value, style, size=7.2, weight="normal", **kwargs):
    ax.text(x, y, value, ha="center", va="center", fontsize=size,
            fontweight=weight, color=style["ink"], **kwargs)


def schematic(name, style):
    fig, ax = plt.subplots(figsize=(7.09, 3.72))
    fig.patch.set_facecolor("white")
    ax.set(xlim=(0, 100), ylim=(0, 100))
    ax.set_axis_off()
    fig.subplots_adjust(left=0.018, right=0.982, bottom=0.018, top=0.982)

    # The five stage positions and the three parallel scale lanes match Fig. 1.
    stages = [
        (1.0, 29, 17.0, 63, "历史窗口"),
        (20.0, 29, 19.0, 63, "多尺度构造"),
        (41.0, 29, 19.0, 63, "DLinear 专家"),
        (62.0, 29, 19.0, 63, "自适应融合"),
        (83.0, 29, 16.0, 63, "预测输出"),
    ]
    for i, (x, y, w, h, label) in enumerate(stages):
        face = style["fusion"] if i == 3 else style["fill"]
        box(ax, x, y, w, h, style["outer"], face)
        if name == "B_labeled_cards":
            ax.add_patch(plt.Rectangle((x + 0.8, 84.3), w - 1.6, 5.2,
                                       color=style["fusion"] if i == 3 else style["router_fill"],
                                       ec="none"))
        text(ax, x + w / 2, 87.3, label, style, 7.9, "bold")

    rng = np.random.default_rng(7)
    matrix = rng.normal(0, 0.32, (13, 18))
    matrix[5:8, 10:] += np.linspace(0.2, 1.25, 8)
    matrix_out = rng.normal(0, 0.27, (13, 12))
    matrix_out[5:8, 6:] += np.linspace(0.2, 1.2, 6)
    for rect, mat in [([4.2, 54, 10.5, 24], matrix),
                      ([86.2, 54, 9.7, 24], matrix_out)]:
        inset = ax.inset_axes(rect, transform=ax.transData)
        inset.imshow(mat, aspect="auto", cmap="RdBu_r", vmin=-1.6, vmax=1.6,
                     interpolation="nearest")
        inset.set_xticks([])
        inset.set_yticks([])
        for spine in inset.spines.values():
            spine.set_color(style["outer"])
            spine.set_linewidth(0.65)
    text(ax, 9.5, 45.5, r"$X\in\mathbb{R}^{96\times C}$", style, 8.0)
    text(ax, 9.5, 36.8, "96 步 · C 个 OD", style, 6.8)
    text(ax, 91.0, 45.5, r"$\hat{Y}\in\mathbb{R}^{24\times C}$", style, 8.0)
    text(ax, 91.0, 36.8, "未来 24 步", style, 6.8)

    lanes = [
        (70.0, 1, "原始序列", "96 步"),
        (53.0, 2, "2 点均值", "48 步"),
        (36.0, 4, "4 点均值", "24 步"),
    ]
    for j, (y, scale, transform, length) in enumerate(lanes):
        color = style["scale"][j]
        box(ax, 21.6, y, 15.8, 11.5, color, "white", 1.3, 1.1)
        if name == "B_labeled_cards":
            ax.add_patch(plt.Rectangle((21.6, y), 1.1, 11.5, color=color, ec="none"))
        elif name == "C_mono_accent":
            ax.add_patch(plt.Circle((23.2, y + 7.9), 0.45, color=color))
        text(ax, 29.5, y + 8.1, f"尺度 {scale}  ·  {length}", style, 7.3, "bold")
        text(ax, 29.5, y + 3.5, transform, style, 6.9)

        box(ax, 42.7, y, 15.8, 11.5, style["outer"], style["expert"], 1.3)
        text(ax, 50.6, y + 7.6, f"DLinear E{scale}", style, 7.5, "bold")
        text(ax, 50.6, y + 3.3, "趋势 + 余项", style, 6.9)
        arrow(ax, (18.0, y + 5.8), (21.6, y + 5.8), style["line"])
        arrow(ax, (37.4, y + 5.8), (42.7, y + 5.8), style["line"])
        arrow(ax, (58.5, y + 5.8), (64.0, y + 5.8), style["line"])

    box(ax, 64.0, 44.0, 15.0, 33.5, style["accent"], "white", 1.5, 1.0)
    text(ax, 71.5, 69.5, "按样本加权", style, 7.6, "bold")
    text(ax, 71.5, 59.0, r"$\hat{Y}=\sum_s\alpha_s\hat{Y}^{(s)}$", style, 8.1)
    text(ax, 71.5, 50.0, r"$\sum_s\alpha_s=1$", style, 8.1)
    arrow(ax, (79.0, 60.8), (83.0, 60.8), style["ink"], lw=1.2)

    # The original lower router branch retains its three operations and arrows.
    box(ax, 20.0, 3.5, 61.0, 21.0, style["accent"], style["router_fill"], 1.3)
    text(ax, 50.5, 22.0, "样本级尺度路由器", style, 7.9, "bold")
    router = [
        (22.0, 16.0, "窗口统计", "均值 · 标准差\n末时均值\n平均绝对差分"),
        (44.4, 13.0, "两层 MLP", "4 → 16 → 3"),
        (63.6, 15.4, "Softmax", r"$\alpha_1,\alpha_2,\alpha_4$"),
    ]
    for x, w, title, body in router:
        box(ax, x, 4.7 if title == "窗口统计" else 6.1,
            w, 14.1 if title == "窗口统计" else 12.7,
            style["outer"], "white", 1.0)
        text(ax, x + w / 2, 16.1 if title == "窗口统计" else 15.0,
             title, style, 7.1, "bold")
        text(ax, x + w / 2, 9.7 if title == "窗口统计" else 10.2,
             body, style, 6.5 if title == "窗口统计" else
             8.1 if title == "Softmax" else 7.3)
    arrow(ax, (38.0, 12.4), (44.4, 12.4), style["line"])
    arrow(ax, (57.4, 12.4), (63.6, 12.4), style["line"])
    arrow(ax, (9.5, 29.0), (9.5, 12.4), style["accent"], True)
    arrow(ax, (9.5, 12.4), (20.0, 12.4), style["accent"], True)
    arrow(ax, (71.3, 24.5), (71.3, 44.0), style["accent"], True)

    arrow(ax, (84.3, 17.2), (89.4, 17.2), style["line"])
    ax.text(90.2, 17.2, "预测流", ha="left", va="center", fontsize=6.8,
            color=style["muted"])
    arrow(ax, (84.3, 10.0), (89.4, 10.0), style["accent"], True)
    ax.text(90.2, 10.0, "权重流", ha="left", va="center", fontsize=6.8,
            color=style["muted"])

    fig.savefig(OUT / f"{name}.svg", facecolor="white",
                bbox_inches="tight", pad_inches=0.03)
    fig.savefig(OUT / f"{name}.pdf", facecolor="white",
                bbox_inches="tight", pad_inches=0.03)
    fig.savefig(OUT / f"{name}.png", dpi=600, facecolor="white",
                bbox_inches="tight", pad_inches=0.03)
    fig.savefig(OUT / f"{name}.tiff", dpi=600, facecolor="white",
                bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


if __name__ == "__main__":
    for option, palette in STYLES.items():
        schematic(option, palette)
