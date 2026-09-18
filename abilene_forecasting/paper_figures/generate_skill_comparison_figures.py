from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper_figures" / "source_data"
RESULTS = ROOT / "results"
OUT_NATURE = ROOT / "paper_figures" / "nature_figure_set"
OUT_SCIPILOT = ROOT / "paper_figures" / "scipilot_figure_set"
for directory in (OUT_NATURE, OUT_SCIPILOT):
    directory.mkdir(parents=True, exist_ok=True)

mpl.rcParams.update(
    {
        "font.family": ["Times New Roman", "SimSun", "Liberation Serif", "Noto Serif CJK SC"],
        "axes.unicode_minus": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 9,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.5,
        "axes.linewidth": 0.7,
        "lines.linewidth": 1.1,
        "savefig.facecolor": "white",
    }
)

BLACK = "#111111"
DARK = "#4a4a4a"
MID = "#858585"
LIGHT = "#c9c9c9"
PALE = "#f2f2f2"
MARKERS = ["o", "s", "^", "D", "P"]
MODEL_LABELS = {
    "dlinear": "DLinear",
    "fits": "FITS",
    "dlinear_freq": "DLinear+频域",
    "dlinear_scale": "本文方法",
    "proposed": "频域门控+多尺度",
}
SHORT_MODEL_LABELS = {
    "dlinear": "DLinear",
    "fits": "FITS",
    "dlinear_freq": "DLinear+频",
    "dlinear_scale": "本文方法",
    "proposed": "频域门控+多尺度",
}
MODEL_ORDER = ["dlinear", "fits", "dlinear_freq", "dlinear_scale", "proposed"]

NATURE_SCRIPTS = os.environ.get("NATURE_FIGURE_SKILL_SCRIPTS")
if NATURE_SCRIPTS:
    sys.path.insert(0, NATURE_SCRIPTS)
    from audit_panel_alignment import require_matplotlib_panel_alignment
else:
    require_matplotlib_panel_alignment = None


def style_axis(ax: plt.Axes, grid: bool = True) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    if grid:
        ax.grid(axis="y", color="#dddddd", linewidth=0.45, linestyle="--", zorder=0)
    ax.tick_params(width=0.7, length=3, direction="in")


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.13, 1.04, label, transform=ax.transAxes, weight="bold", va="bottom")


