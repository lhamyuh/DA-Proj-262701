"""M3 荒漠识别 / M4 人口加权公平性的核心函数。

项目：Shenzhen EV Charging Deserts（Data Analytics 262701，CUHKSZ）
主责：B（Li Luoyang）｜复核：A（YANG Linyu）
版本：2026-11-06 首版，仅覆盖 M3 与 M4 的计算内核，不含读栅格与出图

输入契约（对应计划 §3.3 的 zone 级表）
    zone_id          str      需求单元 ID（TAZ 或 1 km 格网）
    pop              float    人口（人）
    a_i              float    可达性，每千人桩数（= 桩/人 × 1000，见 §4.1）
    has_station_3km  bool     基准半径内是否有观测公共站点（由 M2 的 accessibility 导出）

三条口径，与计划正文一致
1. 人口 <= 0 的单元不进入 Gini、Lorenz、分位数与荒漠判定，单独计数并报告（§4.3）。
2. 加权均值为 0 时不返回 Gini，改报「全部为零」，不得表述为「最公平」（§4.3）。
3. 「无观测覆盖」与「相对低可达」是两套判定，「受影响人口」取并集去重（§4.2）。

本模块刻意只 import pandas：计划 §5.2 的验收标准是「仅依赖 pandas」，
M3/M4 的全部输入都来自 A 的 CSV，不需要 geopandas / rasterio。
"""

from __future__ import annotations

import math

import pandas as pd

REQUIRED_COLUMNS = ("zone_id", "pop", "a_i")
COVERAGE_COLUMN = "has_station_3km"
DESERT_METHODS = ("below_quantile", "at_quantile", "rank")
MEAN_ZERO_NOTE = "全部为零（加权均值为 0，不得表述为最公平）"


# ---------------------------------------------------------------- 基础工具


def _as_float_series(values) -> pd.Series:
    """把 list / ndarray / Series 统一成 float64 Series，None 视为缺失。"""
    return pd.Series(values, dtype="float64", copy=True).reset_index(drop=True)


def _pairs(values, weights) -> pd.DataFrame:
    """值—权重成对表，并剔除权重 <= 0 的单元（人口为零不参与统计）。"""
    a = _as_float_series(values)
    w = _as_float_series(weights)
    if len(a) != len(w):
        raise ValueError(f"values 与 weights 长度不一致：{len(a)} vs {len(w)}")
    df = pd.DataFrame({"a": a.to_numpy(), "w": w.to_numpy()})
    return df[df["w"] > 0].reset_index(drop=True)


