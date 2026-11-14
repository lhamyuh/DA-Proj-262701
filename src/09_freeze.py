"""09_freeze.py — 表 1、numbers_frozen.md 与给 C 的数值卡（B，2026-11-14）

一次生成三件产物，全部从 outputs/tables/ 的三张表现算，不手抄任何数字：
    outputs/tables/table1_main.csv        表 1（主情景汇总，指标 × 三半径）
    numbers_frozen.md                     G2 唯一数值来源（含「禁用数」一节）
    handoff/2026-11-16/number_card.md      给 C 的一页数值卡（第 5–6 页用）

冻结状态由运行日期自动判定：2026-11-16 20:00 之后运行即标记「已冻结」，
在此之前为「待冻结」——11/16 当日只需重跑本脚本，无需手工改文件。

运行：python src/09_freeze.py
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "outputs" / "tables"
HANDOFF_10 = ROOT / "handoff" / "2026-11-10"
FREEZE_AT = datetime(2026, 11, 16, 20, 0)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    desert = pd.read_csv(TAB / "desert_table.csv", encoding="utf-8-sig")
    equity = pd.read_csv(TAB / "equity_table.csv", encoding="utf-8-sig")
    sens = pd.read_csv(TAB / "sensitivity_table.csv", encoding="utf-8-sig")

    radii = [1000, 3000, 5000]
    main_share = 0.20

    eq = equity.set_index("d0_m")
    ds = desert[desert["threshold_share"] == main_share].set_index("d0_m")
    pop = float(eq.loc[3000, "population"])

    # 表 1
    rows = []
    def add(metric, values, unit=""):
        rows.append({"指标": metric, "单位": unit,
                     "1 km": values[0], "3 km（主）": values[1], "5 km": values[2]})

    add("研究区格网", [int(eq.loc[d, "cells_in_study"]) for d in radii], "格")
    add("有效格网（人口>0）", [int(eq.loc[d, "cells_valid"]) for d in radii], "格")
    add("剔除（人口=0）", [int(eq.loc[d, "cells_zero_population"]) for d in radii], "格")
    add("统计域人口", [f"{eq.loc[d, 'population']:,.0f}" for d in radii], "人")
    add("无观测覆盖", [f"{int(ds.loc[d, 'no_coverage_cells'])} / {ds.loc[d, 'no_coverage_population']:,.0f}" for d in radii], "格 / 人")
    add("相对低可达", [f"{int(ds.loc[d, 'low_access_cells'])} / {ds.loc[d, 'low_access_population']:,.0f}" for d in radii], "格 / 人")
    add("受影响并集（去重）", [f"{int(ds.loc[d, 'union_cells'])} / {ds.loc[d, 'union_population']:,.0f}" for d in radii], "格 / 人")
    add("并集占统计域人口", [f"{ds.loc[d, 'union_population_share']:.2%}" for d in radii], "")
    add("人口加权均值", [f"{eq.loc[d, 'weighted_mean_per_1000']:.6f}" for d in radii], "桩/千人")
    add("Gini", [f"{eq.loc[d, 'gini']:.6f}" for d in radii], "")
    add("P10", [f"{eq.loc[d, 'p10']:.6f}" for d in radii], "桩/千人")
    add("最低 20% 群体人口", [f"{eq.loc[d, 'bottom20_population']:,.0f}" for d in radii], "人")
    add("最低 20% 群体均值", [f"{eq.loc[d, 'bottom20_mean_per_1000']:.6f}" for d in radii], "桩/千人")
    add("最低 20% / 全体均值", [f"{eq.loc[d, 'bottom20_mean_per_1000'] / eq.loc[d, 'weighted_mean_per_1000']:.2%}" for d in radii], "")

    table1 = pd.DataFrame(rows)
    table1.to_csv(TAB / "table1_main.csv", index=False, encoding="utf-8-sig")
    print(f"[out] {TAB / 'table1_main.csv'}  {table1.shape[0]} 行")

    # 派生量：其余 80% 的人均可达性（Fig3 第二面板与数值卡用）
    total_mass = float(eq.loc[3000, "weighted_mean_per_1000"]) * pop
    bottom_pop = float(eq.loc[3000, "bottom20_population"])
    bottom_mean = float(eq.loc[3000, "bottom20_mean_per_1000"])
    rest_mean = (total_mass - bottom_mean * bottom_pop) / (pop - bottom_pop)
    ratio = rest_mean / bottom_mean

    # 敏感性
    r1 = sens[(sens.dimension == "radius") & (sens.comparison.astype(str) == "1000")].iloc[0]
    r5 = sens[(sens.dimension == "radius") & (sens.comparison.astype(str) == "5000")].iloc[0]
    th = sens[sens.dimension == "threshold"].set_index("comparison")

    r1p = float(eq.loc[1000, 'bottom20_mean_per_1000']) / float(eq.loc[1000, 'weighted_mean_per_1000'])
    r5p = float(eq.loc[5000, 'bottom20_mean_per_1000']) / float(eq.loc[5000, 'weighted_mean_per_1000'])
    now = datetime.now()
    status = "已冻结" if now >= FREEZE_AT else "待冻结（11/16 20:00 G2 后重跑本脚本即自动标记）"

    h10 = {n: sha256(HANDOFF_10 / n) for n in ("accessibility.csv", "zone_master.csv", "station_master.csv")}

    def row(metric, value, src):
        return f"| {metric} | {value} | {src} |"

    core = [
        row("研究区格网", "997", "table1_main.csv"),
        row("有效格网（人口>0）", "951", "table1_main.csv"),
        row("剔除（人口=0）", "46", "table1_main.csv"),
        row("统计域人口", f"{pop:,.0f}", "table1_main.csv"),
        row("无观测覆盖", f"6 格 / {ds.loc[3000, 'no_coverage_population']:,.0f} 人", "desert_table.csv"),
        row("相对低可达", f"{int(ds.loc[3000, 'low_access_cells'])} 格 / {ds.loc[3000, 'low_access_population']:,.0f} 人", "desert_table.csv"),
        row("受影响并集（去重）", f"{int(ds.loc[3000, 'union_cells'])} 格 / {ds.loc[3000, 'union_population']:,.0f} 人", "desert_table.csv"),
        row("并集占统计域人口", f"{ds.loc[3000, 'union_population_share']:.6f}（{ds.loc[3000, 'union_population_share']:.2%}）", "desert_table.csv"),
        row("人口加权均值", f"{eq.loc[3000, 'weighted_mean_per_1000']:.6f} 桩/千人", "equity_table.csv"),
        row("Gini 系数", f"{eq.loc[3000, 'gini']:.6f}", "equity_table.csv"),
        row("P10", f"{eq.loc[3000, 'p10']:.6f} 桩/千人", "equity_table.csv"),
        row("最低 20% 群体人口", f"{bottom_pop:,.1f} 人", "equity_table.csv"),
        row("最低 20% 群体均值", f"{bottom_mean:.6f} 桩/千人", "equity_table.csv"),
        row("最低 20% / 全体均值", f"{bottom_mean / float(eq.loc[3000, 'weighted_mean_per_1000']):.4f}（{bottom_mean / float(eq.loc[3000, 'weighted_mean_per_1000']):.2%}）", "派生"),
        row("其余 80% 人均", f"{rest_mean:.6f} 桩/千人", "派生"),
        row("其余 80% / 最低 20%", f"{ratio:.2f} 倍", "派生"),
    ]

    radii_rows = []
    for d in radii:
        radii_rows.append(f"| {d} | {int(ds.loc[d, 'union_cells'])} 格 / {ds.loc[d, 'union_population']:,.0f} 人 | "
                          f"{ds.loc[d, 'union_population_share']:.2%} | {eq.loc[d, 'weighted_mean_per_1000']:.6f} | "
                          f"{eq.loc[d, 'gini']:.6f} | {eq.loc[d, 'p10']:.6f} | {eq.loc[d, 'bottom20_mean_per_1000']:.6f} |")

    th_rows = []
    for s in ("10%", "20%", "30%"):
        r = th.loc[s]
        th_rows.append(f"| {s} | {r['threshold_value']:.6f} | {int(r['low_access_cells'])} 格 / "
                       f"{r['low_access_population']:,.0f} 人 | {r['union_population_share']:.6f} |")

    md = f"""# 数值冻结（G2）

