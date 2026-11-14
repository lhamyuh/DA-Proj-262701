# 交接包 2026-11-14（B → A 复核 / C 取数）

- 生成：2026-11-14 11:30｜负责人：B（Li Luoyang）
- 出表脚本：`src/04_equity_desert.py`｜一致性断言：`src/07_crosscheck.py`｜稳健性：`src/08_robustness.py`
- 出图脚本：`src/10_fig3.py`
- 输入：`handoff/2026-11-10/accessibility.csv`、`zone_master.csv`
- 口径：`handoff/2026-11-08/kou_jing_card.md` v2

## 1 本包内容

| 文件 | 行数 / 尺寸 | 对应任务 | 状态 |
|---|---|---|---|
| `sensitivity_table.csv` | 5 行 | M5 敏感性 | 交付 |
| `outputs/figures/fig3_lorenz.png` | 3300 × 1560 | Fig3（报告） | 交付 |
| `outputs/figures/slide/fig3_lorenz_slide.jpg` | 3200 × 1513 | Fig3（幻灯片） | 交付 |

表 1 与方法段见 `outputs/tables/table1_main.csv` 与 `report/sections/b_equity_methods.md`；数值冻结见 `numbers_frozen.md`。

## 2 M5 结果

**半径敏感性**（基准 3 km，重合度在受影响并集上计算）

| 对照 | Spearman ρ | 基准并集 | 对照并集 | 重合 | jaccard | 基准保留率 |
|---|---:|---:|---:|---:|---:|---:|
| 1 km | 0.552379 | 190 格 | 229 格 | 97 格 | 0.301242 | 0.510526 |
| 5 km | 0.799248 | 190 格 | 190 格 | 136 格 | 0.557377 | 0.715789 |

**阈值敏感性**（3 km）

| 档位 | 阈值（桩/千人） | 低可达 | 并集占人口 |
|---|---:|---|---:|
| 10% | 0.393940 | 95 格 / 886,042 人 | 6.0192% |
| 20% | 0.688453 | 190 格 / 2,102,601 人 | 14.2838% |
| 30% | 0.925924 | 285 格 / 3,441,326 人 | 23.3783% |

只报这两个维度，不作组合（半径 × 阈值不在计划范围内）。

## 3 Fig3 说明

两面板：(a) 三个半径的洛伦兹曲线，Gini 标在图例；(b) 3 km 下最低 20% 群体与其余 80% 的人均可达性对比（0.52 vs 1.83 桩/千人，3.5 倍）。

- 统计域 951 个有人口格网，人口加权。
- 最低 20% 群体的定义为「按人口升序累计到 20% 止」，边界格按人口比例计入。
- 图注（可直接用）：见 `report/sections/b_equity_methods.md`。

## 4 复现

```powershell
$env:MKL_THREADING_LAYER = "SEQUENTIAL"
python src\04_equity_desert.py     # 三张表
python src\10_fig3.py              # fig3_lorenz.png + slide 版
python src\07_crosscheck.py        # 期望：[PASS] 9 / 9
```

`sensitivity_table.csv` 的哈希见同目录 `sha256.txt`。