def load_zones(path) -> pd.DataFrame:
    """读取 zone 级 CSV 并做类型检查；缺少必备列直接报错，不做静默补 0。"""
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path} 缺少必备列：{missing}")

    df = df.copy()
    for col in ("pop", "a_i"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
        if df[col].isna().any():
            # 计划 §2.3：人口缺失值不得按零人口处理
            raise ValueError(f"{path} 的 {col} 列存在无法解析的缺失值，不得按 0 处理")

    if COVERAGE_COLUMN in df.columns:
        df[COVERAGE_COLUMN] = (
            df[COVERAGE_COLUMN]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(["true", "1", "yes", "y", "是"])
        )
    return df


def drop_zero_population(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """剔除人口 <= 0 的单元，返回 (保留的表, 被剔除的单元数)。"""
    mask = df["pop"] > 0
    return df.loc[mask].reset_index(drop=True), int((~mask).sum())


# ---------------------------------------------------------------- 公平性（M4）


def weighted_mean(values, weights) -> float:
    """人口加权均值（§4.3 的 a_w 上划线）。"""
    df = _pairs(values, weights)
    total_w = float(df["w"].sum())
    if total_w <= 0:
        raise ValueError("权重之和为 0，加权均值无定义")
    return float((df["a"] * df["w"]).sum() / total_w)


def weighted_gini(values, weights) -> float | None:
    """人口加权 Gini 系数。

    G = sum_i sum_j w_i w_j |a_i - a_j| / (2 * a_w * (sum w)^2)
    由于 a_w = sum(w a) / sum(w)，分母可化简为 2 * sum(w a) * sum(w)，
    手算时只需两个整数：成对差分子与 2 * ΣPa * ΣP。

    返回 None 表示人口加权总量为 0（全部为零），此时不定义 Gini。
    """
    df = _pairs(values, weights)
    total_w = float(df["w"].sum())
    weighted_total = float((df["a"] * df["w"]).sum())
    if total_w <= 0 or weighted_total <= 0:
        return None

    a = df["a"].to_numpy()
    w = df["w"].to_numpy()
    pair_diff = (w[:, None] * w[None, :] * abs(a[:, None] - a[None, :])).sum()
    return float(pair_diff / (2.0 * weighted_total * total_w))


def weighted_quantile(values, weights, q: float) -> float:
    """人口加权分位数：按值升序累计人口，第一个累计份额 >= q 的单元取值。

    q=0.10 即 P10 —— 最差的那 10% 人口处在什么水平（§4.3 要求报告）。
    """
    if not 0 <= q <= 1:
        raise ValueError(f"q 必须落在 [0, 1]，收到 {q}")
    df = _pairs(values, weights).sort_values("a", kind="mergesort").reset_index(drop=True)
    total_w = float(df["w"].sum())
    cum = (df["w"].cumsum() / total_w).to_numpy()
    hit = (cum >= q)
    pos = int(hit.argmax()) if hit.any() else len(df) - 1
    return float(df["a"].iloc[pos])


def lorenz_curve(values, weights) -> pd.DataFrame:
    """Lorenz 曲线：横轴累计人口份额，纵轴累计可达性份额，并补上原点。

    返回列：pop_share, acc_share。曲线越低（离对角线越远）表示分布越不均。
    """
    df = _pairs(values, weights).sort_values("a", kind="mergesort").reset_index(drop=True)
    total_w = float(df["w"].sum())
    weighted_total = float((df["a"] * df["w"]).sum())
    if total_w <= 0:
        raise ValueError("权重之和为 0，Lorenz 曲线无定义")
    if weighted_total <= 0:
        raise ValueError("可达性总量为 0（全部为零），Lorenz 曲线无定义")

    pop_share = (df["w"].cumsum() / total_w).to_numpy()
    acc_share = ((df["a"] * df["w"]).cumsum() / weighted_total).to_numpy()
    out = pd.DataFrame({
        "pop_share": [0.0, *pop_share.tolist()],
        "acc_share": [0.0, *acc_share.tolist()],
    })
    return out


def bottom_group_metrics(values, weights, share: float = 0.20) -> dict:
    """最低 share 份额人口（按 a_i 升序）的指标。

    边界单元按人口比例切开计入，故「最低 20% 群体」的入口数可能带小数；
    这正是 §4.3 要的「最低 20% 群体的人口占比与加权均值」，
    它和 §4.2「相对低可达」按单元分位数判定不是一回事，不要混用。
    """
    if not 0 < share <= 1:
        raise ValueError(f"share 必须落在 (0, 1]，收到 {share}")

    df = _pairs(values, weights).sort_values("a", kind="mergesort").reset_index(drop=True)
    total_w = float(df["w"].sum())
    target = total_w * share

    taken_pop = 0.0
    taken_acc = 0.0
    n_units = 0
    n_partial = 0
    cut_value = float(df["a"].iloc[0])

    for a, w in zip(df["a"].to_numpy(), df["w"].to_numpy()):
        if taken_pop >= target - 1e-12:
            break
        take = min(float(w), target - taken_pop)
        if take < float(w) - 1e-12:
            n_partial += 1
        taken_pop += take
        taken_acc += float(a) * take
        cut_value = float(a)
        n_units += 1

    return {
        "share": share,
        "pop": taken_pop,
        "pop_share": taken_pop / total_w if total_w else None,
        "weighted_mean": taken_acc / taken_pop if taken_pop else None,
        "n_units": n_units,
        "n_partial_units": n_partial,
        "cut_value": cut_value,
    }


def equity_summary(zones: pd.DataFrame, bottom_share: float = 0.20) -> dict:
    """四项必须并列报告的指标（§4.3）+ 被剔除的零人口单元数。"""
    valid, dropped = drop_zero_population(zones)
    if valid.empty:
        raise ValueError("全部单元人口为 0，无法计算公平性指标")

    total_w = float(valid["pop"].sum())
    weighted_total = float((valid["a_i"] * valid["pop"]).sum())
    bottom = bottom_group_metrics(valid["a_i"], valid["pop"], bottom_share)

    if weighted_total <= 0:
        return {
            "n_units": int(len(valid)),
            "n_zero_population_dropped": dropped,
            "population": total_w,
            "weighted_mean": 0.0,
            "gini": None,
            "gini_note": MEAN_ZERO_NOTE,
            "p10": 0.0,
            "bottom_group": bottom,
        }

    return {
        "n_units": int(len(valid)),
        "n_zero_population_dropped": dropped,
        "population": total_w,
        "weighted_mean": weighted_mean(valid["a_i"], valid["pop"]),
        "gini": weighted_gini(valid["a_i"], valid["pop"]),
        "gini_note": None,
        "p10": weighted_quantile(valid["a_i"], valid["pop"], 0.10),
        "bottom_group": bottom,
    }


# ---------------------------------------------------------------- 荒漠（M3）


def desert_threshold(a_values, share: float = 0.20, method: str = "below_quantile") -> float:
    """低可达判定的阈值。

    below_quantile / at_quantile：单元层线性插值分位数
    rank：第 ceil(share * n) 小的单元值（小样本更稳）
    """
    if method not in DESERT_METHODS:
        raise ValueError(f"method 必须是 {DESERT_METHODS} 之一，收到 {method!r}")
    if not 0 < share <= 1:
        raise ValueError(f"share 必须落在 (0, 1]，收到 {share}")

    s = _as_float_series(a_values)
    if s.empty:
        raise ValueError("无可判定单元")
    if method in ("below_quantile", "at_quantile"):
        return float(s.quantile(share))
    k = max(1, math.ceil(share * len(s)))
    return float(s.sort_values(kind="mergesort").iloc[k - 1])


def low_access_mask(a_values, share: float = 0.20, method: str = "below_quantile"):
    """返回 (掩码 list, 阈值)。低于阈值判为「相对低可达」。"""
    s = _as_float_series(a_values)
    thr = desert_threshold(s, share, method)
    if method == "below_quantile":
        mask = (s < thr).tolist()
    else:
        mask = (s <= thr).tolist()
    return mask, thr


def classify_deserts(
    zones: pd.DataFrame,
    share: float = 0.20,
    method: str = "below_quantile",
) -> tuple[pd.DataFrame, dict]:
    """标注两类荒漠与受影响并集。

    返回 (带布尔列的表, meta)。布尔列：no_coverage / low_access / affected。
    meta 记录阈值、方法与三类计数，供 numbers_frozen.md 追溯。
    """
    missing = [c for c in (*REQUIRED_COLUMNS, COVERAGE_COLUMN) if c not in zones.columns]
    if missing:
        raise ValueError(f"classify_deserts 缺少列：{missing}")

    out = zones.copy().reset_index(drop=True)
    pop = out["pop"].to_numpy()
    a = out["a_i"].to_numpy()
    has = out[COVERAGE_COLUMN].astype(bool).to_numpy()

    in_scope = pop > 0
    scope_positions = [i for i, flag in enumerate(in_scope) if flag]
    if not scope_positions:
        raise ValueError("全部单元人口为 0，无判定对象")

    mask_scoped, thr = low_access_mask([a[i] for i in scope_positions], share, method)
    low_by_pos = dict(zip(scope_positions, mask_scoped))

    no_coverage = [bool(in_scope[i] and not has[i]) for i in range(len(out))]
    low_access = [bool(low_by_pos.get(i, False)) for i in range(len(out))]
    affected = [bool(no_coverage[i] or low_access[i]) for i in range(len(out))]

    out["no_coverage"] = no_coverage
    out["low_access"] = low_access
    out["affected"] = affected

    meta = {
        "share": share,
        "method": method,
        "threshold": thr,
        "n_units_in_scope": len(scope_positions),
        "n_zero_population_excluded": int(len(out) - len(scope_positions)),
    }
    return out, meta


def desert_summary(classified: pd.DataFrame) -> dict:
    """两类荒漠与并集的单元数 / 人口数，并给出并集去重省下的量。"""
    def _agg(col: str) -> tuple[int, float]:
        sub = classified.loc[classified[col]]
        return int(len(sub)), float(sub["pop"].sum())

    n_no, pop_no = _agg("no_coverage")
    n_low, pop_low = _agg("low_access")
    n_union, pop_union = _agg("affected")
    total_pop = float(classified["pop"].sum())

    return {
        "no_coverage_units": n_no,
        "no_coverage_population": pop_no,
        "low_access_units": n_low,
        "low_access_population": pop_low,
        "union_units": n_union,
        "union_population": pop_union,
        "union_share_of_population": pop_union / total_pop if total_pop else None,
        "overlap_units": n_no + n_low - n_union,
        "dedup_saved_units": n_no + n_low - n_union,
        "total_population": total_pop,
    }


def format_metrics(summary: dict) -> str:
    """把 equity_summary 的结果压成一行，避免手抄出错。"""
    gini = summary["gini"]
    gini_txt = "未定义（全部为零）" if gini is None else f"{gini:.6f}"
    bottom = summary["bottom_group"]
    return (
        f"单元 {summary['n_units']} 个（剔除零人口 {summary['n_zero_population_dropped']} 个）"
        f"｜人口 {summary['population']:.0f}"
        f"｜加权均值 {summary['weighted_mean']:.6f}"
        f"｜Gini {gini_txt}"
        f"｜P10 {summary['p10']:.6f}"
        f"｜最低 {bottom['share']:.0%} 群体 {bottom['pop']:.1f} 人"
        f"（{bottom['pop_share']:.4%}），加权均值 {bottom['weighted_mean']:.6f}"
    )