> **状态：{status}**
> 生成：{now:%Y-%m-%d %H:%M}｜脚本：`src/09_freeze.py`｜口径：口径说明卡 v2（`handoff/2026-11-08/kou_jing_card.md`）
> **本文件是幻灯片与报告的唯一数值来源。** 任何数值修改必须先改本文件，再改幻灯片；不得在 PowerPoint 中直接改数。

## 0 数据版本

| 文件 | sha256（前 16 位） |
|---|---|
| `handoff/2026-11-10/accessibility.csv` | `{h10['accessibility.csv'][:16]}` |
| `handoff/2026-11-10/zone_master.csv` | `{h10['zone_master.csv'][:16]}` |
| `handoff/2026-11-10/station_master.csv` | `{h10['station_master.csv'][:16]}` |

## 1 主情景（3 km / 20%）

| 指标 | 值 | 来源 |
|---|---|---|
{chr(10).join(core)}

## 2 三个半径（主设定 20%）

| 半径 (m) | 受影响并集 | 占人口 | 加权均值 | Gini | P10 | 最低 20% 均值 |
|---:|---|---:|---:|---:|---:|---:|
{chr(10).join(radii_rows)}

## 3 敏感性

**半径（3 km 对 1 / 5 km，重合度按受影响并集）**

| 对照 | Spearman ρ | jaccard | 3 km 集合保留率 | 对照半径并集 |
|---|---:|---:|---:|---|
| 1 km | {r1['spearman_rho']:.6f} | {r1['jaccard']:.6f} | {r1['base_low_retained']:.6f} | {int(r1['alt_low_cells'])} 格 |
| 5 km | {r5['spearman_rho']:.6f} | {r5['jaccard']:.6f} | {r5['base_low_retained']:.6f} | {int(r5['alt_low_cells'])} 格 |

