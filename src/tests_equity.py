"""6 个虚拟单元的人工算例与 M3/M4 断言（B：Li Luoyang，2026-11-06）。

用途
1. 交付计划 §5.2 的「6 个虚拟单元的人工算例 + 两例通过」：均匀供给、单区供给。
2. 把 §4.2 / §4.3 的口径钉死成可执行的断言，11/12 换真实数据时先跑这一份。

运行（只需 pandas，不需要 pytest）：
    python src/tests_equity.py
装了 pytest 也可以：
    python -m pytest src/tests_equity.py -q

设计约定
- 单元固定为 6 个：Z1..Z6，人口 100/200/300/400/500/600，合计 2100 —— 便于手算。
- 「供给」的两个算例指 M4 看到的 a_i：均匀供给（每处都是 12）与单区供给（只有 Z1 有 60）。
- 「混合」算例 a_i = 0/2/4/6/8/10，专门用来验荒漠判定与并集去重。
- 期望值全部由手算给出，写在同目录的 manual_example_6u.md 里。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import equity_desert as eq  # noqa: E402

TOL = 1e-9
CSV_PATH = Path(__file__).resolve().parents[1] / "handoff" / "2026-11-07" / "zones_6u.csv"

# 6 个虚拟单元：人口合计 2100（手算友好）
UNITS = [
    ("Z1", 100.0, 0.0, False),
    ("Z2", 200.0, 2.0, True),
    ("Z3", 300.0, 4.0, True),
    ("Z4", 400.0, 6.0, True),
    ("Z5", 500.0, 8.0, True),
    ("Z6", 600.0, 10.0, True),
]


def _zones(rows=None) -> pd.DataFrame:
    rows = rows or UNITS
    return pd.DataFrame(rows, columns=["zone_id", "pop", "a_i", "has_station_3km"])


def _close(actual, expected, tol=TOL, label=""):
    if actual is None:
        raise AssertionError(f"{label}：期望 {expected}，得到 None")
    if abs(float(actual) - float(expected)) > tol:
        raise AssertionError(f"{label}：期望 {expected}，得到 {actual}")


# ------------------------------------------------------------ 手算基数


def test_hand_computed_baseline():
    """手算基数：ΣP = 2100、ΣPa = 14000、成对差分子 = 14,560,000。"""
    z = _zones()
    total_p = z["pop"].sum()
    total_pa = (z["pop"] * z["a_i"]).sum()
    _close(total_p, 2100, label="ΣP")
    _close(total_pa, 14000, label="ΣPa")

    # 15 对 (i < j) 的 Pi*Pj*|ai-aj| 之和 = 7,280,000，成对差分子 ×2 = 14,560,000
    pair = 0.0
    for i in range(len(z)):
        for j in range(len(z)):
            pair += z["pop"][i] * z["pop"][j] * abs(z["a_i"][i] - z["a_i"][j])
    _close(pair, 14_560_000, label="ΣΣ PiPj|ai-aj|")


# ------------------------------------------------------------ 算例一：均匀供给


def test_uniform_supply():
    """均匀供给：每处可达性相同 → Gini 必须为 0、Lorenz 与对角线重合、无荒漠。"""
    z = _zones()
    z["a_i"] = 12.0          # 所有单元一样
    z["has_station_3km"] = True

    summary = eq.equity_summary(z)
    _close(summary["weighted_mean"], 12.0, label="均匀：加权均值")
    _close(summary["gini"], 0.0, tol=1e-12, label="均匀：Gini")
    _close(summary["p10"], 12.0, label="均匀：P10")
    _close(summary["bottom_group"]["weighted_mean"], 12.0, label="均匀：最低20%均值")
    _close(summary["bottom_group"]["pop_share"], 0.20, tol=1e-12, label="均匀：最低20%人口占比")

    curve = eq.lorenz_curve(z["a_i"], z["pop"])
    for pop_share, acc_share in zip(curve["pop_share"], curve["acc_share"]):
        _close(acc_share, pop_share, tol=1e-12, label="均匀：Lorenz 对角线")

    classified, meta = eq.classify_deserts(z)
    _close(meta["threshold"], 12.0, label="均匀：阈值")
    assert classified["no_coverage"].sum() == 0, "均匀供给下不应有无观测覆盖单元"
    assert classified["low_access"].sum() == 0, (
        "均匀供给下不应有相对低可达单元：判定用严格小于分位数，"
        "否则所有单元都会等于阈值而被误标"
    )
    assert classified["affected"].sum() == 0


# ------------------------------------------------------------ 算例二：单区供给


def test_single_zone_supply():
    """单区供给：只有 Z1 有供给（每千人 60 桩），其余 5 个为 0。"""
    z = _zones()
    z["a_i"] = [60.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    z["has_station_3km"] = [True, False, False, False, False, False]

    # 手算：ΣPa = 60*100 = 6000；成对差分子 = 2 * 6000 * 2000 = 24,000,000
    #       G = 24,000,000 / (2 * 6000 * 2100) = 20/21 = 0.952380952...
    summary = eq.equity_summary(z)
    _close(summary["weighted_mean"], 6000 / 2100, label="单区：加权均值")
    _close(summary["gini"], 20 / 21, label="单区：Gini")
    _close(summary["p10"], 0.0, label="单区：P10")
    _close(summary["bottom_group"]["weighted_mean"], 0.0, label="单区：最低20%均值")
    _close(summary["bottom_group"]["pop"], 420.0, label="单区：最低20%人口")

    classified, meta = eq.classify_deserts(z)
    _close(meta["threshold"], 0.0, label="单区：阈值")
    # 严格小于 0 的单元不存在，相对低可达为空；无观测覆盖 5 个（共 2000 人）
    assert classified["low_access"].sum() == 0
    assert classified["no_coverage"].sum() == 5

    info = eq.desert_summary(classified)
    assert info["no_coverage_population"] == 2000.0
    assert info["union_units"] == 5
    assert info["union_population"] == 2000.0
    _close(info["union_share_of_population"], 2000 / 2100, label="单区：受影响人口占比")


# ------------------------------------------------------------ 混合算例（荒漠）


def test_mixed_case_metrics():
    """混合算例的四个公平性指标。"""
    summary = eq.equity_summary(_zones())
    _close(summary["weighted_mean"], 14000 / 2100, label="混合：加权均值")
    _close(summary["gini"], 14_560_000 / 58_800_000, label="混合：Gini")
    _close(summary["p10"], 2.0, label="混合：P10")
    # 最低 20% = 420 人：Z1 全部 100 人 + Z2 全部 200 人 + Z3 中的 120 人
    _close(summary["bottom_group"]["pop"], 420.0, label="混合：最低20%人口")
    _close(summary["bottom_group"]["weighted_mean"], 880 / 420, label="混合：最低20%均值")
    assert summary["bottom_group"]["n_partial_units"] == 1


def test_desert_methods_differ():
    """三种判定方式在混合算例上的差别，必须在口径卡里选定一种。"""
    z = _zones()

    below, meta_below = eq.classify_deserts(z, 0.20, "below_quantile")
    at, meta_at = eq.classify_deserts(z, 0.20, "at_quantile")
    rank, meta_rank = eq.classify_deserts(z, 0.20, "rank")

    _close(meta_below["threshold"], 2.0, label="below：阈值")
    _close(meta_at["threshold"], 2.0, label="at：阈值")
    _close(meta_rank["threshold"], 2.0, label="rank：阈值")

    assert below["low_access"].sum() == 1     # 严格小于 2 → 只有 Z1
    assert at["low_access"].sum() == 2        # 小于等于 2 → Z1、Z2
    assert rank["low_access"].sum() == 2      # 取第 2 小 → 阈值 2，含并列


def test_union_dedup():
    """并集去重：两类重叠时，受影响单元数应小于两类之和。"""
    z = _zones()
    classified, _ = eq.classify_deserts(z, 0.20, "at_quantile")
    info = eq.desert_summary(classified)

    assert info["no_coverage_units"] == 1     # Z1
    assert info["low_access_units"] == 2      # Z1、Z2
    assert info["union_units"] == 2           # 去重后
    assert info["dedup_saved_units"] == 1


def test_no_coverage_implies_zero_access():
    """结构性不变量：无观测覆盖的单元，其 A_i 必为 0。

    这条把「无观测覆盖」钉在 M2 的输出上：只要 A_i > 0 就一定有站覆盖，
    所以并集去重不是形式主义——零值超过 20% 时，相对低可达会漏掉一部分零值单元。
    """
    z = _zones()
    z.loc[1, "has_station_3km"] = False       # 让 Z2 也没有站，但 a_i > 0
    classified, _ = eq.classify_deserts(z)
    flagged = classified.loc[classified["no_coverage"]]
    assert len(flagged) == 2
    assert flagged["a_i"].max() > 0, "本用例故意构造矛盾数据，用来验证不做静默修正"


# ------------------------------------------------------------ 边界与口径


def test_zero_population_excluded():
    """人口为零的单元剔除，但不影响 Gini；剔除数要报出来。"""
    z = _zones().copy()
    z.loc[len(z)] = ["Z7", 0.0, 999.0, False]

    summary = eq.equity_summary(z)
    assert summary["n_zero_population_dropped"] == 1
    assert summary["n_units"] == 6
    _close(summary["gini"], 14_560_000 / 58_800_000, label="零人口剔除后 Gini 不变")

    classified, meta = eq.classify_deserts(z)
    assert meta["n_zero_population_excluded"] == 1
    assert not bool(classified.loc[classified["zone_id"] == "Z7", "affected"].iloc[0])


def test_mean_zero_is_not_fair():
    """全部为零时：不返回 Gini，报「全部为零」，不得说成最公平。"""
    z = _zones()
    z["a_i"] = 0.0
    z["has_station_3km"] = False

    summary = eq.equity_summary(z)
    _close(summary["weighted_mean"], 0.0, label="全零：加权均值")
    assert summary["gini"] is None, "均值为 0 时不得返回 Gini"
    assert summary["gini_note"] == eq.MEAN_ZERO_NOTE
    _close(summary["p10"], 0.0, label="全零：P10")
    _close(summary["bottom_group"]["weighted_mean"], 0.0, label="全零：最低20%均值")

    try:
        eq.lorenz_curve(z["a_i"], z["pop"])
    except ValueError as exc:
        assert "全部为零" in str(exc) or "为 0" in str(exc)
    else:
        raise AssertionError("全部为零时 Lorenz 曲线应报错，而不是画一条平行线")


def test_lorenz_endpoints():
    curve = eq.lorenz_curve(_zones()["a_i"], _zones()["pop"])
    _close(curve["pop_share"].iloc[0], 0.0, label="Lorenz 起点人口")
    _close(curve["acc_share"].iloc[0], 0.0, label="Lorenz 起点可达性")
    _close(curve["pop_share"].iloc[-1], 1.0, label="Lorenz 终点人口")
    _close(curve["acc_share"].iloc[-1], 1.0, label="Lorenz 终点可达性")
    # 曲线不得跑到对角线以上（人口加权后累计可达性 <= 累计人口份额）
    for pop_share, acc_share in zip(curve["pop_share"], curve["acc_share"]):
        assert acc_share <= pop_share + 1e-12, "Lorenz 曲线不得高于对角线"


def test_load_zones_reads_fixture():
    z = eq.load_zones(CSV_PATH)
    assert list(z.columns)[:3] == ["zone_id", "pop", "a_i"]
    assert len(z) == 6
    assert z["pop"].sum() == 2100
    assert bool(z.loc[0, "has_station_3km"]) is False
    assert bool(z.loc[5, "has_station_3km"]) is True


def test_load_zones_rejects_missing_population():
    """人口缺失不得按 0 处理（§2.3）。"""
    broken = _zones().copy()
    broken.loc[2, "pop"] = None
    tmp = Path(__file__).resolve().parent / "_tmp_broken_zones.csv"
    broken.to_csv(tmp, index=False)
    try:
        eq.load_zones(tmp)
    except ValueError as exc:
        assert "缺失" in str(exc)
    else:
        raise AssertionError("人口缺失时 load_zones 应报错")
    finally:
        tmp.unlink(missing_ok=True)


# ------------------------------------------------------------ 运行器


def _run_all() -> int:
    tests = [(name, fn) for name, fn in sorted(globals().items())
             if name.startswith("test_") and callable(fn)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {name}\n      {exc}")
        else:
            print(f"PASS  {name}")
    return failed


def main() -> int:
    z = eq.load_zones(CSV_PATH)
    print("=" * 78)
    print("6 个虚拟单元（人口合计 2100）")
    print(z.to_string(index=False))
    print("-" * 78)

    summary = eq.equity_summary(z)
    print("M4 四项指标：")
    print("  " + eq.format_metrics(summary))
    print("-" * 78)

    classified, meta = eq.classify_deserts(z)
    print(f"M3 荒漠判定（share={meta['share']:.0%}, method={meta['method']}, "
          f"阈值={meta['threshold']:.4f}）")
    print(classified[["zone_id", "pop", "a_i", "no_coverage", "low_access", "affected"]]
          .to_string(index=False))
    info = eq.desert_summary(classified)
    print(f"  无观测覆盖：{info['no_coverage_units']} 个单元 / "
          f"{info['no_coverage_population']:.0f} 人")
    print(f"  相对低可达：{info['low_access_units']} 个单元 / "
          f"{info['low_access_population']:.0f} 人")
    print(f"  并集去重　：{info['union_units']} 个单元 / "
          f"{info['union_population']:.0f} 人 "
          f"（占 {info['union_share_of_population']:.4%}，去重省下 {info['dedup_saved_units']} 个）")
    print("=" * 78)

    failed = _run_all()
    print("=" * 78)
    print(f"合计 {len([1 for n in globals() if n.startswith('test_')])} 项断言，失败 {failed} 项")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