def save_bundle(fig: plt.Figure, out_dir: Path, stem: str) -> None:
    for text_artist in fig.findobj(match=mpl.text.Text):
        text_artist.set_fontfamily(["Times New Roman", "SimSun", "Liberation Serif", "Noto Serif CJK SC"])
    fig.canvas.draw()
    if require_matplotlib_panel_alignment is not None and len(fig.axes) > 1:
        require_matplotlib_panel_alignment(
            fig,
            json_out=out_dir / f"{stem}.alignment.json",
            overlay_svg=out_dir / f"{stem}.alignment.svg",
            tolerance_pt=1.5,
            gutter_tolerance_pt=1.5,
            require_panel_labels=False,
            strict=True,
        )
    fig.savefig(out_dir / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(out_dir / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(out_dir / f"{stem}.png", dpi=600, bbox_inches="tight")
    fig.savefig(
        out_dir / f"{stem}.tiff",
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)


def load_data() -> dict[str, pd.DataFrame]:
    return {
        "formal": pd.read_csv(RESULTS / "ablation_summary.csv"),
        "weight": pd.read_csv(SOURCE / "fig3_weight_ablation.csv"),
        "frequency": pd.read_csv(RESULTS / "recommended_analysis" / "frequency_all_runs.csv"),
        "forecast": pd.read_csv(SOURCE / "fig5_representative_forecast.csv"),
        "router": pd.read_csv(SOURCE / "fig6_router_weight_distribution.csv"),
    }


def draw_method_flow(out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.1, 3.45), constrained_layout=True)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    def box(x, y, w, h, text, fill="white", lw=0.85, fs=7.5):
        p = FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.012",
            edgecolor=BLACK, facecolor=fill, linewidth=lw, zorder=2,
        )
        ax.add_patch(p)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, zorder=3)
        return p

    def arrow(x1, y1, x2, y2, dashed=False):
        ax.add_patch(
            FancyArrowPatch(
                (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=9,
                linewidth=0.85, color=DARK, linestyle="--" if dashed else "-",
                shrinkA=3, shrinkB=4, connectionstyle="arc3,rad=0", zorder=4,
            )
        )

    def routed_arrow(points, dashed=False):
        xs, ys = zip(*points)
        ax.plot(xs, ys, color=DARK, linewidth=0.85, linestyle="--" if dashed else "-", zorder=3)
        ax.add_patch(
            FancyArrowPatch(
                points[-2], points[-1], arrowstyle="-|>", mutation_scale=9,
                linewidth=0.85, color=DARK, linestyle="--" if dashed else "-",
                shrinkA=0, shrinkB=4, zorder=4,
            )
        )

    ax.text(0.5, 0.965, "自适应多尺度网络流量预测流程", ha="center", va="top", fontsize=10, weight="bold")
    box(0.025, 0.40, 0.12, 0.18, "流量窗口\n96×144", PALE)
    box(0.175, 0.40, 0.12, 0.18, "对数变换\n训练集标准化", "white")
    arrow(0.145, 0.49, 0.175, 0.49)

    lane_y = [0.69, 0.43, 0.17]
    lane_names = [("尺度1", "L=96"), ("尺度2", "L=48"), ("尺度4", "L=24")]
    for y, (name, length) in zip(lane_y, lane_names):
        box(0.34, y, 0.105, 0.13, f"{name}\n{length}", PALE)
        box(0.485, y, 0.14, 0.13, "频域筛选\nRFFT→门控→IRFFT", "white", fs=7.5)
        box(0.665, y, 0.12, 0.13, "DLinear\n趋势+余项", "white", fs=7.5)
        box(0.825, y, 0.075, 0.13, "预测\nŶ(s)", PALE, fs=7.5)
        arrow(0.445, y + 0.065, 0.485, y + 0.065)
        arrow(0.625, y + 0.065, 0.665, y + 0.065)
        arrow(0.785, y + 0.065, 0.825, y + 0.065)
    for y in lane_y:
        arrow(0.295, 0.49, 0.34, y + 0.065)

    box(0.37, 0.015, 0.31, 0.095,
        "样本级路由器：α=softmax(g(X))\n权重随样本变化，Σαs=1",
        "#e4e4e4", lw=1.1, fs=7.5)
    routed_arrow([(0.235, 0.40), (0.235, 0.063), (0.37, 0.063)], dashed=True)
    box(0.925, 0.40, 0.06, 0.18, "融合\nΣαsŶ(s)", "#dddddd", lw=1.1, fs=7.5)
    for y in lane_y:
        arrow(0.90, y + 0.065, 0.925, 0.49)
    routed_arrow([(0.68, 0.063), (0.955, 0.063), (0.955, 0.40)], dashed=True)
    save_bundle(fig, out_dir, "N1_方法流程")


def nature_formal_ablation(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.75), constrained_layout=True)
    for ax, metric, label in zip(axes, ["mse", "mae"], ["MSE", "MAE"]):
        for i, model in enumerate(MODEL_ORDER):
            vals = df.loc[df.model == model, metric].to_numpy()
            offsets = np.array([-0.10, 0, 0.10])
            ax.scatter(np.full(3, i) + offsets, vals, s=21, marker=MARKERS[i],
                       facecolors="white" if model != "dlinear_scale" else BLACK,
                       edgecolors=BLACK, linewidths=0.75, zorder=3)
            mean, sd = vals.mean(), vals.std(ddof=1)
            ax.errorbar(i, mean, yerr=sd, fmt="_", color=BLACK, capsize=3,
                        markersize=12, linewidth=0.9, zorder=4)
        ax.set_xticks(range(len(MODEL_ORDER)), [SHORT_MODEL_LABELS[x] for x in MODEL_ORDER])
        for tick in ax.get_xticklabels():
            tick.set_rotation(18)
            tick.set_ha("right")
            tick.set_rotation_mode("anchor")
        ax.set_ylabel(f"{label}（越低越好）")
        ax.set_title(f"{label}：原始种子与均值±SD")
        style_axis(ax)
    panel_label(axes[0], "a")
    panel_label(axes[1], "b")
    save_bundle(fig, OUT_NATURE, "N2_五模型正式消融")


