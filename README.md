# Shenzhen EV Charging Deserts — 项目总览

**题目：** Spatial Accessibility and Equity Assessment of Public EV Charging Deserts: A Case Study of Shenzhen
**课程：** Data Analytics（CUHKSZ AY2026-27 Term 1）｜团队 3 人｜C 主讲，A 替补，三人到场
**关键日期：** 11/21 20:00 内部上传｜11/22 23:59 幻灯片截止｜12/02 现场展示｜12/18 23:59 报告截止
**代码仓库：** https://github.com/lhamyuh/DA-Proj-262701
**共享云盘：** 校内 OneDrive 共享文件夹（已建立）

## 当前节点

数据获取阶段：D0 环境与数据自检（11/06 23:00）→ G1 数据冻结（11/07 17:00）

## 分工

| 成员 | 职责 | 主要产出 |
|---|---|---|
| A | 空间数据、人口聚合、2SFCA、地图 | `src/01—03`、Fig1、Fig2 |
| B | 荒漠识别、人口加权公平性、数值冻结 | `src/04`、Fig3、表 1、`numbers_frozen.md` |
| C | 统筹、幻灯片、讲稿、主讲、报告统稿 | `slides/`、讲稿、报告 |

## 执行顺序

```powershell
conda activate ev311
python src/01_audit_inputs.py        # 数据审计 → outputs/qa/
python src/02_spatial_population.py  # 人口聚合 → zone_master
python src/03_accessibility.py       # 2SFCA → accessibility
python src/04_equity_desert.py       # 荒漠与公平性 → 表
python src/05_export_figures.py      # 出图 → outputs/figures/
```

## 文件位置

| 内容 | 位置 |
|---|---|
| 代码、小表、图、PDF 快照 | 本仓库（GitHub 私有） |
| 原始数据 | `data/raw/`（仅 A 的机器上有内容，已被 `.gitignore` 忽略，不入库） |
| 幻灯片与报告 | OneDrive 共享文件夹 |
| 每日记录 | `log.md` |
| 唯一数值来源 | `numbers_frozen.md`（11/16 冻结） |
| 完整计划 | `Shenzhen_UrbanEV_Project_Plan.md` |

## 三项约束

1. 不得将数据或幻灯片提交至 Git；原始数据仅存放于 `data/`。
2. 数值修改须先更新 `numbers_frozen.md`，不得在 PowerPoint 中直接修改。
3. 分析范围已冻结为 M1—M5，不新增模块。
