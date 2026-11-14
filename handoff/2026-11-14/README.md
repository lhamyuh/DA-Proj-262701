# 交付总包 2026-11-14（B → A / C）

- 负责人：B（Li Luoyang）｜生成：2026-11-14
- 内容：截至今日 B 的全部交付物，按**表格 / 图 / 文档**三类归档
- 口径：`handoff/2026-11-08/kou_jing_card.md` v2
- **本目录是只读快照**，不是第二份可编辑副本。改数请改源头再重跑（见 §3）

## 1 分类索引

| 类别 | 文件 | 内容 | 对应任务 | 状态 |
|---|---|---|---|---|
| 表格 | `tables/desert_table.csv` | 9 行 = 3 半径 × 3 阈值 | M3 荒漠识别 | 已交付（11/12） |
| 表格 | `tables/equity_table.csv` | 3 行 = 三个半径 | M4 公平性 | 已交付（11/12） |
| 表格 | `tables/sensitivity_table.csv` | 5 行 = 半径 2 + 阈值 3 | M5 敏感性 | 已交付（11/14） |
| 表格 | `tables/table1_main.csv` | 表 1，14 行 × 三半径 | 表 1 | 已交付 |
| 图 | `figures/fig3_lorenz.png` | Fig3 报告版 3300 × 1560 | M4 / M5 | 已交付（11/14） |
| 图 | `figures/fig3_lorenz_slide.jpg` | Fig3 幻灯片版 3200 × 1513 | 幻灯片第 5 页 | 已交付（11/14） |
| 文档 | `docs/numbers_frozen.md` | 数值冻结，含禁用数表 | G2（11/16） | **草案，11/16 冻结** |
| 文档 | `docs/b_equity_methods.md` | 方法段中英 + 表注 + 统计要点 5 条 + 口径声明 3 条 | 11/15 | 已交付 |
| 文档 | `docs/number_card.md` | 给 C 的一页数值卡 | 幻灯片第 5–6 页 | 已交付 |

## 2 三类怎么用

**表格（`tables/`）**——A 复核与 C 取数都用这四个。`desert_table` 与 `equity_table` 是 11/12 交付的正式版（严格小于判据），`sensitivity_table` 是 M5，`table1_main` 是幻灯片与报告的主表。列定义见 `handoff/2026-11-12/README.md` §6。

**图（`figures/`）**——`fig3_lorenz.png` 用于报告（300 dpi），`fig3_lorenz_slide.jpg` 用于幻灯片（3200 宽）。两版是同一张图的不同分辨率，不是两个设计。

**文档（`docs/`）**——`number_card.md` 直接给 C；`b_equity_methods.md` 给 C 写报告与讲稿；`numbers_frozen.md` 是 G2 之后全组唯一的数值来源，**11/16 20:00 之前是草案**。

## 3 三条使用规则

1. **不要在本目录改任何数字。** 本目录的 `sha256.txt` 会在源头重跑后失效——这正是设计目的：它一旦对不上，说明该重新打包了。
2. **权威版本在源头**：`outputs/tables/*.csv`、`outputs/figures/*`、`numbers_frozen.md`、`report/sections/b_equity_methods.md`。改数改那里。
3. **刷新本目录**：源头变了就重跑 `04 → 09 → 11`（见 §4），本目录会整体重建。

## 4 复现与刷新

```powershell
$env:MKL_THREADING_LAYER = "SEQUENTIAL"
python src\04_equity_desert.py     # 三张表
python src\10_fig3.py              # Fig3 两版
python src\09_freeze.py            # 表 1、numbers_frozen、数值卡
python src\11_package.py           # 汇总到本目录并重算 sha256
python src\07_crosscheck.py        # 期望：[PASS] 9 / 9
python src\08_robustness.py        # 期望：三个假设的最坏扰动都没有改变量级与方向
```

## 5 与 11/12 包的关系

`handoff/2026-11-12/` 保留为 11/12 那次交付的历史记录（含口径说明、列定义与四处旧数修正）。本目录是它的超集并按类别重组；两者内容冲突时，以本目录为准，因为它是 11/14 重新打包的。

## 6 需要对方做的事

- **A**：复核 `tables/` 四张表；并修正 `handoff/2026-11-12/README.md` §7 列的四处旧数（g1 的 949、图内的 949、908、200 格）。
- **C**：按 `docs/number_card.md` 填第 5–6 页；数值只从 `docs/numbers_frozen.md` 取。
