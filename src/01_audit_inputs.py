#!/usr/bin/env python3
"""01_audit_inputs.py — 数据审计与 D0 自检

用途
    遍历 data/raw/，对每个文件回答 D0 的三个问题并留下证据：
      Q1 体积是否与来源说明的数量级相符？
      Q2 行数 / 波段数是否可读出？
      Q3 首条记录 / 首个像元是否可读取？

产出
    outputs/qa/audit_report.md          人读报告（含 PASS / FAIL 结论）
    outputs/qa/data_manifest_auto.csv   机器可读清单（url / doi 等栏留空待填）

用法
    python src/01_audit_inputs.py
    python src/01_audit_inputs.py --root data/raw --config config.yaml

设计约束
    - 不假设任何具体文件名：Dryad 包解压后长什么样它都能跑。
    - geopandas / rasterio 为可选依赖；缺失时降级为"仅记录未能验证"，不中断。
    - 不修改、不移动、不解压原始文件；zip 只读取目录。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:  # 允许在无 pyyaml 的精简环境中运行
    yaml = None

CHUNK = 1 << 20
VECTOR_EXT = {".shp", ".gpkg", ".geojson", ".json", ".kml"}
RASTER_EXT = {".tif", ".tiff", ".img", ".vrt"}
TABULAR_EXT = {".csv", ".tsv", ".parquet", ".xlsx", ".xls"}
TEXT_EXT = {".txt", ".md", ".log", ".dat"}
SIDECAR_EXT = {".dbf", ".shx", ".prj", ".cpg", ".sbn", ".sbx", ".qix", ".xml"}
INCOMPLETE_EXT = {".part", ".crdownload", ".download", ".tmp"}


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0
    return f"{n:.1f} TB"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def count_lines(path: Path) -> int:
    """按二进制分块计数换行符，1 GB 级文件也可在数秒内完成。"""
    count = 0
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            count += block.count(b"\n")
    return count


def probe_tabular(path: Path, notes: list[str]) -> dict:
    info: dict = {"type": "tabular"}
    try:
        import pandas as pd
    except ImportError:
        notes.append("pandas 不可用，跳过表结构检查")
        return info
    suffix = path.suffix.lower()
    try:
        if suffix == ".parquet":
            try:  # 只读元数据，避免把大文件读进内存
                import pyarrow.parquet as pq

                pf = pq.ParquetFile(path)
                info["rows"] = pf.metadata.num_rows
                info["n_columns"] = pf.metadata.num_columns
                info["columns"] = pf.schema_arrow.names[:15]
                return info
            except Exception:
                pass  # 退回 pandas 方式
        if suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(path, nrows=5)
            info["rows"] = "excel（未全量计数）"
        elif suffix == ".parquet":
            df = pd.read_parquet(path).head(5)
            info["rows"] = "parquet（未全量计数）"
        else:
            sep = "\t" if suffix == ".tsv" else ","
            df = pd.read_csv(path, nrows=5, sep=sep, low_memory=False)
            info["rows"] = count_lines(path)
        info["columns"] = list(df.columns)[:15]
        info["n_columns"] = len(df.columns)
        info["first_row"] = {k: str(v) for k, v in df.iloc[0].to_dict().items()} if len(df) else {}
    except Exception as exc:  # 读取失败本身就是审计结论
        notes.append(f"读取失败：{type(exc).__name__}: {exc}")
    return info


def probe_raster(path: Path, notes: list[str]) -> dict:
    info: dict = {"type": "raster"}
    try:
        import rasterio
    except ImportError:
        notes.append("rasterio 不可用，跳过栅格检查（环境未装好）")
        return info
    try:
        with rasterio.open(path) as ds:
            info.update(
                driver=ds.driver,
                width=ds.width,
                height=ds.height,
                bands=ds.count,
                dtype=str(ds.dtypes[0]),
                crs=str(ds.crs),
                nodata=ds.nodata,
                bounds=[round(v, 4) for v in ds.bounds],
            )
            arr = ds.read(1, window=((0, 1), (0, 1)))
            info["first_pixel"] = float(arr[0][0])
    except Exception as exc:
        notes.append(f"打开失败：{type(exc).__name__}: {exc}")
    return info


def probe_vector(path: Path, notes: list[str]) -> dict:
    info: dict = {"type": "vector"}
    try:
        import geopandas as gpd
    except ImportError:
        notes.append("geopandas 不可用，跳过矢量检查（环境未装好）")
        return info
    try:
        gdf = gpd.read_file(path, rows=5)
        info["columns"] = list(gdf.columns)[:15]
        info["crs"] = str(gdf.crs)
        info["bounds"] = [round(v, 3) for v in gdf.total_bounds]
        try:  # 有 pyogrio 时取真实要素数
            import pyogrio

            info["features"] = int(pyogrio.read_info(path)["features"])
        except Exception:
            info["features"] = "未计数（仅读了前 5 行）"
        if len(gdf):
            geom = gdf.geometry.iloc[0]
            info["first_geometry_type"] = geom.geom_type if geom is not None else None
    except Exception as exc:
        notes.append(f"读取失败：{type(exc).__name__}: {exc}")
    return info


def compile_verdict(size: int, info: dict, notes: list[str], min_bytes: int) -> tuple[str, list[str]]:
    """按 D0 三问给出 PASS / FAIL / NA 及原因。"""
    if info.get("type") == "sidecar":
        return "NA", ["矢量数据的附属文件，不单独判定"]
    reasons: list[str] = []
    if size < min_bytes:
        reasons.append("Q1 体积过小，疑为占位或下载中断")
    if info.get("type") == "archive" and info.get("members"):
        return ("PASS" if not reasons else "FAIL", reasons)
    readable = any(
        k in info for k in ("rows", "bands", "features", "members", "first_pixel", "columns", "first_line")
    )
    if not readable:
        reasons.append("Q2/Q3 未能读出结构或首条记录")
    if any("失败" in n for n in notes):
        reasons.append("Q3 读取错误")
    return ("PASS" if not reasons else "FAIL", reasons)


def main() -> int:
    ap = argparse.ArgumentParser(description="数据审计与 D0 自检")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--root", default=None, help="默认取 config.paths.raw")
    args = ap.parse_args()

    cfg: dict = {}
    if Path(args.config).exists():
        if yaml is None:
            print("[warn] 未安装 pyyaml，使用默认参数")
        else:
            cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}

    paths = cfg.get("paths", {})
    raw = Path(args.root or paths.get("raw", "data/raw"))
    qa_dir = Path(paths.get("qa", "outputs/qa"))
    min_bytes = int(cfg.get("qa", {}).get("min_file_bytes", 1024))
    qa_dir.mkdir(parents=True, exist_ok=True)

    if not raw.exists():
        print(f"[FAIL] 目录不存在：{raw.resolve()}")
        print("       请先创建 data/raw 并将下载文件放入其中。")
        return 2

    files = sorted(p for p in raw.rglob("*") if p.is_file())
    if not files:
        print(f"[FAIL] {raw} 为空：尚未下载任何数据，D0 无法通过。")
        return 2

    records = []
    for p in files:
        rel = p.relative_to(raw).as_posix()
        size = p.stat().st_size
        notes: list[str] = []
        ext = p.suffix.lower()

        if ext in INCOMPLETE_EXT:
            notes.append("下载未完成的临时文件")
            info = {"type": "incomplete"}
        elif ext in SIDECAR_EXT:
            notes.append("矢量数据的附属文件，不单独审计")
            info = {"type": "sidecar"}
        elif ext == ".zip":
            info = {"type": "archive"}
            try:
                import zipfile

                with zipfile.ZipFile(p) as zf:
                    members = zf.infolist()
                    info["members"] = len(members)
                    info["uncompressed_bytes"] = sum(m.file_size for m in members)
                    info["top_members"] = [
                        {"name": m.filename, "bytes": m.file_size}
                        for m in sorted(members, key=lambda m: -m.file_size)[:10]
                    ]
            except Exception as exc:
                notes.append(f"无法读取压缩包目录：{type(exc).__name__}: {exc}")
        elif ext in RASTER_EXT:
            info = probe_raster(p, notes)
        elif ext in VECTOR_EXT:
            info = probe_vector(p, notes)
        elif ext in TABULAR_EXT:
            info = probe_tabular(p, notes)
        elif ext in TEXT_EXT:
            info = {"type": "text"}
            try:
                with p.open("r", encoding="utf-8", errors="replace") as fh:
                    info["first_line"] = fh.readline().strip()[:200]
            except Exception as exc:
                notes.append(f"读取失败：{type(exc).__name__}: {exc}")
        else:
            info = {"type": "unknown"}
            notes.append("扩展名未识别，未做结构检查")

        verdict, reasons = compile_verdict(size, info, notes, min_bytes)
        records.append(
            dict(
                path=rel,
                bytes=size,
                sha256=sha256_of(p),
                verdict=verdict,
                reasons=reasons,
                notes=notes,
                info=info,
            )
        )

    # ---- 报告 ----
    n_pass = sum(1 for r in records if r["verdict"] == "PASS")
    n_fail = sum(1 for r in records if r["verdict"] == "FAIL")
    n_na = len(records) - n_pass - n_fail
    lines = [
        "# 数据审计报告（D0 自检）",
        "",
        f"- 生成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- 审计目录：`{raw.as_posix()}`",
        f"- 文件数：{len(records)}（PASS {n_pass} / FAIL {n_fail} / NA {n_na}）",
        "",
        "| 文件 | 体积 | 结论 | 结构摘要 | 备注 |",
        "|---|---:|---|---|---|",
    ]
    for r in records:
        info = r["info"]
        summary = []
        if "rows" in info:
            summary.append(f"行 {info['rows']}")
        if "n_columns" in info:
            summary.append(f"列 {info['n_columns']}")
        if "bands" in info:
            summary.append(f"{info['width']}×{info['height']} / {info['bands']} 波段 / {info['dtype']}")
            summary.append(f"CRS {info.get('crs')}")
        if "features" in info:
            summary.append(f"要素 {info['features']} / CRS {info.get('crs')}")
        if info.get("type") == "archive" and info.get("members"):
            summary.append(f"包内 {info['members']} 项 / {human(info['uncompressed_bytes'])}")
        note = "；".join(r["reasons"] + r["notes"])
        lines.append(
            f"| `{r['path']}` | {human(r['bytes'])} | **{r['verdict']}** | {'；'.join(summary) or '—'} | {note or '—'} |"
        )
    lines += ["", "## 逐文件明细", ""]
    for r in records:
        lines += [f"### {r['path']}", "", "```json", json.dumps(r["info"], ensure_ascii=False, indent=2), "```", ""]

    report = qa_dir / "audit_report.md"
    report.write_text("\n".join(lines), encoding="utf-8")

    manifest = qa_dir / "data_manifest_auto.csv"
    import csv as _csv

    with manifest.open("w", encoding="utf-8", newline="") as fh:
        w = _csv.writer(fh)
        w.writerow(["url", "doi", "version", "downloaded_at", "bytes", "sha256", "license", "local_path"])
        for r in records:
            w.writerow(["", "", "", "", r["bytes"], r["sha256"], "", r["path"]])

    print(f"\n报告：{report.resolve()}")
    print(f"清单：{manifest.resolve()}")
    print(f"结论：{n_pass} PASS / {n_fail} FAIL / {n_na} NA")
    for r in records:
        if r["verdict"] == "FAIL":
            print(f"  [FAIL] {r['path']} — {'；'.join(r['reasons'] + r['notes'])}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