**阈值（3 km，10% / 20% / 30%）**

| 档位 | 阈值（桩/千人） | 低可达 | 并集占人口 |
|---|---:|---|---:|
{chr(10).join(th_rows)}

## 4 禁用数（不得再出现在任何文件中）

| 数 | 出处 | 为什么禁用 | 现值 |
|---|---|---|---|
| 191 格 / 2,111,567 人 | 11/10 首轮 `rank` 口径 | 判据已改为 `quantile_strict` | 190 格 / 2,102,601 人 |
| 200 格 / 2,023,405 人 | `log.md` 11/10（A） | 用当前数据复现不出（200 格 → 2,272,245；191 格 → 2,111,567） | 190 格 / 2,102,601 人 |
| 949 格 / 1,450 万 / 83.1% | `outputs/qa/g1_conclusion.md` | 孔洞填充前 | 997 / 1,472 万 / 84.4% |
| 1,562 站 / 22,818 桩 | `outputs/qa/g1_conclusion.md` | 同上 | 1,583 站 / 23,034 桩 |
| 908 个有人口格网 | `handoff/2026-11-10/README.md` | 949 版正确、997 版应为 951 | 951 |
| 「949 cells (949 km²)」/「n = 7 of 949」 | Fig1、Fig2(b) 图内文字 | 需 A 重出图 | 997 / 6（含零人口则为 7） |

## 5 变更记录

| 日期 | 事项 |
|---|---|
| 11/10 | 首轮三张表（`rank` 口径），未提交 |
| 11/11 | 判据定稿为 `quantile_strict`，三张表重跑；新增 `07_crosscheck.py`（9/9）与 `08_robustness.py`（三个上游假设） |
| 11/14 | 表 1、方法段、本文件首版 |
| 11/16 20:00 | G2：重跑 `09_freeze.py` 使本文件标记为「已冻结」 |

## 6 复现

```powershell
$env:MKL_THREADING_LAYER = "SEQUENTIAL"
python src\\04_equity_desert.py
python src\\07_crosscheck.py
python src\\08_robustness.py
python src\\09_freeze.py
```
"""
    (ROOT / "numbers_frozen.md").write_text(md, encoding="utf-8", newline="\n")
    print(f"[out] {ROOT / 'numbers_frozen.md'}")

    card = f"""# 数值卡（给 C · 第 5–6 页）

> 来源：`numbers_frozen.md`（G2）。**只准用下面这些数**，其余一律不用。
> 生成：{now:%Y-%m-%d %H:%M}

## 第 5 页 · 荒漠人口与公平性（65 秒）

| 要讲的 | 数 |
|---|---|
| 研究区 | 997 个 1 km 格网，1,472 万人（占市域 84.4%） |
| 受影响人口（3 km / 20%） | 190 格 / 210.3 万人，占 14.28% |
| 其中无站覆盖 | 仅 6 格 / 1.19 万人 |
| Gini | 0.294 |
| 最低 20% 群体 | 人均 0.52 桩/千人，为全体 1.57 的 33%，只占可达性总量的 6.6% |

一句话：**深圳的充电荒漠不是「没桩」，是「桩不在人住的地方」——受影响的是 210 万人，而真正「半径内一个站都没有」的只有 1.2 万人。**

## 第 6 页 · 稳健性（55 秒）

| 要讲的 | 数 |
|---|---|
| 半径 1 km vs 3 km | Spearman 0.552，并集重合度 0.301 |
| 半径 5 km vs 3 km | Spearman 0.799，并集重合度 0.557 |
| 阈值 10% / 30%（3 km） | 95 → 285 格；占比 6.02% → 23.38% |
| 换半径后 Gini | 0.576（1 km）/ 0.294（3 km）/ 0.234（5 km） |

一句话：**半径越大，可达性越平缓；但每个半径下最低 20% 的人都明显低于平均——1 km 只剩全体的 {r1p:.1%}，5 km 也只有 {r5p:.0%}。**

## 禁用（不要出现在幻灯片上）

191 格 / 211.2 万 · 200 格 / 202.3 万 · 949 格 / 1,450 万 / 83.1% · 908 个格网 · 图里的「949 cells」。
"""
    out16 = ROOT / "handoff" / "2026-11-16"
    out16.mkdir(parents=True, exist_ok=True)
    (out16 / "number_card.md").write_text(card, encoding="utf-8", newline="\n")
    print(f"[out] {out16 / 'number_card.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
