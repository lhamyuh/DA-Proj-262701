#!/usr/bin/env python3
"""03_accessibility.py — Gaussian-2SFCA 可达性（M2）

方法说明（A 需能口述）
  两步式浮动搜索半径法：
    第一步  R_j = S_j / Σ_k P_k · g(d_kj)   —— 每个站点的"供需比"，分母是它能服务的需求
    第二步  A_i = Σ_j R_j · g(d_ij)          —— 每个需求单元拿到的加权供给
  其中 g(d) 为截断高斯核：在 d ≤ d0 内归一化到 [0,1]，d > d0 取 0。
  供给 S_j 取**桩数**（charge_count），需求 P_i 取格网人口。
  主半径 d0 = 3 km，对照 1 km 与 5 km；距离为 Albers 等积投影下的平面欧氏距离（米）。

自检
  - 零分母站点（附近无人口）单独标记，不分配供给，不设 R 为无穷。
  - 人口加权总量回收：Σ P_i A_i / Σ S_j 应接近 1（差值来自边界外需求与零分母站点）。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.spatial import cKDTree

os.environ.setdefault("GDAL_DATA", r"D:\miniconda3\envs\ev311\Library\share\gdal")
os.environ.setdefault("PROJ_LIB", r"D:\miniconda3\envs\ev311\Library\share\proj")

ROOT = Path(__file__).resolve().parents[1]


def log(m: str) -> None:
    print(m, flush=True)


def gaussian_kernel(d: np.ndarray, d0: float) -> np.ndarray:
    """截断高斯：d ∈ [0, d0] 内归一化到 [0, 1]，d > d0 为 0。"""
    e = np.exp(-0.5)
    g = (np.exp(-0.5 * (d / d0) ** 2) - e) / (1.0 - e)
    return np.where(d <= d0, g, 0.0)


def two_sfca(dem_xy: np.ndarray, pop: np.ndarray, sup_xy: np.ndarray,
             sup: np.ndarray, d0: float) -> tuple[np.ndarray, dict]:
    tree_s = cKDTree(sup_xy)
    tree_d = cKDTree(dem_xy)

    # ---- 第一步：R_j ----
    denom = np.zeros(len(sup_xy))
    for j, nb in enumerate(tree_d.query_ball_point(sup_xy, d0)):
        if nb:
            d = np.linalg.norm(dem_xy[nb] - sup_xy[j], axis=1)
            denom[j] = (np.asarray(pop)[nb] * gaussian_kernel(d, d0)).sum()
    zero_denom = denom <= 0
    R = np.divide(sup, denom, out=np.zeros_like(denom), where=~zero_denom)

    # ---- 第二步：A_i ----
    A = np.zeros(len(dem_xy))
    n_reach = np.zeros(len(dem_xy), dtype=int)
    for i, nb in enumerate(tree_s.query_ball_point(dem_xy, d0)):
        if nb:
            d = np.linalg.norm(sup_xy[nb] - dem_xy[i], axis=1)
            w = gaussian_kernel(d, d0)
            A[i] = float((R[nb] * w).sum())
            n_reach[i] = int((w > 0).sum())

    info = dict(
        stations=len(sup_xy),
        stations_zero_denominator=int(zero_denom.sum()),
        supply_total=float(np.asarray(sup)[~zero_denom].sum()),
        supply_total_all=float(np.asarray(sup).sum()),
        recovery_ratio=float((pop * A).sum() / np.asarray(sup)[~zero_denom].sum())
        if np.asarray(sup)[~zero_denom].sum() > 0 else np.nan,
        cells_with_station_in_radius=int((n_reach > 0).sum()),
        cells_without_station_in_radius=int((n_reach == 0).sum()),
    )
    return A, n_reach, info


def main() -> int:
    cfg = yaml.safe_load((ROOT / "config.yaml").open(encoding="utf-8"))
    processed = ROOT / cfg["paths"]["processed"]
    qa_dir = ROOT / cfg["paths"]["qa"]

    zm = pd.read_parquet(processed / "zone_master.parquet")
    sm = pd.read_parquet(processed / "station_master.parquet")

    # 需求集 = 市域内全部格网（2SFCA 分母须包含半径内所有人口，不能只取研究区）
    study_cells = set(zm.loc[zm.in_study, "cell_id"])
    st = sm[sm.cell_id.isin(study_cells)].copy()
    dem_xy = zm[["x", "y"]].to_numpy(dtype=float)
    dem_pop = zm["pop"].fillna(0.0).to_numpy(dtype=float)
    sup_all = sm[["x", "y", "charge_count"]].to_numpy(dtype=float)
    log(f"[in] 需求单元（市域）{len(zm)}；研究区 {len(study_cells)}；供给站点 {len(st)}（区内）/ {len(sm)}（全部）")

    radii = [cfg["accessibility"]["radius_main_m"]] + list(cfg["accessibility"]["radius_sensitivity_m"])
    radii = sorted(set(int(r) for r in radii))
    rows, checks = [], []

    for d0 in radii:
        A, n_reach, info = two_sfca(
            dem_xy=dem_xy, pop=dem_pop,
            sup_xy=sup_all[:, 0:2], sup=sup_all[:, 2], d0=float(d0))
        out = zm[["cell_id", "x", "y", "pop", "in_study"]].copy()
        out["d0_m"] = d0
        out["A_i"] = A
        out["piles_per_1000"] = np.where(out["pop"] > 0, A * 1000.0, np.nan)
        out["n_stations_in_radius"] = n_reach
        out["supply_metric"] = cfg["accessibility"]["supply_metric"]
        out["distance_type"] = cfg["accessibility"]["distance_type"]
        rows.append(out)
        checks.append(dict(d0_m=d0, **info))
        s = out[out.in_study]
        log(f"[run] d0={d0:>4d} m | 零分母站 {info['stations_zero_denominator']:>3d} | "
            f"半径内无站的单元 {info['cells_without_station_in_radius']:>3d}（区内 {int((s.n_stations_in_radius==0).sum())}）| "
            f"回收比 {info['recovery_ratio']:.4f} | 区内 A_i 均值 {s.A_i.mean():.6f} 中位 {s.A_i.median():.6f}")

    acc = pd.concat(rows, ignore_index=True)
    acc.to_parquet(processed / "accessibility.parquet", index=False)

    ck = pd.DataFrame(checks)
    lines = ["# M2 可达性报告（Gaussian-2SFCA）", "",
             f"- 需求单元：{len(zm)} 个 1 km 格网；供给：{len(sup_all)} 个站点（供给口径=桩数）",
             f"- 核函数：截断高斯；距离：Albers 平面欧氏（米）",
             f"- 半径：{radii}（米）", "",
             "## 自检", "",
             "| d0(m) | 零分母站 | 半径内无站单元 | 人口加权回收比 | A_i 均值 | A_i 中位数 | A_i 最大 |",
             "|---:|---:|---:|---:|---:|---:|---:|"]
    for (_, r), d0 in zip(ck.iterrows(), radii):
        sub = acc[acc.d0_m == d0]
        lines.append(f"| {d0} | {r.stations_zero_denominator} | {r.cells_without_station_in_radius} | "
                     f"{r.recovery_ratio:.4f} | {sub.A_i.mean():.6f} | {sub.A_i.median():.6f} | {sub.A_i.max():.6f} |")
    lines += ["", "## 口径与局限", "",
              "1. 供给取桩数（`charge_count`）；不主张'车桩比'，A_i 单位为桩/人，×1000 报“每千人桩数”。",
              "2. 零分母站点不参与分配、R 不设为无穷，其供给不计入回收比的分母。",
              "3. 需求点取格网中心；未用人口加权中心（无 TAZ 多边形，无法计算）。",
              "4. 直线距离，非路网距离或驾车时间；结果表述为“可达性差异”，不作因果解释。",
              "5. 回收比 <1 的差额来自：研究区外需求未计入、以及站点服务范围跨越研究区边界。"]
    (qa_dir / "m2_report.md").write_text("\n".join(lines), encoding="utf-8")

    log("")
    log(f"[out] {processed / 'accessibility.parquet'}  {len(acc)} 行（{len(radii)} 套半径）")
    log(f"[out] {qa_dir / 'm2_report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
