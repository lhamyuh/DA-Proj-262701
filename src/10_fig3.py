"""10_fig3.py — Fig3：洛伦兹曲线 + 最低 20% 群体对比（B，2026-11-14）

输出
    outputs/figures/fig3_lorenz.png             3300 × 1500（300 dpi，报告用）
    outputs/figures/slide/fig3_lorenz_slide.jpg 3200 宽（幻灯片用）

数据：handoff/2026-11-10/accessibility.csv（in_study 且 pop>0）
口径：与 equity_table.csv 同一套（人口加权、按 p1k 升序累加）

运行：python src/10_fig3.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ACC = ROOT / "handoff" / "2026-11-10" / "accessibility.csv"
FIG = ROOT / "outputs" / "figures"

plt.rcParams.update({
    "font.family": "Arial",
    "axes.edgecolor": "#444444", "axes.labelcolor": "#1a1a1a",
    "xtick.color": "#333333", "ytick.color": "#333333",
    "axes.spines.top": False, "axes.spines.right": False,
})

NAVY = "#14468C"
BRICK = "#B03A2E"
PALE = "#7FB3D5"


def lorenz(acc: pd.DataFrame, d0: int):
    v = acc[(acc.d0_m == d0) & acc.in_study & (acc["pop"] > 0)].sort_values(
        "piles_per_1000", kind="mergesort")
    w = v["pop"].to_numpy(float)
    m = v["piles_per_1000"].to_numpy(float) * w
    cx = np.r_[0.0, np.cumsum(w) / w.sum()]
    cy = np.r_[0.0, np.cumsum(m) / m.sum()]
    return cx, cy, 1.0 - 2.0 * np.trapz(cy, cx), v


def main() -> int:
    acc = pd.read_csv(ACC, encoding="utf-8-sig")
    curves = {d: lorenz(acc, d) for d in (1000, 3000, 5000)}

    v3 = curves[3000][3]
    w = v3["pop"].to_numpy(float)
    a = v3["piles_per_1000"].to_numpy(float)
    order = np.argsort(a, kind="mergesort")
    target = 0.20 * w.sum()
    taken = tot = 0.0
    for i in order:
        if taken >= target - 1e-12:
            break
        piece = min(w[i], target - taken)
        taken += piece
        tot += a[i] * piece
    bottom_mean = tot / taken
    rest_mean = ((a * w).sum() - tot) / (w.sum() - taken)
    ratio = rest_mean / bottom_mean
    y20 = float(np.interp(0.20, curves[3000][0], curves[3000][1]))

    fig = plt.figure(figsize=(11.0, 5.2), dpi=300)
    ax1 = fig.add_axes([0.055, 0.175, 0.335, 0.670])
    ax2 = fig.add_axes([0.515, 0.175, 0.455, 0.670])

    # ---------------- (a) Lorenz ----------------
    ax1.set_axisbelow(True)
    ax1.grid(True, ls=":", lw=0.7, color="#d0d0d0")
    ax1.plot([0, 1], [0, 1], ls=(0, (4, 3)), color="#8a8a8a", lw=1.1, zorder=1)
    styles = {1000: (BRICK, 1.7, 3), 3000: (NAVY, 3.0, 5), 5000: (PALE, 1.7, 4)}
    for d0 in (1000, 3000, 5000):
        cx, cy, g, _ = curves[d0]
        color, lw, z = styles[d0]
        ax1.plot(cx, cy, color=color, lw=lw, zorder=z, solid_capstyle="round",
                 label=f"d0 = {d0 // 1000} km     Gini {g:.3f}")
    cx, cy, _, _ = curves[3000]
    ax1.fill_between(cx, cy, cx, color=NAVY, alpha=0.05, zorder=0)
    ax1.vlines(0.20, 0, y20, color="#9a9a9a", lw=0.9, ls=":", zorder=2)
    ax1.plot([0.20], [y20], marker="o", ms=7, mfc=NAVY, mec="white", mew=1.3, zorder=8)
    ax1.text(0.243, 0.043, "6.6%", fontsize=9.0, color=NAVY, ha="left", va="bottom", zorder=9)
    ax1.text(0.60, 0.648, "perfect equality", fontsize=7.4, color="#8a8a8a",
             rotation=45, rotation_mode="anchor", ha="left", va="bottom", zorder=2)

    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.set_aspect("equal", adjustable="box", anchor="C")
    ax1.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax1.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax1.set_xlabel("Cumulative share of residents", fontsize=9.4)
    ax1.set_ylabel("Cumulative share of accessibility", fontsize=9.4)
    ax1.tick_params(labelsize=8.4)
    ax1.legend(loc="upper left", frameon=False, fontsize=8.6, handlelength=2.2,
               borderaxespad=0.35, labelspacing=0.45, handletextpad=0.6).set_zorder(10)

    # ---------------- (b) 两组人均 ----------------
    labels = ["Remaining 80%", "Lowest 20%"]
    vals = [rest_mean, bottom_mean]
    colors = ["#C8D6E5", BRICK]
    bars = ax2.barh(labels, vals, color=colors, height=0.46, zorder=3)
    ax2.set_axisbelow(True)
    ax2.grid(True, axis="x", ls=":", lw=0.7, color="#d0d0d0")
    for b, val in zip(bars, vals):
        ax2.text(val + 0.045, b.get_y() + b.get_height() / 2, f"{val:.2f}",
                 va="center", ha="left", fontsize=11.5, color="#1a1a1a", fontweight="bold")
    ax2.set_ylim(-0.62, 1.62)
    ax2.set_xlim(0, max(vals) * 1.30)
    ax2.set_xlabel("Mean accessible capacity (piles per 1,000 residents)", fontsize=9.4)
    ax2.tick_params(labelsize=9.6, axis="y")
    ax2.tick_params(labelsize=8.4, axis="x")

    ax2.annotate("", xy=(1.02, 0.76), xytext=(1.02, 0.24),
                 arrowprops=dict(arrowstyle="<->", lw=1.0, color="#8a8a8a"))
    ax2.text(1.07, 0.50, f"{ratio:.1f}×  higher", fontsize=9.6, color="#444444", va="center")

    # ---------------- 图题与脚注 ----------------
    fig.text(0.012, 0.985, "Fig 3  Accessibility inequality across the 997 study cells",
             fontsize=13.0, fontweight="bold", color="#111111", va="top")
    fig.text(0.012, 0.945,
             "Gaussian-2SFCA, public charging in Shenzhen  ·  2020 census population  ·  station supply, 2022–2023",
             fontsize=8.4, color="#555555", va="top")
    fig.text(0.055, 0.878, "(a) Lorenz curve", fontsize=11.0, fontweight="bold", color="#111111")
    fig.text(0.515, 0.878, "(b) Mean accessibility by group, d0 = 3 km",
             fontsize=11.0, fontweight="bold", color="#111111")
    fig.text(0.012, 0.018,
             f"997 study cells, 951 of them populated  ·  "
             f"lowest 20% = {taken:,.0f} residents, holding {y20 * 100:.1f}% of total accessibility",
             fontsize=7.6, color="#6b6b6b", va="bottom")

    png = FIG / "fig3_lorenz.png"
    fig.savefig(png, dpi=300, facecolor="white")
    print(f"[out] {png}  {Image.open(png).size}")

    slide_dir = FIG / "slide"
    slide_dir.mkdir(exist_ok=True)
    im = Image.open(png).convert("RGB")
    wpx = 3200
    im = im.resize((wpx, round(im.height * wpx / im.width)), Image.LANCZOS)
    jpg = slide_dir / "fig3_lorenz_slide.jpg"
    im.save(jpg, quality=92, optimize=True)
    print(f"[out] {jpg}  {im.size}")
    print(f"      bottom20 {bottom_mean:.6f} | rest {rest_mean:.6f} | ratio {ratio:.2f} | y20 {y20:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
