# M1 数据基座报告

- 生成：2026-11-10T20:09:34
- 格网：1000 m；需求单元 = 949 个（研究区内）

## 研究区口径

- 研究区 = 深圳市界内 ∩ 距最近 TAZ 质心 ≤ 1.4 km 的格网单元
- 半径按 275 个 TAZ 面积总量（982.5 km²）标定；因数据集**不提供 TAZ 多边形**，此为必要近似
- 剔除质心缺失的 TAZ：1 个（TAZID 348）

## 校验

| 指标 | 值 |
|---|---:|
| grid_cells_total | 6370 |
| cells_in_city | 2127 |
| cells_in_study | 949 |
| R_km | 1.4 |
| pop_city_km2_sum | 17446224.0 |
| pop_study_sum | 14504046.0 |
| pop_city_share_of_study | 0.8314 |
| stations_total | 1682 |
| stations_in_study | 1562 |
| piles_total | 24798 |
| piles_in_study | 22818 |
| cells_with_pop_gt0 | 908 |
| cells_without_pop_data | 0 |
| stations_per_cell_mean | 1.6459 |
| cells_without_station | 499 |

## 口径与局限

1. 站与桩分别保留（`station_id` / `charge_count`），供给指标取桩数。
2. 人口像元为“人/像元”，NoData 不视为 0；格网人口为 10×10 像元求和。
3. 无 TAZ 多边形，故不输出 TAZ 级人口；全部统计在 1 km 格网尺度完成。
4. 距离为 Albers 等积投影下的平面欧氏距离（米），非路网距离。