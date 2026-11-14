# B 交付：荒漠与公平性方法段、表 1 说明与统计要点

> 负责人：B（Li Luoyang）｜交付日：2026-11-14（原定 11/15，提前一天）
> 供 C 直接引用；中英并列，英文用于报告与幻灯片。
> 文中所有数字出自 `numbers_frozen.md`，不得在本文件内另行计算。

---

## 1 荒漠与公平性方法（报告 §III-B 草稿，中文，约 290 字）

荒漠识别以人口大于零的 951 个 1 km 格网为统计域，按两类定义判定。无观测覆盖指格网在基准半径 3 km 内没有任何观测公共站点，其可达性必为零；相对低可达指可达性严格低于研究区分布的 20% 分位，阈值取线性插值。采用严格小于而非含等号，是因为均匀供给下含等号会把全部单元判为荒漠。受影响人口为两类区域的并集，按格网去重，两类各自的格网数与人口同时报告。公平性采用人口加权口径：加权均值为 ΣP_i a_i / ΣP_i，Gini 系数取加权洛伦兹曲线与对角线之间面积的二倍，另报告最低 20% 群体的加权均值、其占全体的比例与 P10。人口为零的 46 个格网剔出全部加权统计并单独计数。敏感性只作两个维度：服务半径 3 km 对 1 km 与 5 km，重合度按受影响并集计算；低可达阈值 20% 对 10% 与 30%。

### English (for report use)

The desert analysis is conducted on the 951 populated 1 km cells. A cell is classified as having **no observed coverage** if no public station lies within the 3 km catchment, which necessarily implies zero accessibility. A cell is **relatively low-access** if its accessibility falls strictly below the 20th percentile of the study-area distribution, with the threshold taken by linear interpolation; strict inequality is used because an inclusive rule would flag every cell under uniform supply. Affected population is the de-duplicated union of the two classes, with each class reported separately in cells and residents. Equity metrics are population-weighted: the weighted mean is ΣP_i a_i / ΣP_i, the Gini coefficient is twice the area between the weighted Lorenz curve and the diagonal, and the bottom-20% group's weighted mean, its ratio to the overall mean, and P10 are reported alongside. The 46 zero-population cells are excluded from all weighted statistics and counted separately. Sensitivity is restricted to two dimensions: the catchment radius (3 km against 1 and 5 km), with overlap measured on the affected union, and the low-access threshold (20% against 10% and 30%).

---

## 2 表 1 说明（可直接作表注）

**Table 1.** Desert extent and population-weighted accessibility by catchment radius (Shenzhen, 2020 census population; station supply 2022–09 to 2023–02). Population-weighted statistics use the 951 of 997 study cells with population > 0; the 46 zero-population cells are counted but excluded from weighted statistics. Low-access cells fall strictly below the 20th percentile of the accessibility distribution. Affected population is the de-duplicated union of the two desert classes. Distances are straight-line in an Albers equal-area projection, not road-network distances.

**表 1.** 三个服务半径下的荒漠范围与人口加权可达性。加权统计使用研究区 997 个格网中人口大于零的 951 个；人口为零的 46 个格网仅计数、不进入加权统计。相对低可达指严格低于可达性分布 20% 分位的格网。受影响人口为两类荒漠区域的并集（已去重）。距离为 Albers 等积投影下的平面直线距离，非路网距离。

---

## 3 统计说明要点（幻灯片第 5–6 页，5 条，可直接念）

1. **两类荒漠不是相加关系。** 3 km 下「半径内一个站都没有」只有 6 格 / 1.19 万人，而且它们必然落在低可达里；所以受影响人口是 190 格 / 210.3 万，不是 6 + 190。
2. **Gini 0.294 说的是分布形状，不是「29.4% 的人没桩」。** 它的意思是：如果可达性完全平均分配，洛伦兹曲线会是对角线；现在的曲线与对角线之间的面积，是 Gini 的一半。
3. **最低 20% 的居民只拿到全体的三分之一。** 人均 0.52 桩/千人，全体 1.57，差 3.5 倍；他们占人口的 20%，只占可达性总量的 6.6%。
4. **半径越小，看起来越不公平——但这是定义的一部分。** 1 km 半径下有 24% 的格网半径内根本没有站，可达性为零；Gini 因此升到 0.576。换半径改变的是「什么叫够得着」，不改变「哪里的人被落下」。
5. **稳健性。** 半径 1 km 与 3 km 的秩相关 0.552、并集重合度 0.301；5 km 是 0.799 与 0.557。阈值从 10% 挪到 30%，受影响人口从 6.02% 到 23.38%——方向与排序都不变。

---

## 4 三条口径声明（局限页与问答用）

1. **1 km 结果对站点坐标敏感。** 把所有站点整体平移 500 m，1 km 的 Gini 从 0.576 升到 0.605，零覆盖格网从 229 增到 238；3 km 的 Gini 从 0.294 到 0.313。方向不变，但 1 km 那一组不宜当作硬结论引用。
2. **并集在阈值大于零时恒等于低可达类。** 因为无覆盖必使可达性为零，零值必低于任何正阈值。两类的区分意义在政策含义而非数量：绝对缺失需要建站，相对剥夺需要调配。
3. **研究区是近似。** 数据集无 TAZ 多边形，研究区由质心 1.4 km 缓冲并集加内部孔洞填充得到（997 格 / 997 km²），对标的 275 个小区面积合计 982.5 km²，偏 +1.5%。剔除孔洞填充的 48 格重算，Gini 由 0.2936 变为 0.2937，结论不变。

---

## 5 与 A 的交付对齐

| 项目 | A 的口径 | 本文件口径 | 是否一致 |
|---|---|---|---|
| 研究区 | 997 格 / 1,472 万 / 84.4% | 同 | 一致 |
| 供给 | 桩数（`charge_count`），1,583 站 / 23,034 桩 | 同 | 一致 |
| 距离 | Albers 平面直线距离 | 同 | 一致 |
| 人口 | 七普 2020，100 m 格网，「人/像元」 | 同 | 一致 |
| 可达性单位 | 桩/人，对外报每千人桩数 | 同 | 一致 |
| 未观测区域 | 不赋零供给 | 同（`in_study` 之外不进入统计） | 一致 |
