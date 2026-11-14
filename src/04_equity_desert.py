"""M3 荒漠识别 / M4 人口加权公平性 / M5 敏感性（重写版，2026-11-10）

数据来源（A 的交接包，G1 路线 B：1 km 规则格网）
    handoff/2026-11-10/accessibility.csv   cell_id × d0_m 的 A_i 与半径内站点数
    handoff/2026-11-10/zone_master.csv     格网属性（人口、行列、是否研究区）

统计口径（口径说明卡 v2 的落地实现）
    研究域    in_study == True 的格网（997 个）
    统计域    研究域 ∩ pop > 0（951 个）；人口为 0 的格网只计数，不进入加权统计
    单位      A_i 为桩/人，对外报「每千人桩数」= A_i × 1000
    无覆盖    n_stations_in_radius == 0（等价于 A_i == 0，本脚本两者都验）
    低可达    研究域内 A_i 的分位数判据，默认「严格小于 20% 分位」（quantile_strict）
    敏感度    半径维度的重合度按「受影响并集」计算（低可达 ∪ 无覆盖），与主表同口径
    受影响人口 两类区域的并集，按 cell_id 去重

本文件与 11/06 的 `src/equity_desert.py` 没有代码复用关系：Gini 用前缀和恒等式
重写，分位数与下限截取的边界规则独立定义。两者的一致性由 `src/07_crosscheck.py`
在真实数据的 3 个半径 × 3 档阈值上逐组断言，任何一组不一致即报错。

运行：python src/04_equity_desert.py
输出：outputs/tables/{desert,equity,sensitivity}_table.csv
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ACC_PATH = ROOT / "handoff" / "2026-11-10" / "accessibility.csv"
ZONE_PATH = ROOT / "handoff" / "2026-11-10" / "zone_master.csv"
OUT_DIR = ROOT / "outputs" / "tables"

MAIN_RADIUS = 3000
RADII = (1000, 3000, 5000)
THRESHOLDS = (0.10, 0.20, 0.30)
MAIN_THRESHOLD = 0.20


# ────────────────────────────────────────────────────────────── 读入与校验


def load_layers() -> tuple[pd.DataFrame, pd.DataFrame]:
    """读两张交接表，做一次硬校验；任何一项不满足就报错，不做静默修补。"""
    acc = pd.read_csv(ACC_PATH)
    zone = pd.read_csv(ZONE_PATH)

    need_acc = {"cell_id", "d0_m", "A_i", "piles_per_1000", "in_study", "n_stations_in_radius"}
    need_zone = {"cell_id", "pop", "in_study"}
    if missing := need_acc - set(acc.columns):
        raise ValueError(f"accessibility.csv 缺列：{sorted(missing)}")
    if missing := need_zone - set(zone.columns):
        raise ValueError(f"zone_master.csv 缺列：{sorted(missing)}")

    # 人口以 zone_master 为准；accessibility 自带的 pop 先改名，只用来做一致性核对
    acc = acc.rename(columns={"pop": "pop_acc"}) if "pop" in acc.columns else acc
    merged = acc.merge(
        zone[["cell_id", "pop", "in_study"]].rename(columns={"in_study": "in_study_zone"}),
        on="cell_id",
        how="left",
        validate="many_to_one",
    )
    if merged["pop"].isna().any():
        raise ValueError("存在 accessibility 有、zone_master 无的 cell_id")
    if "pop_acc" in merged.columns and int((merged["pop_acc"] != merged["pop"]).sum()) != 0:
        raise ValueError("两张表的 pop 不一致，口径无法对齐")
    if (merged["in_study"] != merged["in_study_zone"]).any():
        raise ValueError("两张表的 in_study 不一致，口径无法对齐")

    # 结构不变量：A_i == 0 当且仅当半径内没有观测站点
    zero_a = merged["A_i"] == 0
    zero_s = merged["n_stations_in_radius"] == 0
    if int((zero_a != zero_s).sum()) != 0:
        raise ValueError(f"A_i==0 与无站点不等价，冲突 {int((zero_a != zero_s).sum())} 行")

    return merged, zone


def with_per_thousand(frame: pd.DataFrame) -> pd.DataFrame:
    """把 A_i（桩/人）换算成每千人桩数；人口为零处不产出数字（保持 NaN）。"""
    out = frame.copy()
    out["p1k"] = out["piles_per_1000"]
    return out


# ────────────────────────────────────────────────────────────── M4 公平性


def wmean(values: pd.Series, weights: pd.Series) -> float:
    total = float(weights.sum())
    if total <= 0:
        raise ValueError("权重之和为 0")
    return float((values * weights).sum() / total)


def gini(values: pd.Series, weights: pd.Series) -> float | None:
    """人口加权 Gini。

    用排序后的一阶矩恒等式，避免 O(n²) 成对矩阵：
        Σ_i Σ_j w_i w_j |a_i - a_j| = 2 · Σ_k w_k · (a_k · W_<k − A_<k)
    其中 W_<k、A_<k 是 k 之前的权重前缀和与加权值前缀和（升序排列后）。

    返回 None 表示加权总量为 0（全部为零），此时 Gini 无定义。
    """
    df = pd.DataFrame({"a": values.astype(float), "w": weights.astype(float)})
    df = df[df["w"] > 0].sort_values("a", kind="mergesort")
    total_w = float(df["w"].sum())
    total_a = float((df["a"] * df["w"]).sum())
    if total_w <= 0 or total_a <= 0:
        return None

    w = df["w"].to_numpy().astype(float)
    a = df["a"].to_numpy().astype(float)
    w_below = w.cumsum() - w           # 严格小于当前格的权重和
    a_below = (a * w).cumsum() - a * w
    numerator = 2.0 * float((w * (a * w_below - a_below)).sum())
    return numerator / (2.0 * total_a * total_w)


def gini_via_lorenz(values: pd.Series, weights: pd.Series) -> float:
    """同一 Gini 的第二条实现：洛伦兹曲线与对角线围成的面积 × 2。

    只用于自检——两条路径在浮点意义上应当相等。
    """
    df = pd.DataFrame({"a": values.astype(float), "w": weights.astype(float)})
    df = df[df["w"] > 0].sort_values("a", kind="mergesort")
    total_w = float(df["w"].sum())
    total_a = float((df["a"] * df["w"]).sum())
    if total_a <= 0:
        raise ValueError("全部为零时 Lorenz 面积无定义")
    xs = [0.0] + (df["w"].cumsum() / total_w).tolist()
    ys = [0.0] + ((df["a"] * df["w"]).cumsum() / total_a).tolist()
    area = 0.0
    for i in range(len(xs) - 1):
        area += (xs[i + 1] - xs[i]) * (ys[i + 1] + ys[i]) / 2.0
    return 1.0 - 2.0 * area


def wquantile(values: pd.Series, weights: pd.Series, q: float) -> float:
    """人口加权分位数：升序累计人口份额首次达到 q 时，该格的取值。"""
    if not 0.0 <= q <= 1.0:
        raise ValueError(f"q 越界：{q}")
    df = pd.DataFrame({"a": values.astype(float), "w": weights.astype(float)})
    df = df[df["w"] > 0].sort_values("a", kind="mergesort").reset_index(drop=True)
    share = df["w"].cumsum() / df["w"].sum()
    hit = share >= q - 1e-15
    idx = int(hit.idxmax()) if hit.any() else len(df) - 1
    return float(df.loc[idx, "a"])


def bottom_group(values: pd.Series, weights: pd.Series, share: float = 0.20) -> dict:
    """按升序取占人口 share 的最底下一批格网，边界格按人口比例切开。"""
    df = pd.DataFrame({"a": values.astype(float), "w": weights.astype(float)})
    df = df[df["w"] > 0].sort_values("a", kind="mergesort").reset_index(drop=True)
    target = float(df["w"].sum()) * share

    taken_w = 0.0
    taken_a = 0.0
    n_full = 0
    n_cut = 0
    for a, w in zip(df["a"], df["w"]):
        if taken_w >= target - 1e-12:
            break
        piece = min(w, target - taken_w)
        if piece < w - 1e-12:
            n_cut += 1
        taken_w += piece
        taken_a += a * piece
        if piece >= w - 1e-12:
            n_full += 1
        else:
            n_cut += 0

    return {
        "share": share,
        "population": taken_w,
        "population_share": taken_w / float(df["w"].sum()),
        "weighted_mean": taken_a / taken_w if taken_w else float("nan"),
        "cells_full": n_full,
        "cells_partial": min(n_cut, 1),
    }


def equity_row(frame: pd.DataFrame, d0: int) -> dict:
    scope = frame[(frame["d0_m"] == d0) & frame["in_study"]]
    valid = scope[scope["pop"] > 0]
    if valid.empty:
        raise ValueError(f"d0={d0} 无有效格网")

    a, w = valid["p1k"], valid["pop"]
    g = gini(a, w)
    if g is not None:
        g_check = gini_via_lorenz(a, w)
        if abs(g - g_check) > 1e-9:
            raise AssertionError(f"Gini 两条实现不一致：{g} vs {g_check}")

    bottom = bottom_group(a, w, 0.20)
    return {
        "d0_m": d0,
        "cells_in_study": int(len(scope)),
        "cells_valid": int(len(valid)),
        "cells_zero_population": int(len(scope) - len(valid)),
        "population": float(w.sum()),
        "weighted_mean_per_1000": wmean(a, w),
        "gini": g if g is not None else float("nan"),
        "p10": wquantile(a, w, 0.10),
        "bottom20_population": bottom["population"],
        "bottom20_population_share": bottom["population_share"],
        "bottom20_mean_per_1000": bottom["weighted_mean"],
        "max_abs_unit_error": float((valid["piles_per_1000"] - valid["A_i"] * 1000.0).abs().max()),
    }


# ────────────────────────────────────────────────────────────── M3 荒漠


def threshold_value(values: pd.Series, share: float, rule: str) -> float:
    if rule == "quantile":
        return float(values.quantile(share))
    if rule == "rank":
        ordered = values.sort_values(kind="mergesort").reset_index(drop=True)
        k = max(1, math.ceil(share * len(ordered)))
        return float(ordered.iloc[k - 1])
    raise ValueError(f"未知 rule：{rule}")


def desert_row(frame: pd.DataFrame, d0: int, share: float, rule: str = "rank") -> dict:
    """两类荒漠与受影响人口。

    判据只作用于研究域内人口>0 的格网。
      rank           取第 ceil(share·n) 小的值作阈值，**含并列**（默认）
      quantile_strict 取线性插值分位数，判据为严格小于（历史口径，见 degenerate 标记）
    """
    scope = frame[(frame["d0_m"] == d0) & frame["in_study"]]
    valid = scope[scope["pop"] > 0].copy()

    if rule == "rank":
        ordered = valid["p1k"].sort_values(kind="mergesort").reset_index(drop=True)
        k = max(1, math.ceil(share * len(ordered)))
        thr = float(ordered.iloc[k - 1])
        below = valid["p1k"] <= thr
    elif rule == "quantile_strict":
        thr = float(valid["p1k"].quantile(share))
        below = valid["p1k"] < thr
    else:
        raise ValueError(f"未知 rule：{rule}")

    no_cov = valid["n_stations_in_radius"] == 0
    low = below
    both = no_cov & low
    union = no_cov | low

    zero_mass = int((valid["p1k"] == 0).sum())
    return {
        "d0_m": d0,
        "threshold_share": share,
        "rule": rule,
        "threshold_value": thr,
        "cells_valid": int(len(valid)),
        "population_valid": float(valid["pop"].sum()),
        "zero_mass_cells": zero_mass,
        "zero_mass_share": zero_mass / len(valid),
        "degenerate": bool(zero_mass / len(valid) >= share),
        "no_coverage_cells": int(no_cov.sum()),
        "no_coverage_population": float(valid.loc[no_cov, "pop"].sum()),
        "low_access_cells": int(low.sum()),
        "low_access_population": float(valid.loc[low, "pop"].sum()),
        "overlap_cells": int(both.sum()),
        "union_cells": int(union.sum()),
        "union_population": float(valid.loc[union, "pop"].sum()),
        "union_population_share": float(valid.loc[union, "pop"].sum() / valid["pop"].sum()),
    }


# ────────────────────────────────────────────────────────────── M5 敏感性


def radius_sensitivity(frame: pd.DataFrame, share: float = MAIN_THRESHOLD) -> list[dict]:
    """主半径 3 km 对 1 km / 5 km：秩相关 + 重点格网重合度。只换半径，不换阈值组合。

    判据与 desert_row 的 quantile_strict 一致（严格小于线性插值分位数）；
    重合度在「受影响并集」（低可达 ∪ 无覆盖）上计算——1 km 下低可达集合因
    24% 格网 A_i 恰为 0 而退化，用并集才与其他半径可比。
    """
    base = frame[(frame["d0_m"] == MAIN_RADIUS) & frame["in_study"] & (frame["pop"] > 0)]
    base_thr = threshold_value(base["p1k"], share, "quantile")
    base_low = set(base.loc[(base["p1k"] < base_thr) |
                            (base["n_stations_in_radius"] == 0), "cell_id"])

    rows = []
    for other in (1000, 5000):
        alt = frame[(frame["d0_m"] == other) & frame["in_study"] & (frame["pop"] > 0)]
        joined = base[["cell_id", "p1k"]].merge(
            alt[["cell_id", "p1k"]], on="cell_id", suffixes=("_base", "_alt"), validate="one_to_one"
        )
        rho = float(joined["p1k_base"].corr(joined["p1k_alt"], method="spearman"))

        alt_thr = threshold_value(alt["p1k"], share, "quantile")
        alt_low = set(alt.loc[(alt["p1k"] < alt_thr) |
                              (alt["n_stations_in_radius"] == 0), "cell_id"])
        inter = base_low & alt_low
        union = base_low | alt_low

        rows.append({
            "dimension": "radius",
            "base": f"{MAIN_RADIUS}",
            "comparison": f"{other}",
            "cells_compared": int(len(joined)),
            "spearman_rho": rho,
            "base_low_cells": len(base_low),
            "alt_low_cells": len(alt_low),
            "overlap_cells": len(inter),
            "jaccard": (len(inter) / len(union)) if union else float("nan"),
            "base_low_retained": (len(inter) / len(base_low)) if base_low else float("nan"),
        })
    return rows


def threshold_sensitivity(frame: pd.DataFrame, d0: int = MAIN_RADIUS) -> list[dict]:
    """只换低可达阈值，10% / 20% / 30%；半径固定 3 km。"""
    rows = []
    for share in THRESHOLDS:
        row = desert_row(frame, d0, share, "quantile_strict")
        rows.append({
            "dimension": "threshold",
            "base": f"{MAIN_THRESHOLD:.0%}",
            "comparison": f"{share:.0%}",
            "threshold_value": row["threshold_value"],
            "low_access_cells": row["low_access_cells"],
            "low_access_population": row["low_access_population"],
            "union_cells": row["union_cells"],
            "union_population": row["union_population"],
            "union_population_share": row["union_population_share"],
        })
    return rows


# ────────────────────────────────────────────────────────────── 入口


def main() -> int:
    frame, zone = load_layers()
    frame = with_per_thousand(frame)

    equity = pd.DataFrame([equity_row(frame, d0) for d0 in RADII])
    desert = pd.DataFrame([desert_row(frame, d0, share, "quantile_strict")
                           for d0 in RADII for share in THRESHOLDS])
    # 判据变体只对主情景各算一遍，供与 A 的口径对账
    variants = pd.DataFrame([desert_row(frame, MAIN_RADIUS, MAIN_THRESHOLD, rule)
                             for rule in ("rank", "quantile_strict")])
    sensitivity = pd.DataFrame(radius_sensitivity(frame) + threshold_sensitivity(frame))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    equity.to_csv(OUT_DIR / "equity_table.csv", index=False, encoding="utf-8-sig")
    desert.to_csv(OUT_DIR / "desert_table.csv", index=False, encoding="utf-8-sig")
    sensitivity.to_csv(OUT_DIR / "sensitivity_table.csv", index=False, encoding="utf-8-sig")

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 40)

    print("=" * 96)
    print("M4 公平性（研究域内人口>0 的格网）")
    print(equity.round(6).to_string(index=False))
    print()
    print("M3 荒漠（主情景 3 km，三档阈值）")
    main3 = desert[desert["d0_m"] == MAIN_RADIUS]
    print(main3[["threshold_share", "threshold_value", "no_coverage_cells", "no_coverage_population",
                 "low_access_cells", "low_access_population", "union_cells", "union_population",
                 "union_population_share"]].round(6).to_string(index=False))
    print()
    print("判据变体（3 km / 20%）：")
    print(variants[["rule", "threshold_value", "low_access_cells", "low_access_population"]]
          .round(6).to_string(index=False))
    print()
    print("M5 敏感性")
    print(sensitivity.round(6).to_string(index=False))
    print("=" * 96)
    print("已写出：", OUT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
