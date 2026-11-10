# 交接包 2026-11-10（A → B）

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

## 给 B 的字段口径答复（回应 log 11/06 的接口请求）

B 在 `log.md` 中要求确认 `accessibility` 的三项口径，逐条答复如下：

| B 的要求 | 本交接包中的对应列 | 说明 |
|---|---|---|
| `d0` | `d0_m` | 取值 1000 / 3000 / 5000（米）；主半径 3000 |
| 站覆盖标记 | `n_stations_in_radius` | 该格网在 `d0_m` 内可达的站点数；**`n_stations_in_radius == 0` 即"无观测覆盖"**，可直接用于 M3 的第一类荒漠 |
| 边界标记 | `in_study` | 研究区（市界内且距 TAZ 质心 ≤1.4 km）。**所有公平性统计只取 `in_study == True`** |

补充三条：

1. **不要用 `n_stations`（格网内站点数）判断覆盖**——它只数落在同一格网内的站，会严重高估荒漠。覆盖一律用 `n_stations_in_radius`。
2. **需求集为什么是 2127 行而不是 949 行**：2SFCA 的分母必须包含半径内的全部人口。若只把研究区 949 个格网当需求，区外站点的供需比会被系统性放大（初版即因此出现 A_i 在 3→5 km 跳变 8 倍的错误）。计算用 2127，**统计用 949**。
3. **`pop == 0` 的格网**：人口为零处 A_i 仍可计算，但**不计入人口加权 Gini 与 Lorenz**（计划 §4.3）。研究区内 `pop > 0` 的格网为 908 个。

B 提到的"数字开头模块名无法 import"属实，`04_equity_desert.py` 采用 `src/equity_desert.py` 承载函数、`04_*.py` 只做入口的做法，与 A 的 `src/02/03` 结构一致，无需改动。

