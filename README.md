# Shenzhen EV Charging Deserts — 项目总览

**题目：** Spatial Accessibility and Equity Assessment of Public EV Charging Deserts: A Case Study of Shenzhen
**课程：** Data Analytics（CUHKSZ AY2026-27 T1）｜3 人｜C 主讲，A 替补，三人到场
**关键日期：** 11/21 20:00 内部上传｜11/22 23:59 slides 截止｜12/02 展示｜12/18 23:59 报告截止

## 现在在哪一步

阶段：**数据获取**（D0 闸门 11/06 23:00 → G1 数据冻结 11/07 17:00）

## 三个人各管什么

| 人 | 职责 | 主要产出 |
|---|---|---|
| A | 空间数据、人口聚合、2SFCA、地图 | `src/01—03`、Fig1、Fig2 |
| B | 荒漠识别、人口加权公平性、数值冻结 | `src/04`、Fig3、表 1、`numbers_frozen.md` |
| C | 统筹、slides、讲稿、唯一主讲、报告统稿 | `slides/`、讲稿、报告 |

## 怎么跑

```powershell
conda activate ev311
python src/01_audit_inputs.py        # 数据审计 → outputs/qa/
python src/02_spatial_population.py  # 人口聚合 → zone_master
python src/03_accessibility.py       # 2SFCA → accessibility
python src/04_equity_desert.py       # 荒漠 + 公平性 → 表
python src/05_export_figures.py      # 出图 → outputs/figures/
```

## 文件在哪

| 内容 | 位置 |
|---|---|
| 代码、小表、图、PDF 快照 | 本仓库（GitHub 私有） |
| 原始数据 | `E:\EV_Shenzhen\raw`（只在 A 的机器上，不入库） |
| pptx / 报告 docx | OneDrive 共享夹 |
| 每天发生了什么 | `log.md` |
| 唯一数字来源 | `numbers_frozen.md`（11/16 冻结） |
| 完整计划 | `Shenzhen_UrbanEV_Project_Plan.md` |

## 三条不要做

1. 不要把数据或 pptx 提交进 Git（`.gitignore` 已设）。
2. 不要在 PowerPoint 里直接改数字——先改 `numbers_frozen.md`。
3. 不要新增分析（范围已冻结在 M1—M5）。
