"""11_package.py — 把 B 的全部交付物汇总成 handoff/2026-11-14/ 分类快照（B，2026-11-14）

本目录是**只读快照**，不是第二份可编辑副本：
    权威版本分别在 outputs/tables/、outputs/figures/、numbers_frozen.md、
    report/sections/b_equity_methods.md；改数请改那里，再重跑 04 → 09 → 11。

目录结构
    tables/   desert_table.csv  equity_table.csv  sensitivity_table.csv  table1_main.csv
    figures/  fig3_lorenz.png   fig3_lorenz_slide.jpg
    docs/     numbers_frozen.md  b_equity_methods.md  number_card.md
    sha256.txt  上述全部文件（不含本清单自身）

注：docs/number_card.md 由 09_freeze.py 直接写入，本脚本不覆盖。

运行：python src/11_package.py
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "handoff" / "2026-11-14"

# (源文件, 目标子目录)
ITEMS = [
    (ROOT / "outputs" / "tables" / "desert_table.csv", "tables"),
    (ROOT / "outputs" / "tables" / "equity_table.csv", "tables"),
    (ROOT / "outputs" / "tables" / "sensitivity_table.csv", "tables"),
    (ROOT / "outputs" / "tables" / "table1_main.csv", "tables"),
    (ROOT / "outputs" / "figures" / "fig3_lorenz.png", "figures"),
    (ROOT / "outputs" / "figures" / "slide" / "fig3_lorenz_slide.jpg", "figures"),
    (ROOT / "numbers_frozen.md", "docs"),
    (ROOT / "report" / "sections" / "b_equity_methods.md", "docs"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    missing = [str(src) for src, _ in ITEMS if not src.exists()]
    if missing:
        print("[ERROR] 缺少源文件：")
        for m in missing:
            print("  -", m)
        return 1

    for src, sub in ITEMS:
        dst_dir = PKG / sub
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst_dir / src.name)
        print(f"[copy] {src.relative_to(ROOT)}  ->  {sub}/{src.name}")

    files = sorted(p for p in PKG.rglob("*") if p.is_file() and p.name != "sha256.txt")
    lines = [f"{sha256(p)}  {p.relative_to(PKG).as_posix()}" for p in files]
    (PKG / "sha256.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"[out] {PKG / 'sha256.txt'}  {len(files)} 个文件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
