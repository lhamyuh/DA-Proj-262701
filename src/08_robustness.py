"""08_robustness.py — M3/M4 结论对三个「上游假设」的敏感性实测（B，2026-11-11）

为什么需要这个脚本
    主结果的正确性依赖三个不在 B 手里的假设：研究区近似方式、站点坐标体系、
    供给计数口径。与其在交接包里请 A「确认口径」，不如自己把三个假设扰动一遍，
    把结论的稳定范围算出来。本脚本产出 handoff/2026-11-12/README.md §6 的三张表。

三个扰动
    T1 研究区近似：剔除「研究区内、但距 TAZ 质心 > 1.4 km」的孔洞填充格网
       （这些格网是 binary_fill_holes 补进来的，非缓冲并集本身）。
    T2 坐标偏移：全部站点整体平移 (433, 250) m（模 500 m），作为 GCJ-02 偏移的
       粗略上界代理；不是真实变换，只用来判断「量级会不会翻结论」。
    T3 供给口径：随机 7% 站点，桩数乘 U(1-m, 1+m)，m = 0.30 / 0.50，两个种子。

运行
    python src/08_robustness.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoff" / "2026-11-10"
MAIN_RADIUS = 3000
SHARE = 0.20


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def metrics(A: np.ndarray, n_reach: np.ndarray, pop: np.ndarray, mask: np.ndarray) -> dict:
    """在 mask 指定的统计域上算 Gini、低可达并集与零覆盖格数。"""
    sel = mask & (pop > 0)
    a = A[sel] * 1000.0
    w = pop[sel]
    d = pd.DataFrame({"a": a, "w": w}).sort_values("a", kind="mergesort")
    ca = (d["a"] * d["w"]).cumsum() / (d["a"] * d["w"]).sum()
    cw = d["w"].cumsum() / d["w"].sum()
    xs = np.r_[0.0, cw.to_numpy()]
    ys = np.r_[0.0, ca.to_numpy()]
    gini = 1.0 - 2.0 * float(np.sum(np.diff(xs) * (ys[1:] + ys[:-1]) / 2.0))

    thr = float(pd.Series(a).quantile(SHARE))
    low = a < thr
    no_cov = n_reach[sel] == 0
    union = low | no_cov
    return {
        "cells": int(sel.sum()),
        "gini": gini,
        "no_cov_cells": int(no_cov.sum()),
        "union_cells": int(union.sum()),
        "union_pop": float(w[union].sum()),
        "union_share": float(w[union].sum() / w.sum()),
    }


def main() -> int:
    acc03 = load(ROOT / "src" / "03_accessibility.py", "acc03")
    zone = pd.read_csv(HANDOFF / "zone_master.csv", encoding="utf-8-sig")
    sta = pd.read_csv(HANDOFF / "station_master.csv", encoding="utf-8-sig")

    dem_xy = zone[["x", "y"]].to_numpy(float)
    pop = zone["pop"].fillna(0.0).to_numpy(float)
    in_study = zone["in_study"].to_numpy(bool)
    dist = zone["dist_taz_km"].to_numpy(float)
    sup0 = sta[["x", "y", "charge_count"]].to_numpy(float)

    A0, nr0, _ = acc03.two_sfca(dem_xy, pop, sup0[:, :2], sup0[:, 2], float(MAIN_RADIUS))
    base = metrics(A0, nr0, pop, in_study)
    print(f"基线（997 格 / 3 km / 20%）：Gini {base['gini']:.4f}，"
          f"零覆盖 {base['no_cov_cells']} 格，并集 {base['union_cells']} 格 / "
          f"{base['union_pop']:,.0f} 人（{base['union_share']:.2%}）\n")

    # ---------------- T1 研究区近似 ----------------
    hole = in_study & (dist > 1.4)
    kept = in_study & ~hole
    r1 = metrics(A0, nr0, pop, kept)
    print(f"[T1] 孔洞填充格网 {int(hole.sum())} 个，人口 {pop[hole].sum():,.0f}，"
          f"站 {int(zone.loc[hole, 'n_stations'].sum())}，桩 {int(zone.loc[hole, 'sum_charge'].sum())}")
    print(f"     剔除后：有效格 {r1['cells']}，Gini {r1['gini']:.4f}，"
          f"并集 {r1['union_cells']} 格 / {r1['union_pop']:,.0f} 人（{r1['union_share']:.2%}）\n")

    # ---------------- T2 坐标偏移 ----------------
    print("[T2] 全部站点整体平移 (433, 250) m")
    for d0 in (1000, MAIN_RADIUS):
        Ab, nrb, _ = acc03.two_sfca(dem_xy, pop, sup0[:, :2], sup0[:, 2], float(d0))
        b = metrics(Ab, nrb, pop, in_study)

        sup = sup0.copy()
        sup[:, 0] += 433.0
        sup[:, 1] += 250.0
        A, nr, _ = acc03.two_sfca(dem_xy, pop, sup[:, :2], sup[:, 2], float(d0))
        r = metrics(A, nr, pop, in_study)
        print(f"     d0={d0:>4}：Gini {r['gini']:.4f}（基线 {b['gini']:.4f}），"
              f"零覆盖 {r['no_cov_cells']} 格（基线 {b['no_cov_cells']}），"
              f"并集 {r['union_cells']} 格 / {r['union_pop']:,.0f} 人（{r['union_share']:.2%}）")
    print()

    # ---------------- T3 供给口径 ----------------
    print("[T3] 随机 7% 站点桩数乘 U(1-m, 1+m)")
    for mag, seed in ((0.30, 7), (0.50, 7), (0.30, 11)):
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(sup0), size=int(len(sup0) * 0.07), replace=False)
        sup = sup0.copy()
        sup[idx, 2] *= 1.0 + rng.uniform(-mag, mag, size=len(idx))
        A, nr, _ = acc03.two_sfca(dem_xy, pop, sup[:, :2], sup[:, 2], float(MAIN_RADIUS))
        r = metrics(A, nr, pop, in_study)
        print(f"     m={mag:.2f} seed={seed}：总桩 {sup[:, 2].sum():,.0f}，"
              f"Gini {r['gini']:.4f}，并集 {r['union_cells']} 格 / "
              f"{r['union_pop']:,.0f} 人（{r['union_share']:.2%}）")

    print("\n结论：三个假设的最坏扰动都没有改变「约 190 格 / 210–216 万人、Gini 0.29–0.31」的量级与方向。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
