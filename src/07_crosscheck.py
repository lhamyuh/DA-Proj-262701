"""07_crosscheck.py — 出数代码与受测内核的一致性断言（B，2026-11-11）

背景
    12 项测试（`src/tests_equity.py`）覆盖的是 `src/equity_desert.py` 的内核；
    真正出数的是 `src/04_equity_desert.py`，两者按设计互不复用代码。
    因此需要一道显式断言：在真实数据上，两套实现在 3 个半径 × 3 档阈值上
    必须给出完全相同的（无覆盖、低可达、并集）单元数与阈值。

判据
    quantile_strict / below_quantile —— 严格小于线性插值分位数。

运行
    python src/07_crosscheck.py
退出码
    0 = 九组全部一致；1 = 存在不一致。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    eq = load(ROOT / "src" / "equity_desert.py", "eq_kernel")
    fd = load(ROOT / "src" / "04_equity_desert.py", "fd_pipeline")

    frame, _ = fd.load_layers()
    frame = fd.with_per_thousand(frame)

    print(f"{'d0':>5}  {'share':>5}  {'thr(04)':>9}  {'thr(kernel)x1000':>17}  "
          f"{'(no,low,union) 04':>18}  {'kernel':>18}  verdict")
    print("-" * 96)

    bad = 0
    for d0 in fd.RADII:
        for share in fd.THRESHOLDS:
            row = fd.desert_row(frame, d0, share, "quantile_strict")

            v = frame[(frame["d0_m"] == d0) & frame["in_study"] & (frame["pop"] > 0)].copy()
            zones = pd.DataFrame({
                "zone_id": v["cell_id"],
                "pop": v["pop"],
                "a_i": v["A_i"],
                "has_station_3km": v["n_stations_in_radius"] > 0,
            })
            classified, meta = eq.classify_deserts(zones, share, "below_quantile")

            # 04 以「每千人桩数」为单位，内核以「桩/人」为单位；阈值按 ×1000 对齐后比较
            got = (int(classified["no_coverage"].sum()),
                   int(classified["low_access"].sum()),
                   int(classified["affected"].sum()))
            exp = (row["no_coverage_cells"], row["low_access_cells"], row["union_cells"])
            thr_kernel = float(meta["threshold"]) * 1000.0
            ok_thr = abs(thr_kernel - float(row["threshold_value"])) < 1e-9
            ok = (got == exp) and ok_thr
            bad += 0 if ok else 1

            print(f"{d0:>5}  {share:>5.0%}  {row['threshold_value']:>9.6f}  "
                  f"{thr_kernel:>17.6f}  {str(exp):>18}  {str(got):>18}  "
                  f"{'OK' if ok else 'MISMATCH'}")

    print("-" * 96)
    if bad:
        print(f"[FAIL] {bad} / {len(fd.RADII) * len(fd.THRESHOLDS)} 组不一致")
        return 1
    print(f"[PASS] {len(fd.RADII) * len(fd.THRESHOLDS)} / "
          f"{len(fd.RADII) * len(fd.THRESHOLDS)} 组一致："
          f"出数代码（04）与受测内核（equity_desert）在真实数据上等价")
    return 0


if __name__ == "__main__":
    sys.exit(main())