def nature_weight_evidence(weight: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.5), constrained_layout=True, sharey=True)
    for ax, setting in zip(axes, weight.setting.unique()):
        part = weight[weight.setting == setting]
        for _, row in part.iterrows():
            ax.plot([0, 1], [row.fixed_mse, row.adaptive_mse], color=MID, marker="o", markersize=3.5, linewidth=0.8)
        means = [part.fixed_mse.mean(), part.adaptive_mse.mean()]
        ax.plot([0, 1], means, color=BLACK, marker="s", markersize=5, linewidth=1.7)
        reduction = (means[0] - means[1]) / means[0] * 100
        ax.set_title(f"{setting}\n降低 {reduction:.1f}%")
        ax.set_xticks([0, 1], ["固定等权", "自适应权重"])
        ax.set_xlim(-0.25, 1.35)
        style_axis(ax)
    axes[0].set_ylabel("MSE（越低越好）")
    for label, ax in zip("abc", axes):
        panel_label(ax, label)
    save_bundle(fig, OUT_NATURE, "N3_自适应权重证据")


def nature_frequency(freq: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.65), constrained_layout=True)
    styles = {"dlinear_freq": ("--", "o", DARK), "proposed": ("-", "s", BLACK)}
    labels = {"dlinear_freq": "DLinear+频域", "proposed": "频域门控+多尺度"}
    for ax, metric, title in zip(axes, ["mse", "mae"], ["MSE", "MAE"]):
        for model in ["dlinear_freq", "proposed"]:
            ls, marker, color = styles[model]
            means, sds, xs = [], [], []
            for ratio, part in freq[freq.model == model].groupby("cut_ratio"):
                vals = part[metric].to_numpy()
                xs.append(ratio); means.append(vals.mean()); sds.append(vals.std(ddof=1))
                ax.scatter(np.full(3, ratio) + np.array([-0.012, 0, 0.012]), vals, s=13,
                           marker=marker, facecolors="white", edgecolors=color, linewidths=0.65, zorder=3)
            ax.errorbar(xs, means, yerr=sds, color=color, linestyle=ls, marker=marker,
                        markersize=4.2, capsize=2.5, label=labels[model], zorder=4)
        ax.set_xticks([0.25, 0.50, 0.75])
        ax.set_xlabel("频域保留比例 $r$")
        ax.set_ylabel(f"{title}（越低越好）")
        style_axis(ax)
    axes[0].legend(frameon=False)
    panel_label(axes[0], "a"); panel_label(axes[1], "b")
    save_bundle(fig, OUT_NATURE, "N4_频域比例敏感性")


def nature_router_forecast(router: pd.DataFrame, forecast: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.75), constrained_layout=True)
    data = [router.loc[router.scale == scale, "router_weight"].to_numpy() for scale in [1, 2, 4]]
    vp = axes[0].violinplot(data, positions=[1, 2, 3], showmedians=True, showextrema=False, widths=0.75)
    for body, shade in zip(vp["bodies"], ["#d9d9d9", "#aaaaaa", "#737373"]):
        body.set_facecolor(shade); body.set_edgecolor(BLACK); body.set_alpha(1)
    vp["cmedians"].set_color(BLACK)
    axes[0].set_xticks([1, 2, 3], ["尺度1", "尺度2", "尺度4"])
    axes[0].set_ylabel("路由权重")
    axes[0].set_title("样本级权重分布（$n$=2439/尺度）")
    style_axis(axes[0])

    axes[1].plot(forecast.forecast_hour, forecast.truth, color=BLACK, linewidth=1.6, label="真实值")
    axes[1].plot(forecast.forecast_hour, forecast.dlinear_seed42, color=MID, linestyle="--", marker="o", markersize=2.6, label="DLinear")
    axes[1].plot(forecast.forecast_hour, forecast.adaptive_multiscale_seed42, color=DARK, linestyle="-.", marker="s", markersize=2.5, label="自适应多尺度")
    axes[1].set_xlabel("预测步（小时）"); axes[1].set_ylabel("标准化流量")
    axes[1].set_title("代表性24小时预测\n实线：真实值　虚线○：DLinear　点划□：自适应多尺度",
                      fontsize=7.5, linespacing=1.35)
    style_axis(axes[1])
    panel_label(axes[0], "a"); panel_label(axes[1], "b")
    save_bundle(fig, OUT_NATURE, "N5_路由机制与预测实例")


