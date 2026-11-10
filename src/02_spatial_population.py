#!/usr/bin/env python3
"""02_spatial_population.py — 研究区格网、人口聚合与供给主表（M1）

方法说明（A 需能口述）
  输入：UrbanEV 站点/分区静态表（WGS84）、全国 100 m 人口栅格（Albers 等积投影）、深圳区界 GeoJSON。
  处理：① 把深圳 bbox 转到栅格 CRS 后按手算窗口裁剪（绕开 rasterio.transform 的 ctypes 崩溃）；
        ② 在 100 m 栅格上叠加 1 km 规则格网（10×10 像元求和），得到格网人口；
        ③ 研究区 = 区界内、且距最近 TAZ 质心 ≤ R 的格网单元（R 按 275 个 TAZ 面积总量标定）；
        ④ 站点由 WGS84 投影到同一 CRS 并落入格网。
  关键假设：
    - 数据集**没有 TAZ 多边形**，只有质心与面积，故需求单元只能用格网，不能做 TAZ 级人口聚合（已写入局限）。
    - 人口像元值语义为"人/像元"，NoData 不当 0。
    - 距离在 Albers 等积投影下按平面欧氏计算，单位米。
  输出：data/processed/station_master.parquet、zone_master.parquet、pop_shenzhen_100m.tif，
        以及 outputs/qa/m1_report.md。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

os.environ.setdefault("GDAL_DATA", r"D:\miniconda3\envs\ev311\Library\share\gdal")
os.environ.setdefault("PROJ_LIB", r"D:\miniconda3\envs\ev311\Library\share\proj")

import geopandas as gpd
import rasterio
from affine import Affine
from pyproj import Transformer
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]


def log(m: str) -> None:
    print(m, flush=True)


def load_cfg() -> dict:
    with (ROOT / "config.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def clip_population(cfg: dict) -> Path:
    """把全国栅格裁剪到深圳 bbox，返回裁剪后路径。已存在则跳过。"""
    src = ROOT / cfg["paths"]["raw"] / "_pop" / "PopSE_China2020_100m.tif"
    out = ROOT / cfg["paths"]["processed"] / "pop_shenzhen_100m.tif"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        log(f"[skip] 裁剪文件已存在：{out.relative_to(ROOT)}")
        return out

    lon0, lat0, lon1, lat1 = 113.70, 22.40, 114.60, 22.92
    with rasterio.open(src) as ds:
        T = ds.transform
        tr = Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True)
        xs, ys = zip(*[tr.transform(lon, lat) for lon, lat in
                       [(lon0, lat0), (lon1, lat0), (lon0, lat1), (lon1, lat1)]])
        col0 = max(int(round((min(xs) - T.c) / T.a)), 0)
        col1 = min(int(round((max(xs) - T.c) / T.a)), ds.width)
        row0 = max(int(round((max(ys) - T.f) / T.e)), 0)
        row1 = min(int(round((min(ys) - T.f) / T.e)), ds.height)
        win = rasterio.windows.Window(col0, row0, col1 - col0, row1 - row0)
        data = ds.read(1, window=win)
        pop = data.astype("float32")
        pop[data == ds.nodata] = np.nan
        T2 = Affine(T.a, T.b, T.c + col0 * T.a, T.d, T.e, T.f + row0 * T.e)
        prof = dict(driver="GTiff", height=data.shape[0], width=data.shape[1], count=1,
                    dtype="float32", crs=ds.crs, transform=T2, nodata=np.nan,
                    compress="lzw", tiled=True, blockxsize=128, blockysize=128)
    with rasterio.open(out, "w", **prof) as o:
        o.write(pop, 1)
    log(f"[ok] 裁剪完成 {out.relative_to(ROOT)}  {data.shape[1]}x{data.shape[0]} px")
    return out


def calibrate_radius(taz: gpd.GeoDataFrame, target_km2: float,
                     x0: float, x1: float, y0: float, y1: float, cell: float) -> tuple[float, dict]:
    """按 TAZ 面积总量标定缓冲半径 R：使落入缓冲并集的格网数 ≈ 目标面积（km²）。"""
    gx = np.arange(np.floor(x0 / cell) * cell + cell / 2, x1, cell)
    gy = np.arange(np.floor(y0 / cell) * cell + cell / 2, y1, cell)
    XX, YY = np.meshgrid(gx, gy)
    pts = np.c_[XX.ravel(), YY.ravel()]
    tree = cKDTree(np.c_[taz.geometry.x, taz.geometry.y])
    sel: dict = {}
    best = (None, 1e9, None)
    for R in np.arange(0.8, 3.01, 0.05):
        d, _ = tree.query(pts, k=1)
        n = int((d <= R * 1000).sum())
        sel[round(float(R), 2)] = n
        if abs(n - target_km2) < best[1]:
            best = (round(float(R), 2), abs(n - target_km2), n)
    return best[0], {"target_km2": target_km2, "chosen_R_km": best[0], "cells": best[2],
                     "scan": {k: v for k, v in list(sel.items())[::4]}}


def main() -> int:
    cfg = load_cfg()
    raw = ROOT / cfg["paths"]["raw"] / "urbanEV"
    processed = ROOT / cfg["paths"]["processed"]
    qa_dir = ROOT / cfg["paths"]["qa"]
    processed.mkdir(parents=True, exist_ok=True)
    qa_dir.mkdir(parents=True, exist_ok=True)

    cell = float(cfg["study_area"]["grid_size_m"])
    R_default = 1.40

    # ---------- 1. 读取静态表 ----------
    st = pd.read_csv(raw / "station_information_raw.csv")
    zi = pd.read_csv(raw / "zone_information.csv")
    st["station_id"] = st["station_id"].astype("int64")
    log(f"[in] 站点 {len(st)} 个，桩数合计 {st.charge_count.sum():,}；分区 {len(zi)} 个")

    # ---------- 2. 人口栅格 ----------
    pop_path = clip_population(cfg)
    with rasterio.open(pop_path) as ds:
        pop = ds.read(1).astype("float32")
        T = ds.transform
        crs_r = ds.crs
        res = abs(T.a)
    log(f"[in] 人口栅格 {pop.shape[1]}x{pop.shape[0]}  res={res}m  CRS={'Albers' if crs_r.is_projected else crs_r}")

    # ---------- 3. 投影 TAZ 质心与站点 ----------
    tr = Transformer.from_crs("EPSG:4326", crs_r, always_xy=True)
    zi["valid"] = (zi.longitude.abs() > 1) & (zi.latitude.abs() > 1)
    zx, zy = tr.transform(zi.loc[zi.valid, "longitude"].to_numpy(),
                          zi.loc[zi.valid, "latitude"].to_numpy())
    taz = gpd.GeoDataFrame(zi.loc[zi.valid].copy(),
                           geometry=gpd.points_from_xy(zx, zy), crs=crs_r)
    sx, sy = tr.transform(st.longitude.to_numpy(), st.latitude.to_numpy())
    st_g = gpd.GeoDataFrame(st.copy(), geometry=gpd.points_from_xy(sx, sy), crs=crs_r)
    log(f"[ok] 投影完成：有效 TAZ {len(taz)} 个（剔除质心缺失 {int((~zi.valid).sum())} 个）")

    # ---------- 4. 区界 ----------
    bnd = gpd.read_file(ROOT / cfg["paths"]["raw"] / "boundary" / "shenzhen_440300_full.json").to_crs(crs_r)
    city = bnd.union_all()

    # ---------- 5. 标定研究区半径 ----------
    # 注意：TAZ 是点几何，其 geometry.area 恒为 0；面积须取自 zone_information 的 area 字段（m²）
    target_km2 = float(taz["area"].sum() / 1e6)
    x0, y0, x1, y1 = city.bounds
    R, cal = calibrate_radius(taz, target_km2, x0, x1, y0, y1, cell)
    log(f"[ok] 半径标定：目标 {target_km2:.1f} km² → R={R} km（单元 {cal['cells']} 个）")

    # ---------- 6. 1 km 格网与人口聚合 ----------
    nx, ny = pop.shape[1], pop.shape[0]
    k = int(round(cell / res))
    if k * res != cell:
        log(f"[warn] 格网 {cell} m 不是像元 {res} m 的整数倍，按 {k} 像元近似")
    nx_c, ny_c = nx // k, ny // k
    block = pop[:ny_c * k, :nx_c * k].reshape(ny_c, k, nx_c, k)
    pop_cell = np.nansum(block, axis=(1, 3))
    has_pop = np.isfinite(block).any(axis=(1, 3))

    jj, ii = np.meshgrid(np.arange(nx_c), np.arange(ny_c))
    cx = T.c + (jj * k + k / 2) * res
    cy = T.f - (ii * k + k / 2) * res
    cells = pd.DataFrame({
        "cell_id": [f"r{r:03d}c{c:03d}" for r, c in zip(ii.ravel(), jj.ravel())],
        "row": ii.ravel(), "col": jj.ravel(),
        "x": cx.ravel(), "y": cy.ravel(),
        "pop": pop_cell.ravel(), "has_data": has_pop.ravel(),
    })
    cells = gpd.GeoDataFrame(cells, geometry=gpd.points_from_xy(cells.x, cells.y), crs=crs_r)

    # ---------- 7. 研究区选择：区界内 ∩ 距 TAZ ≤ R，并填内部孔洞 ----------
    tree = cKDTree(np.c_[taz.geometry.x, taz.geometry.y])
    d_taz, _ = tree.query(np.c_[cells.geometry.x, cells.geometry.y], k=1)
    cells["dist_taz_km"] = d_taz / 1000.0
    inside = cells.within(city)
    cells["in_city"] = inside
    raw_study = inside & (cells.dist_taz_km <= R)

    # 缓冲并集在城区内部会留下空洞（质心分布不均），这些空洞里的人口会被错误排除。
    # 处理：在区界内对研究区掩膜做孔洞填充（只填被完全包围的空洞，不外扩边界）。
    from scipy import ndimage as ndi

    ny_c = int(cells.row.max()) + 1
    nx_c = int(cells.col.max()) + 1
    g_raw = np.zeros((ny_c, nx_c), bool)
    g_raw[cells.row.to_numpy(), cells.col.to_numpy()] = raw_study.to_numpy()
    g_city = np.zeros((ny_c, nx_c), bool)
    g_city[cells.row.to_numpy(), cells.col.to_numpy()] = inside.to_numpy()
    g_fill = ndi.binary_fill_holes(g_raw) & g_city
    filled_extra = int(g_fill.sum() - g_raw.sum())
    cells["in_study"] = g_fill[cells.row.to_numpy(), cells.col.to_numpy()]

    # ---------- 8. 站点落格 ----------
    tree_c = cKDTree(np.c_[cells.geometry.x, cells.geometry.y])
    _, idx = tree_c.query(np.c_[st_g.geometry.x, st_g.geometry.y], k=1)
    st_g["cell_id"] = cells.cell_id.to_numpy()[idx]
    st_g["x"] = st_g.geometry.x
    st_g["y"] = st_g.geometry.y
    st_master = pd.DataFrame({
        "station_id": st_g.station_id, "TAZID": st_g.TAZID,
        "lon": st_g.longitude, "lat": st_g.latitude, "x": st_g.x, "y": st_g.y,
        "slow_count": st_g.slow_count, "fast_count": st_g.fast_count,
        "charge_count": st_g.charge_count, "cell_id": st_g.cell_id,
    })

    # ---------- 9. 汇总与校验 ----------
    study = cells[cells.in_study].copy()
    n_st_in = int(st_master.cell_id.isin(study.cell_id).sum())
    # 站点汇总对全部市域格网计算（2SFCA 的分母需要市域内全部需求单元）
    city_cells = cells[cells.in_city].copy()
    st_sum = (st_master[st_master.cell_id.isin(city_cells.cell_id)]
              .groupby("cell_id").agg(n_stations=("station_id", "size"),
                                      sum_charge=("charge_count", "sum")))
    zone_master = city_cells.drop(columns="geometry").merge(
        st_sum, left_on="cell_id", right_index=True, how="left")
    zone_master[["n_stations", "sum_charge"]] = zone_master[["n_stations", "sum_charge"]].fillna(0)
    zone_master["pop"] = zone_master["pop"].fillna(0)
    zone_master["area_km2"] = (cell / 1000.0) ** 2
    zone_master["in_study"] = zone_master["cell_id"].isin(study.cell_id)

    pop_city = float(cells.loc[cells.in_city, "pop"].sum())
    study_rows = zone_master[zone_master.in_study]
    pop_study = float(study_rows["pop"].sum())
    report = {
        "grid_cells_total": int(len(cells)),
        "cells_in_city": int(cells.in_city.sum()),
        "cells_in_study": int(len(study_rows)),
        "R_km": R,
        "study_cells_added_by_hole_fill": filled_extra,
        "calibration": cal,
        "pop_city_km2_sum": pop_city,
        "pop_study_sum": pop_study,
        "pop_city_share_of_study": None if pop_city == 0 else pop_study / pop_city,
        "stations_total": int(len(st_master)),
        "stations_in_study": n_st_in,
        "piles_total": int(st_master.charge_count.sum()),
        "piles_in_study": int(st_master.loc[st_master.cell_id.isin(study.cell_id), "charge_count"].sum()),
        "cells_with_pop_gt0": int((study_rows["pop"] > 0).sum()),
        "cells_without_pop_data": int((~study_rows["has_data"]).sum()),
        "stations_per_cell_mean": float(study_rows["n_stations"].mean()),
        "cells_without_station": int((study_rows["n_stations"] == 0).sum()),
    }

    st_master.to_parquet(processed / "station_master.parquet", index=False)
    zone_master.to_parquet(processed / "zone_master.parquet", index=False)

    lines = ["# M1 数据基座报告", "",
             f"- 生成：{pd.Timestamp.now().isoformat(timespec='seconds')}",
             f"- 格网：{cell:.0f} m；需求单元 = {report['cells_in_study']} 个（研究区内）",
             "", "## 研究区口径", "",
             f"- 研究区 = 深圳市界内 ∩ 距最近 TAZ 质心 ≤ {R} km 的格网单元",
             f"- 半径按 275 个 TAZ 面积总量（{target_km2:.1f} km²）标定；因数据集**不提供 TAZ 多边形**，此为必要近似",
             f"- 剔除质心缺失的 TAZ：{int((~zi.valid).sum())} 个（TAZID {'、'.join(zi.loc[~zi.valid,'TAZID'].astype(str))}）",
             "", "## 校验", "",
             "| 指标 | 值 |", "|---|---:|"]
    for k2, v2 in report.items():
        if k2 == "calibration":
            continue
        lines.append(f"| {k2} | {v2 if not isinstance(v2, float) else round(v2, 4)} |")
    lines += ["", "## 口径与局限", "",
              "1. 站与桩分别保留（`station_id` / `charge_count`），供给指标取桩数。",
              "2. 人口像元为“人/像元”，NoData 不视为 0；格网人口为 10×10 像元求和。",
              "3. 无 TAZ 多边形，故不输出 TAZ 级人口；全部统计在 1 km 格网尺度完成。",
              "4. 距离为 Albers 等积投影下的平面欧氏距离（米），非路网距离。"]
    (qa_dir / "m1_report.md").write_text("\n".join(lines), encoding="utf-8")

    log("")
    log(f"[out] {processed / 'station_master.parquet'}  {len(st_master)} 行")
    log(f"[out] {processed / 'zone_master.parquet'}  {len(zone_master)} 行")
    log(f"[out] {qa_dir / 'm1_report.md'}")
    log("")
    for k2, v2 in report.items():
        if k2 != "calibration":
            log(f"    {k2} = {v2 if not isinstance(v2, float) else round(v2, 4)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
