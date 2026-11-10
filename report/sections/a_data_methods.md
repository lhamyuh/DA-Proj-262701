# A 交付：数据段、方法段、图注与讲解要点

> 负责人：A（YANG Linyu）｜交付日：2026-11-10（原定 11/15，提前）
> 供 C 直接引用；中英文并列，英文可用于报告与幻灯片。

---

## 1. 数据与研究区（报告 §II 草稿，中文，约 245 字）

本研究使用 UrbanEV 数据集（Li et al., 2025；Dryad, v20260204）的深圳市公共充电站静态属性表，观测期为 2022-09-01 至 2023-02-28，含 1,682 个站点、24,798 个充电桩及 WGS84 坐标。数据集同时提供 275 个交通小区的质心、面积与周长，但不提供任何小区多边形。居住需求取自中国第七次人口普查 100 m 格网人口（Chen et al., 2024），像元值为人/像元，按栅格求和得市域人口 1,744.6 万，与 2020 年七普 1,756 万相差 0.6%。由于缺少小区多边形，需求单元采用 1 km 规则格网；研究区定义为市界内、且距最近小区质心不超过 1.4 km 的格网（半径按 275 个小区面积合计 982.5 km² 标定），共 997 个格网、1,472 万人、1,583 个站点、23,034 个桩。

### English (for report use)

We use the UrbanEV dataset (Li et al., 2025; Dryad, v20260204) for Shenzhen public EV charging, covering 2022-09-01 to 2023-02-28: 1,682 stations and 24,798 piles with WGS84 coordinates. The release provides centroids, areas and perimeters for 275 traffic analysis zones (TAZs) but **no TAZ polygons**. Residential demand is taken from the 100 m gridded 2020 census population (Chen et al., 2024); summing pixels within the city boundary gives 17.45 million, within 0.6% of the official 17.56 million. Because polygons are unavailable, demand units are a 1 km grid. The study area is defined as 1 km cells inside the city boundary and within 1.4 km of a TAZ centroid — the radius is calibrated so that the union area matches the summed TAZ area of 982.5 km² — yielding 997 cells, 14.72 million residents, 1,583 stations and 23,034 piles.

---

## 2. 方法（报告 §III-A，中文，约 240 字）

可达性采用 Gaussian-2SFCA 两步浮动搜索半径法。设供给 S_j 为站点桩数、需求 P_i 为格网人口、d_ij 为 Albers 等积投影下的平面直线距离，g(d) 为截断高斯核（d ≤ d0 归一化至 [0,1]，d > d0 取 0）。第一步求站点供需比 R_j = S_j / Σ_k P_k·g(d_kj)，第二步求格网可达性 A_i = Σ_j R_j·g(d_ij)。主半径为 3 km，另以 1 km 与 5 km 作敏感性对照。分母为零的站点不参与分配，R 不设为无穷。为免边缘站点供需比被系统性放大，分母与分子使用同一市域需求集（2,127 个格网），而非仅研究区内的 997 个。A_i 单位为桩/人，乘 1,000 后表述为每千人桩数，不称"车桩比"。计算以 cKDTree 做半径检索、numpy 向量化求和，三套半径合计约 3 秒。

### English (for report use)

Accessibility is computed with a two-step floating catchment area method using a truncated Gaussian kernel. Supply S_j is the number of piles at station j, demand P_i is grid-cell population, and d_ij is straight-line distance in an Albers equal-area projection. The kernel g(d) decays smoothly and is normalised to [0, 1] within the catchment d0 and zero beyond it. Step 1 computes station-level supply-to-demand ratios R_j = S_j / Σ_k P_k g(d_kj); step 2 sums them to cell accessibility A_i = Σ_j R_j g(d_ij). The main catchment is 3 km, with 1 km and 5 km as sensitivity cases. Stations with zero denominator receive no allocation and their ratios are not set to infinity. To avoid inflating the ratios of peripheral stations, both the numerator and the denominator use the same city-wide demand set (2,127 cells) rather than the 997 study cells alone. A_i is expressed in piles per person and reported as piles per 1,000 persons.

---

## 3. 图注（可直接用）

**Fig 1.** Study area, population and observed public charging supply. (a) 2020 census population on the 100 m grid, clipped to the Shenzhen boundary; (b) 1,682 observed public charging stations, symbol size proportional to the number of piles per station. The dark blue outline marks the study area: 997 1 km cells inside the city boundary and within 1.4 km of a TAZ centroid (997 km²). Albers equal-area projection; station observations cover 2022-09-01 to 2023-02-28. Sources: UrbanEV (Li et al., 2025); 2020 census 100 m grid (Chen et al., 2024).

**Fig 2.** Accessibility and areas without observed coverage at d0 = 3 km. (a) Gaussian-2SFCA accessibility A_i in piles per 1,000 persons; darker cells indicate higher accessibility. (b) Cells with no observed public charging station within 3 km (n = 7 of 997). The lowest-20% accessibility class and the affected-population statistics are produced separately from the frozen results table. Distances are straight-line in the Albers projection, not road-network distances.

---

## 4. 地图讲解要点（幻灯片第 4 页，5 条）

1. **图 1a 的作用是建立分母的合理性**：人口不是均匀铺开的，福田—南山—宝安一线密集，东部坪山、大鹏稀疏；这决定了"人均桩数"的分布不会与"桩的总数"同构。
2. **图 1b 显示供给高度集中在原特区内**：1,682 个站点明显向西南聚集，东部与北部只有零星点位。这一目视结论与后文 Gini 的方向一致，但**不能单独作为证据**，需由 M3/M4 的数字支撑。
3. **深蓝轮廓是研究区，不是行政边界**：它由 274 个小区质心的 1.4 km 缓冲并集得到（并填补内部空洞），面积 997 km²，接近 275 个小区面积合计的 982.5 km²。之所以不能用真实小区边界，是因为数据集不含多边形。
4. **图 2a 的梯度与图 1b 的密度方向相反**：中心区虽然桩多，但人口同样密集、竞争强，人均可达性并非全域最高；边缘格网因人口稀疏反而出现较高的每千人桩数。这说明**"设施密度"与"人均可达性"是两个不同的量**，是本研究的核心论点。
5. **图 2b 的 7 个格网只是"3 km 内无站"**，不等于"荒漠"：荒漠还包括"相对低可达"（可达性最低 20%），后者由 B 的 M3 计算。回答提问时务必区分这两类，不能把 7 个格网说成全部荒漠。

---

## 5. 站点与供给 QA 摘要（完整见 `outputs/qa/a_station_qa.md`）

| 检查 | 结果 | 判定 |
|---|---|---|
| 坐标是否落在市界内 | 1,682 / 1,682（100%） | 通过；若为 GCJ-02 偏移，应有大量点落到市界外或海上 |
| 零坐标 / 缺失坐标 | 0 | 通过 |
| 共址站点（同经纬度多 station_id） | 125 组、264 个站点 | 属同一场站拆分为多条记录，按站计入供给（保守），不作错误处理 |
| `charge_count` 与桩级表一致率 | 92.9% | 不一致者以 `charge_count` 为准；供给不用功率，故不受影响 |
| 功率字段覆盖 | 1,552 / 1,682 站有记录 | 仅作描述，不进入主指标 |

**未做人工目视核对**：本机无 QGIS，改用"市界内比例 + 随机 20 站分区分派 + 与人口栅格的空间一致性"三项量化检查替代；`outputs/qa/station_spotcheck.csv` 可在任意 GIS 中复核。