def scipilot_formal_ablation(df: pd.DataFrame) -> None:
    long = df.melt(id_vars=["model", "seed"], value_vars=["mse", "mae"], var_name="metric", value_name="value")
    fig, axes = plt.subplots(2, 1, figsize=(6.7, 4.8), constrained_layout=True)
    for ax, metric, title in zip(axes, ["mse", "mae"], ["MSE", "MAE"]):
        sub = long[long.metric == metric]
        for i, model in enumerate(MODEL_ORDER):
            vals = sub.loc[sub.model == model, "value"].to_numpy()
            ax.scatter(vals, np.full_like(vals, i) + np.array([-0.08, 0, 0.08]),
                       marker=MARKERS[i], s=28, facecolors="white", edgecolors=BLACK, zorder=3)
            ax.plot([vals.mean() - vals.std(ddof=1), vals.mean() + vals.std(ddof=1)], [i, i], color=BLACK, linewidth=1.2)
            ax.scatter(vals.mean(), i, marker="|", s=120, color=BLACK, zorder=4)
        ax.set_yticks(range(5), [MODEL_LABELS[x] for x in MODEL_ORDER])
        ax.invert_yaxis(); ax.set_xlabel(f"{title}（点=种子；横线=均值±SD）")
        ax.set_title(f"{title} 的完整三随机种子结果")
        ax.grid(axis="x", color="#dddddd", linestyle="--", linewidth=0.45)
        ax.spines[["top", "right", "left"]].set_visible(False)
        panel_label(ax, "a" if metric == "mse" else "b")
    save_bundle(fig, OUT_SCIPILOT, "S1_小样本透明化消融")


def scipilot_paired(weight: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(6.7, 2.9), constrained_layout=True)
    positions = np.arange(len(weight.setting.unique()))
    for i, setting in enumerate(weight.setting.unique()):
        part = weight[weight.setting == setting]
        for _, row in part.iterrows():
            axes[0].plot([2 * i, 2 * i + 0.75], [row.fixed_mse, row.adaptive_mse], color=MID, linewidth=0.75, marker="o", markersize=3)
        delta = (part.fixed_mse.to_numpy() - part.adaptive_mse.to_numpy()) / part.fixed_mse.to_numpy() * 100
        axes[1].scatter(np.full(3, i) + np.array([-0.10, 0, 0.10]), delta, s=27, facecolors="white", edgecolors=BLACK)
        axes[1].scatter(i, delta.mean(), marker="_", s=130, color=BLACK)
    axes[0].set_xticks([0.375, 2.375, 4.375], ["无频域", "$r$=0.50", "$r$=0.75"])
    axes[0].set_ylabel("MSE"); axes[0].set_title("同一种子的固定—自适应配对")
    axes[0].text(0.02, 0.96, "左点：固定等权\n右点：自适应权重",
                 transform=axes[0].transAxes, fontsize=7.5, va="top", ha="left", color=DARK)
    axes[1].axhline(0, color=MID, linewidth=0.7)
    axes[1].set_xticks(positions, ["无频域", "$r$=0.50", "$r$=0.75"])
    axes[1].set_ylabel("相对MSE降低（%）"); axes[1].set_title("每个种子的改进幅度")
    for ax in axes: style_axis(ax)
    panel_label(axes[0], "a"); panel_label(axes[1], "b")
    save_bundle(fig, OUT_SCIPILOT, "S2_配对权重消融")


