#!/usr/bin/env python3
"""06_export_handoff.py — 生成给 B 的交接包（CSV + README + sha256）

约定（计划 §5.5）：一次交接 = 四件东西
  ① 数据文件（CSV，不用 parquet，B 无需 pyarrow） ② README（列名+单位+口径）
  ③ sha256.txt ④ 生成它的脚本（src/02、src/03）
"""
from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "handoff" / f"{date.today():%Y-%m-%d}"
OUT.mkdir(parents=True, exist_ok=True)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    zm = pd.read_parquet(ROOT / "data/processed/zone_master.parquet")
    acc = pd.read_parquet(ROOT / "data/processed/accessibility.parquet")
    sm = pd.read_parquet(ROOT / "data/processed/station_master.parquet")

    zm_f = OUT / "zone_master.csv"
    acc_f = OUT / "accessibility.csv"
    sm_f = OUT / "station_master.csv"
    zm.to_csv(zm_f, index=False, encoding="utf-8-sig")
    acc.to_csv(acc_f, index=False, encoding="utf-8-sig")
    sm.to_csv(sm_f, index=False, encoding="utf-8-sig")

    readme = f"""# 交接包 {OUT.name}（A → B）

生成脚本：`src/02_spatial_population.py`、`src/03_accessibility.py`、`src/06_export_handoff.py`
数据口径见 `outputs/qa/m1_report.md`、`outputs/qa/m2_report.md`。

## zone_master.csv（{len(zm)} 行）
需求单元为 **1 km 规则格网**（数据集不含 TAZ 多边形，故无法做 TAZ 级人口聚合）。

| 列 | 含义 | 单位 |
|---|---|---|
| cell_id | 格网编号 r{{行}}c{{列}} | — |
| row, col | 栅格行列 | — |
| x, y | 格网中心（Albers 等积投影） | m |
| pop | 格网人口（10×10 个 100 m 像元求和） | 人 |
| has_data | 是否有人口栅格数据 | bool |
| dist_taz_km | 到最近 TAZ 质心距离 | km |
| in_city | 是否在市界内 | bool |
| in_study | 是否属研究区（市界内且 dist_taz ≤ 1.4 km） | bool |
| n_stations | 格网内站点数 | 个 |
| sum_charge | 格网内桩数 | 桩 |

## accessibility.csv（{len(acc)} 行 = 2127 格网 × 3 个半径）
| 列 | 含义 | 单位 |
|---|---|---|
| cell_id, d0_m | 格网与搜索半径 | —, m |
| A_i | Gaussian-2SFCA 可达性 | 桩/人 |
| piles_per_1000 | A_i × 1000 | 每千人桩数 |
| n_stations_in_radius | 半径内站点数 | 个 |
| in_study | 是否属研究区 | bool |

**B 只需用 `in_study == True` 的格网做公平性与荒漠统计**；需求定义与阈值见计划 §4.2—§4.4。

## station_master.csv（{len(sm)} 行，供核对，B 一般不需用）
## 未提供的表
- TAZ 级人口：无多边形，不提供。
- 动态占用：范围冻结中已删除。
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    files = [zm_f, acc_f, sm_f, OUT / "README.md"]
    lines = [f"{sha256(p)}  {p.name}" for p in files]
    (OUT / "sha256.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 原始数据台账
    man = ROOT / "metadata/data_manifest.csv"
    rows = [
        dict(url="https://datadryad.org/dataset/doi:10.5061/dryad.np5hqc04z",
             doi="10.5061/dryad.np5hqc04z", version="v20260204",
             downloaded_at="2026-11-10", bytes=(ROOT / "data/raw/doi_10_5061_dryad_np5hqc04z__v20260204.zip").stat().st_size,
             sha256=sha256(ROOT / "data/raw/doi_10_5061_dryad_np5hqc04z__v20260204.zip"),
             license="see Dryad", local_path="data/raw/doi_10_5061_dryad_np5hqc04z__v20260204.zip"),
        dict(url="https://ndownloader.figshare.com/files/43847643",
             doi="10.6084/m9.figshare.24916140.v1", version="2024-08-13",
             downloaded_at="2026-11-10", bytes=(ROOT / "data/raw/PopSE_China2020_100m.rar").stat().st_size,
             sha256=sha256(ROOT / "data/raw/PopSE_China2020_100m.rar"),
             license="see Figshare", local_path="data/raw/PopSE_China2020_100m.rar"),
        dict(url="https://geo.datav.aliyun.com/areas_v3/bound/440300_full.json",
             doi="", version="datav-geoatlas", downloaded_at="2026-11-10",
             bytes=(ROOT / "data/raw/boundary/shenzhen_440300_full.json").stat().st_size,
             sha256=sha256(ROOT / "data/raw/boundary/shenzhen_440300_full.json"),
             license="DataV GeoAtlas（仅作图与掩膜，非权威边界）",
             local_path="data/raw/boundary/shenzhen_440300_full.json"),
    ]
    pd.DataFrame(rows).to_csv(man, index=False, encoding="utf-8")

    print(f"[out] {OUT}")
    for p in files + [OUT / "sha256.txt"]:
        print(f"   {p.name:<20} {p.stat().st_size/1e3:8.1f} KB")
    print(f"[out] {man}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
