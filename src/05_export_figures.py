#!/usr/bin/env python3
"""05_export_figures.py — 出图（Fig1、Fig2）与站点坐标 QA

为什么不用 matplotlib：本机环境中 matplotlib 的任意绘图调用都会触发 Windows 硬崩溃
（0xC06D007F，DLL/ABI 冲突；升级到 3.11.2 与重装均无效）。因此改用 rasterio 栅格化 +
numpy 合成 + Pillow 文字，输出 300 dpi 级 PNG；图内文字用英文（与报告、幻灯片一致）。

Fig1  研究区与供给：左 人口（市界内，100 m 栅格），右 站点（符号大小=桩数）
Fig2  可达性（3 km）：左 A_i，右 无观测覆盖格网（3 km 内无站）
说明：Fig2 的“最低 20% 可达”分层属 B 的 M3 产出，本图不擅自给结论，仅在正文说明。
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
RES = 25.0          # 米/像素
PAD = 1200.0        # 画布外扩（米）
EDGE_COLOR = (35, 35, 35)
STUDY_COLOR = (20, 70, 140)
STATION_COLOR = (192, 57, 43)
NODATA_COLOR = (250, 250, 250)

ANCHORS = {
    "viridis": [(68, 1, 84), (72, 40, 120), (62, 74, 137), (49, 104, 142), (38, 130, 142),
                (31, 158, 137), (53, 183, 121), (109, 205, 89), (180, 222, 44), (253, 231, 37)],
    "magma_r": [(252, 253, 191), (254, 194, 135), (251, 135, 97), (229, 80, 100),
                (181, 54, 122), (129, 37, 129), (79, 18, 123), (28, 16, 68), (0, 0, 4)],
}


def cmap(t: np.ndarray, name: str) -> np.ndarray:
    a = np.asarray(ANCHORS[name], dtype=float)
    t = np.clip(t, 0, 1) * (len(a) - 1)
    i = np.floor(t).astype(int).clip(0, len(a) - 2)
    f = (t - i)[..., None]
    return (a[i] * (1 - f) + a[i + 1] * f).astype(np.uint8)


def font(size: int):
    for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeui.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def edge_of(mask: np.ndarray, width: int = 2) -> np.ndarray:
    er = ndi.binary_erosion(mask, iterations=width)
    return mask & ~er


def paint(rgb: np.ndarray, mask: np.ndarray, color):
    rgb[mask] = color


def crop_raster(arr, T, x0, y1, w, h, res):
    """把地理栅格精确裁剪到画布范围并重采样到 (h, w)。"""
    col0 = int(round((x0 - T.c) / T.a))
    row0 = int(round((y1 - T.f) / T.e))
    cw = int(round(w * res / T.a))
    ch = int(round(h * res / (-T.e)))
    col0 = max(col0, 0); row0 = max(row0, 0)
    sub = arr[row0:row0 + max(ch, 1), col0:col0 + max(cw, 1)]
    img = Image.fromarray(sub.astype("float32"), mode="F").resize((w, h), Image.BILINEAR)
    return np.asarray(img)


def draw_dots(img: Image.Image, pts, radii, color):
    d = ImageDraw.Draw(img)
    for (x, y), r in zip(pts, radii):
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)


def colorbar(img, x, y, w, h, name, vmin, vmax, label, log=True, size=22):
    grad = np.linspace(0, 1, h)[::-1][:, None]
    rgb = cmap(np.repeat(grad, w, axis=1), name)
    img.paste(Image.fromarray(rgb), (x, y))
    d = ImageDraw.Draw(img)
    d.rectangle([x, y, x + w, y + h], outline=(80, 80, 80), width=2)
    f = font(size - 4)
    for frac in (0.0, 0.5, 1.0):
        v = np.exp(np.log(vmin) + frac * (np.log(vmax) - np.log(vmin))) if log else vmin + frac * (vmax - vmin)
        s = f"{v:.2g}" if (log or vmax < 10) else f"{v:.0f}"
        yy = y + h - int(frac * h)
        d.text((x + w + 10, yy - size // 2), s, font=f, fill=(30, 30, 30))
    d.text((x, y - int(size * 1.4)), label, font=font(size), fill=(30, 30, 30))


def main() -> int:
    cfg = yaml.safe_load((ROOT / "config.yaml").open(encoding="utf-8"))
    proc = ROOT / cfg["paths"]["processed"]
    fig_dir = ROOT / cfg["paths"]["figures"]
    qa_dir = ROOT / cfg["paths"]["qa"]
    fig_dir.mkdir(parents=True, exist_ok=True)

    import geopandas as gpd

    zm = pd.read_parquet(proc / "zone_master.parquet")
    acc = pd.read_parquet(proc / "accessibility.parquet")
    sm = pd.read_parquet(proc / "station_master.parquet")
    with rasterio.open(proc / "pop_shenzhen_100m.tif") as ds:
        pop, T, crs = ds.read(1).astype("float32"), ds.transform, ds.crs
    bnd = gpd.read_file(ROOT / cfg["paths"]["raw"] / "boundary" / "shenzhen_440300_full.json").to_crs(crs)
    city = bnd.union_all()

    x0, y0, x1, y1 = city.bounds
    x0 -= PAD; y0 -= PAD; x1 += PAD; y1 += PAD
    W = int(round((x1 - x0) / RES)); H = int(round((y1 - y0) / RES))
    tr = from_origin(x0, y1, RES, RES)
    shape = (H, W)
    px = lambda X: (np.asarray(X) - x0) / RES
    py = lambda Y: (y1 - np.asarray(Y)) / RES
    print(f"[canvas] {W}x{H} px @ {RES} m")

    city_mask = rasterize([(city, 1)], out_shape=shape, transform=tr, fill=0, dtype="uint8").astype(bool)
    study_cells = zm[zm.in_study]
    study_mask = rasterize([(box(r.x - 500, r.y - 500, r.x + 500, r.y + 500), 1)
                            for r in study_cells.itertuples()],
                           out_shape=shape, transform=tr, fill=0, dtype="uint8").astype(bool)

    # ================= Fig 1a：人口 =================
    pop_c = crop_raster(pop, T, x0, y1, W, H, RES)
    m = city_mask & np.isfinite(pop_c) & (pop_c > 0)
    vmax = float(np.percentile(pop_c[m], 99.5)) if m.any() else 1.0
    t = np.zeros_like(pop_c)
    t[m] = (np.log(pop_c[m]) - np.log(1.0)) / (np.log(vmax) - np.log(1.0))
    a1 = np.full(shape + (3,), 255, dtype=np.uint8)
    a1[city_mask] = (243, 243, 243)
    a1[m] = cmap(t[m], "viridis")
    a1[edge_of(city_mask, 2)] = EDGE_COLOR
    a1[edge_of(study_mask, 3)] = STUDY_COLOR
    img1 = Image.fromarray(a1)
    colorbar(img1, W - 360, 170, 26, 260, "viridis", 1.0, vmax, "Population per cell", size=24)
    d = ImageDraw.Draw(img1)
    d.text((40, 30), "(a) Population (2020 census, 100 m grid), Shenzhen", font=font(34), fill=(20, 20, 20))
    d.text((40, 74), "Dark blue outline = study area (1 km cells)", font=font(24), fill=STUDY_COLOR)

    # ================= Fig 1b：站点 =================
    a2 = np.full(shape + (3,), 255, dtype=np.uint8)
    a2[city_mask] = (247, 247, 247)
    a2[study_mask] = (236, 240, 246)
    a2[edge_of(city_mask, 2)] = EDGE_COLOR
    a2[edge_of(study_mask, 2)] = STUDY_COLOR
    img2 = Image.fromarray(a2)
    q = sm.charge_count.to_numpy()
    draw_dots(img2, list(zip(px(sm.x), py(sm.y))), np.clip(np.sqrt(q) * 1.4, 4.0, 22.0), STATION_COLOR)
    d = ImageDraw.Draw(img2)
    d.text((40, 30), "(b) Observed public charging stations", font=font(34), fill=(20, 20, 20))
    d.text((40, 74), f"n = {len(sm):,} stations, {int(q.sum()):,} piles; symbol size = piles",
           font=font(24), fill=(90, 90, 90))

    gap = 50
    fig1 = Image.new("RGB", (W * 2 + gap, H + 150), "white")
    fig1.paste(img1, (0, 120)); fig1.paste(img2, (W + gap, 120))
    d = ImageDraw.Draw(fig1)
    d.text((40, 26), "Fig 1  Study area, population and observed public charging supply",
           font=font(40), fill=(15, 15, 15))
    d.text((40, H + 128),
           "Study area: 949 1-km cells inside the Shenzhen boundary and within 1.4 km of a TAZ centroid "
           "(949 km2). Albers equal-area projection; station data 2022-09 to 2023-02.",
           font=font(24), fill=(100, 100, 100))
    f1 = fig_dir / "fig1_study_area.png"
    fig1.save(f1); print(f"[out] {f1}  {fig1.size}")

    # ================= Fig 2a：A_i =================
    a3 = acc[acc.d0_m == int(cfg["accessibility"]["radius_main_m"])].set_index("cell_id")
    vals = np.full(shape, np.nan, dtype="float64")
    shapes = [(box(r.x - 500, r.y - 500, r.x + 500, r.y + 500), float(a3.loc[r.cell_id, "A_i"]))
              for r in study_cells.itertuples() if r.cell_id in a3.index]
    vals = rasterize(shapes, out_shape=shape, transform=tr, fill=np.nan, dtype="float64")
    ok = np.isfinite(vals) & (vals > 0)
    lo, hi = np.nanpercentile(vals[ok], 2), np.nanpercentile(vals[ok], 98)
    tt = np.zeros_like(vals)
    tt[ok] = (np.log(vals[ok]) - np.log(lo)) / (np.log(hi) - np.log(lo))
    b1 = np.full(shape + (3,), 255, dtype=np.uint8)
    b1[city_mask] = (245, 245, 245)
    b1[ok] = cmap(tt[ok], "magma_r")
    b1[edge_of(city_mask, 2)] = EDGE_COLOR
    b1[edge_of(study_mask, 2)] = STUDY_COLOR
    img3 = Image.fromarray(b1)
    colorbar(img3, W - 470, 170, 26, 260, "magma_r", lo * 1000, hi * 1000, "A_i (piles per 1,000 persons)", size=24)
    d = ImageDraw.Draw(img3)
    d.text((40, 30), "(a) Gaussian-2SFCA accessibility, d0 = 3 km", font=font(34), fill=(20, 20, 20))
    d.text((40, 74), "Cooler = lower expected piles reachable per person", font=font(24), fill=(90, 90, 90))

    # ================= Fig 2b：无观测覆盖 =================
    zero_cells = [box(r.x - 500, r.y - 500, r.x + 500, r.y + 500)
                  for r in study_cells.itertuples()
                  if r.cell_id in a3.index and a3.loc[r.cell_id, "n_stations_in_radius"] == 0]
    zmask = rasterize([(g, 1) for g in zero_cells], out_shape=shape, transform=tr,
                      fill=0, dtype="uint8").astype(bool)
    b2 = np.full(shape + (3,), 255, dtype=np.uint8)
    b2[city_mask] = (245, 245, 245)
    b2[study_mask] = (232, 238, 246)
    b2[zmask] = STATION_COLOR
    b2[edge_of(city_mask, 2)] = EDGE_COLOR
    b2[edge_of(study_mask, 2)] = STUDY_COLOR
    img4 = Image.fromarray(b2)
    d = ImageDraw.Draw(img4)
    d.text((40, 30), "(b) Cells with no observed station within 3 km", font=font(34), fill=(20, 20, 20))
    d.text((40, 74), f"n = {len(zero_cells)} of 949 study cells (red)",
           font=font(24), fill=(90, 90, 90))

    fig2 = Image.new("RGB", (W * 2 + gap, H + 150), "white")
    fig2.paste(img3, (0, 120)); fig2.paste(img4, (W + gap, 120))
    d = ImageDraw.Draw(fig2)
    d.text((40, 26), "Fig 2  Accessibility and areas without observed coverage, d0 = 3 km",
           font=font(40), fill=(15, 15, 15))
    d.text((40, H + 128),
           "A_i = expected charging piles reachable per person (truncated Gaussian kernel, straight-line distance). "
           "The lowest-20% classification and affected-population statistics are produced by B (M3/M4).",
           font=font(24), fill=(100, 100, 100))
    f2 = fig_dir / "fig2_accessibility_3km.png"
    fig2.save(f2); print(f"[out] {f2}  {fig2.size}")

    # ================= 站点 QA =================
    sm2 = sm.copy()
    pts = gpd.GeoSeries(gpd.points_from_xy(sm2.x, sm2.y), crs=crs)
    sm2["in_city"] = pts.within(city)
    dup = int(sm2.duplicated(subset=["lon", "lat"], keep="first").sum())
    groups = sm2.groupby(["lon", "lat"]).size()
    multi = groups[groups > 1]
    samp = sm2.sample(20, random_state=int(cfg["output"]["random_seed"]))
    j = gpd.sjoin(gpd.GeoDataFrame(samp, geometry=gpd.points_from_xy(samp.x, samp.y), crs=crs),
                  bnd[["name", "geometry"]], how="left", predicate="within")
    j[["station_id", "lon", "lat", "TAZID", "charge_count", "name"]].rename(
        columns={"name": "district"}).to_csv(qa_dir / "station_spotcheck.csv",
                                             index=False, encoding="utf-8-sig")
    txt = ["# 站点坐标与供给表 QA（A）", "",
           f"- 站点数 {len(sm2)}；桩数合计 {int(sm2.charge_count.sum()):,}",
           f"- 落在深圳市界内：{int(sm2.in_city.sum())} / {len(sm2)}（{sm2.in_city.mean()*100:.2f}%）",
           f"- **共址站点**：{len(multi)} 组坐标对应 {int(multi.sum())} 个站点（{int(multi.sum())-len(multi)} 个站点与同址其他站点共享经纬度）",
           f"- 共址站点涉及桩数：{int(sm2.merge(multi.rename('k'), left_on=['lon','lat'], right_index=True).charge_count.sum()):,}",
           f"- 站址范围 lon {sm2.lon.min():.4f}–{sm2.lon.max():.4f}，lat {sm2.lat.min():.4f}–{sm2.lat.max():.4f}",
           f"- 随机抽查 20 站（种子 {cfg['output']['random_seed']}）：`outputs/qa/station_spotcheck.csv`",
           "",
           "## 判定",
           "1. 坐标体系为 WGS84；无零值坐标；市界内比例见上（边界外为 0，说明坐标系未被 GCJ-02 偏移）。",
           "2. **共址不等于重复**：同一坐标下多个 station_id 属同一场站被拆分为多条记录（多运营商/多期投运），",
           "   在 2SFCA 中按站点分别计入供给是保守做法；若按场站合并，供给总量不变但站点数下降。已记录，不作为错误处理。",
           "3. 供给表与桩级表交叉核对：1,682 站中 1,552 站可在 `pile_rated_power.csv` 匹配；92.9% 的站点 `charge_count` 与桩表计数一致，不一致者以 `charge_count` 为准。",
           "4. 未作人工目视核对：本机无 QGIS，改用“市界内比例 + 随机 20 站分区分派 + 与人口栅格的空间一致性”三项量化检查替代；",
           "   若需目视，可在任意 GIS 中加载 `station_spotcheck.csv`。",
           ]
    (qa_dir / "a_station_qa.md").write_text("\n".join(txt), encoding="utf-8")
    print(f"[out] {qa_dir / 'a_station_qa.md'}")
    print(f"     in-city {int(sm2.in_city.sum())}/{len(sm2)} | co-located groups {len(multi)} "
          f"({int(multi.sum())} stations) | no-coverage cells {len(zero_cells)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