def scipilot_frequency(freq: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(6.7, 2.75), constrained_layout=True)
    for ax, metric, label in zip(axes, ["mse", "mae"], ["MSE", "MAE"]):
        for model, ls, marker, name in [("dlinear_freq", "--", "o", "DLinear+频域"), ("proposed", "-", "s", "频域门控+多尺度")]:
            sub = freq[freq.model == model]
            for seed, part in sub.groupby("seed"):
                ax.plot(part.cut_ratio, part[metric], color=LIGHT if model == "dlinear_freq" else MID,
                        linestyle=ls, marker=marker, markersize=2.6, linewidth=0.65)
            g = sub.groupby("cut_ratio")[metric]
            xs = np.array(sorted(sub.cut_ratio.unique()))
            ax.plot(xs, g.mean().reindex(xs), color=DARK if model == "dlinear_freq" else BLACK,
                    linestyle=ls, marker=marker, markersize=5, linewidth=1.6, label=name)
        ax.set_xticks([0.25, 0.50, 0.75]); ax.set_xlabel("频域保留比例 $r$"); ax.set_ylabel(label)
        ax.set_title(f"{label}：细线为种子，粗线为均值")
        style_axis(ax)
    axes[0].legend(frameon=False)
    panel_label(axes[0], "a"); panel_label(axes[1], "b")
    save_bundle(fig, OUT_SCIPILOT, "S3_频域敏感性原始轨迹")


def scipilot_router_forecast(router: pd.DataFrame, forecast: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(6.7, 5.1), constrained_layout=True)
    scales = [1, 2, 4]
    for scale, shade in zip(scales, [LIGHT, MID, DARK]):
        means = router[router.scale == scale].groupby("test_window_index").router_weight.mean()
        axes[0, 0].plot(means.index, means.values, color=shade, linewidth=0.75, label=f"尺度{scale}")
    axes[0, 0].set_xlabel("测试窗口"); axes[0, 0].set_ylabel("三种子平均权重")
    axes[0, 0].set_title("权重随样本变化"); axes[0, 0].legend(frameon=False, ncol=3)

    distributions = [router.loc[router.scale == scale, "router_weight"].to_numpy() for scale in scales]
    violins = axes[0, 1].violinplot(distributions, positions=range(3), widths=0.72,
                                    showmedians=True, showextrema=False)
    for body, shade in zip(violins["bodies"], ["#d9d9d9", "#aaaaaa", "#737373"]):
        body.set_facecolor(shade); body.set_edgecolor(BLACK); body.set_alpha(1)
    violins["cmedians"].set_color(BLACK)
    axes[0, 1].set_xticks(range(3), [f"尺度{s}" for s in scales]); axes[0, 1].set_ylabel("路由权重")
    axes[0, 1].set_title("权重分布（$n$=2439/尺度）")

    axes[1, 0].plot(forecast.forecast_hour, forecast.truth, color=BLACK, linewidth=1.6, label="真实值")
    axes[1, 0].plot(forecast.forecast_hour, forecast.dlinear_seed42, color=MID, linestyle="--", marker="o", markersize=2.5, label="DLinear")
    axes[1, 0].plot(forecast.forecast_hour, forecast.adaptive_multiscale_seed42, color=DARK, linestyle="-.", marker="s", markersize=2.4, label="自适应多尺度")
    axes[1, 0].set_xlabel("预测步（小时）"); axes[1, 0].set_ylabel("标准化流量")
    axes[1, 0].set_title("代表性预测曲线"); axes[1, 0].legend(frameon=False, ncol=3)

    err_d = np.abs(forecast.truth - forecast.dlinear_seed42)
    err_a = np.abs(forecast.truth - forecast.adaptive_multiscale_seed42)
    axes[1, 1].plot(forecast.forecast_hour, err_d, color=MID, linestyle="--", marker="o", markersize=2.5, label="DLinear")
    axes[1, 1].plot(forecast.forecast_hour, err_a, color=BLACK, marker="s", markersize=2.4, label="自适应多尺度")
    axes[1, 1].fill_between(forecast.forecast_hour, err_d, err_a, where=err_a < err_d, color="#dddddd", alpha=0.65)
    axes[1, 1].set_xlabel("预测步（小时）"); axes[1, 1].set_ylabel("绝对误差")
    axes[1, 1].set_title("逐小时误差对比"); axes[1, 1].legend(frameon=False)
    for ax, label in zip(axes.flat, "abcd"):
        style_axis(ax); panel_label(ax, label)
    save_bundle(fig, OUT_SCIPILOT, "S4_路由与预测诊断")


