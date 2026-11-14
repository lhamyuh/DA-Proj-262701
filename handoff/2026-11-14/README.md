# 交接包 2026-11-14（A → B）

生成脚本：`src/02_spatial_population.py`、`src/03_accessibility.py`、`src/06_export_handoff.py`
数据口径见 `outputs/qa/m1_report.md`、`outputs/qa/m2_report.md`。

## zone_master.csv（2127 行）
需求单元为 **1 km 规则格网**（数据集不含 TAZ 多边形，故无法做 TAZ 级人口聚合）。

| 列 | 含义 | 单位 |
|---|---|---|
| cell_id | 格网编号 r{行}c{列} | — |
| row, col | 栅格行列 | — |
| x, y | 格网中心（Albers 等积投影） | m |
| pop | 格网人口（10×10 个 100 m 像元求和） | 人 |
| has_data | 是否有人口栅格数据 | bool |
| dist_taz_km | 到最近 TAZ 质心距离 | km |
| in_city | 是否在市界内 | bool |
| in_study | 是否属研究区（市界内且 dist_taz ≤ 1.4 km） | bool |
| n_stations | 格网内站点数 | 个 |
| sum_charge | 格网内桩数 | 桩 |

## accessibility.csv（6381 行 = 2127 格网 × 3 个半径）
| 列 | 含义 | 单位 |
|---|---|---|
| cell_id, d0_m | 格网与搜索半径 | —, m |
| A_i | Gaussian-2SFCA 可达性 | 桩/人 |
| piles_per_1000 | A_i × 1000 | 每千人桩数 |
| n_stations_in_radius | 半径内站点数 | 个 |
| in_study | 是否属研究区 | bool |

**B 只需用 `in_study == True` 的格网做公平性与荒漠统计**；需求定义与阈值见计划 §4.2—§4.4。

## station_master.csv（1682 行，供核对，B 一般不需用）
## 未提供的表
- TAZ 级人口：无多边形，不提供。
- 动态占用：范围冻结中已删除。

---

## 给 B 的字段口径答复

| 要求 | 对应列 | 说明 |
|---|---|---|
| `d0` | `d0_m` | 1000 / 3000 / 5000（米）；主半径 3000 |
| 站覆盖标记 | `n_stations_in_radius` | 该格网在 `d0_m` 内可达的站点数；**`== 0` 即"无观测覆盖"** |
| 边界标记 | `in_study` | 研究区（市界内且距 TAZ 质心 ≤1.4 km，含内部孔洞填补） |

三条补充：

1. **不要用 `n_stations`（格网内站点数）判断覆盖**——它只数落在同一格网内的站，会严重高估荒漠。覆盖一律用 `n_stations_in_radius`。
2. **需求集是 2127 行、统计只用 949/997 行**：2SFCA 的分母必须包含半径内的全部人口；若只把研究区格网当需求，区外站点的供需比会被系统性放大。
3. **`pop == 0` 的格网**：研究区 997 个格网中 `pop > 0` 的有 **951** 个、`pop == 0` 的 **46** 个；后者不计入人口加权 Gini 与 Lorenz。