def scipilot_router_only(router: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(6.7, 2.65), constrained_layout=True)
    scales = [1, 2, 4]
    for scale, shade in zip(scales, [LIGHT, MID, DARK]):
        means = router[router.scale == scale].groupby("test_window_index").router_weight.mean()
        axes[0].plot(means.index, means.values, color=shade, linewidth=0.75, label=f"尺度{scale}")
    axes[0].set_xlabel("测试窗口"); axes[0].set_ylabel("三种子平均权重")
    axes[0].set_title("权重随样本变化"); axes[0].legend(frameon=False, ncol=3)

    distributions = [router.loc[router.scale == scale, "router_weight"].to_numpy() for scale in scales]
    violins = axes[1].violinplot(distributions, positions=range(3), widths=0.72,
                                 showmedians=True, showextrema=False)
    for body, shade in zip(violins["bodies"], ["#d9d9d9", "#aaaaaa", "#737373"]):
        body.set_facecolor(shade); body.set_edgecolor(BLACK); body.set_alpha(1)
    violins["cmedians"].set_color(BLACK)
    axes[1].set_xticks(range(3), [f"尺度{s}" for s in scales]); axes[1].set_ylabel("路由权重")
    axes[1].set_title("权重分布（$n$=2439/尺度）")
    for ax, label in zip(axes, "ab"):
        style_axis(ax); panel_label(ax, label)
    save_bundle(fig, OUT_SCIPILOT, "S4a_路由权重诊断")


def scipilot_forecast_only(forecast: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(6.7, 2.65), constrained_layout=True)
    axes[0].plot(forecast.forecast_hour, forecast.truth, color=BLACK, linewidth=1.6, label="真实值")
    axes[0].plot(forecast.forecast_hour, forecast.dlinear_seed42, color=MID, linestyle="--", marker="o", markersize=2.5, label="DLinear")
    axes[0].plot(forecast.forecast_hour, forecast.adaptive_multiscale_seed42, color=DARK, linestyle="-.", marker="s", markersize=2.4, label="自适应多尺度")
    axes[0].set_xlabel("预测步（小时）"); axes[0].set_ylabel("标准化流量")
    axes[0].set_title("代表性预测曲线"); axes[0].legend(frameon=False, ncol=3)

    err_d = np.abs(forecast.truth - forecast.dlinear_seed42)
    err_a = np.abs(forecast.truth - forecast.adaptive_multiscale_seed42)
    axes[1].plot(forecast.forecast_hour, err_d, color=MID, linestyle="--", marker="o", markersize=2.5, label="DLinear")
    axes[1].plot(forecast.forecast_hour, err_a, color=BLACK, marker="s", markersize=2.4, label="自适应多尺度")
    axes[1].fill_between(forecast.forecast_hour, err_d, err_a, where=err_a < err_d, color="#dddddd", alpha=0.65)
    axes[1].set_xlabel("预测步（小时）"); axes[1].set_ylabel("绝对误差")
    axes[1].set_title("逐小时误差对比"); axes[1].legend(frameon=False)
    for ax, label in zip(axes, "ab"):
        style_axis(ax); panel_label(ax, label)
    save_bundle(fig, OUT_SCIPILOT, "S4b_代表性预测诊断")


def main() -> None:
    data = load_data()
    draw_method_flow(OUT_NATURE)
    nature_formal_ablation(data["formal"])
    nature_weight_evidence(data["weight"])
    nature_frequency(data["frequency"])
    nature_router_forecast(data["router"], data["forecast"])
    scipilot_formal_ablation(data["formal"])
    scipilot_paired(data["weight"])
    scipilot_frequency(data["frequency"])
    scipilot_router_forecast(data["router"], data["forecast"])
    scipilot_router_only(data["router"])
    scipilot_forecast_only(data["forecast"])
    print(f"nature-figure outputs: {OUT_NATURE}")
    print(f"scipilot outputs: {OUT_SCIPILOT}")


if __name__ == "__main__":
    main()
