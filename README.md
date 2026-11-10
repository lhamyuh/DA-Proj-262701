# Shenzhen EV Charging Deserts — 项目总览

**题目：** Spatial Accessibility and Equity Assessment of Public EV Charging Deserts: A Case Study of Shenzhen
**课程：** Data Analytics（CUHKSZ AY2026-27 Term 1）｜团队 3 人｜C 主讲，A 替补，三人到场
**关键日期：** 11/21 20:00 内部上传｜11/22 23:59 幻灯片截止｜**12/02 现场展示（第 8 个出场，6A609）**｜12/18 23:59 报告截止
**评分标准：** 两份 rubric 已取得，不强制要求回归或预测分析
**代码仓库：** https://github.com/lhamyuh/DA-Proj-262701（已邀请其余两名成员）
**共享云盘：** 校内 OneDrive 共享文件夹（已建立）

## 当前节点

数据获取阶段。**D0 结果（11/06 23:00）：环境项通过，数据项未通过**（`data/raw` 为空）。环境已可用：python 3.11.15 / geopandas 1.2.0 / rasterio 1.4.4 / rasterstats 0.21.0 / pandas 3.1.1 / numpy 2.4.6。
下一步：11/07 09:00 前站点表到手 → 17:00 交 G1 结论（路线 A/B、坐标可用性、人口档位、研究区）。

## 分工

| 成员 | 姓名 | 职责 | 主要产出 |
|---|---|---|---|
| A | **YANG Linyu** | 空间数据、人口聚合、2SFCA、地图 | `src/01—03`、Fig1、Fig2 |
| B | **Li Luoyang** | 荒漠识别、人口加权公平性、数值冻结 | `src/04`、Fig3、表 1、`numbers_frozen.md` |
| C | **Liu Mingjing** | 统筹、幻灯片、讲稿、主讲、报告统稿 | `slides/`、讲稿、报告 |

## 执行顺序

> 说明：`01_audit_inputs.py` 已建立；`02—05` 按计划 §5 的交付日逐项补齐。**PowerShell 未配置 `conda init`，请用绝对路径或先执行 `.\activate_env.ps1`。**

```powershell
.\activate_env.ps1                        # 设置 GDAL_DATA / PROJ_LIB 并自检版本
& "D:\miniconda3\envs\ev311\python.exe" src\01_audit_inputs.py        # 数据审计 → outputs/qa/
& "D:\miniconda3\envs\ev311\python.exe" src\02_spatial_population.py  # 人口聚合 → zone_master
& "D:\miniconda3\envs\ev311\python.exe" src\03_accessibility.py       # 2SFCA → accessibility
& "D:\miniconda3\envs\ev311\python.exe" src\04_equity_desert.py       # 荒漠与公平性 → 表
& "D:\miniconda3\envs\ev311\python.exe" src\05_export_figures.py      # 出图 → outputs/figures/
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

## 评分项—证据—负责人—完成状态检查表

依据两份评分文件：展示评分（100% = 15+10+20+35+20）与报告评分（100% = 30+35+15+20）。「完成状态」按 11/06 当日口径填写，后续由 C 在 story line 页与每页脚注持续维护；所有数值性结论须能在 `numbers_frozen.md`（11/16 20:00 冻结）中追溯到脚本输出。本表即 §1.1，与计划正文同源，版本号随计划同步（当前 v4.2）。

**核验规则：** 任一评分项的证据须同时落在 §5 的交付行与 §7 的页面规格里，三者不一致时以本表为准，并在 `log.md` 登记偏差来源与处理决定。本表不得与 `Shenzhen_UrbanEV_Project_Plan.md` 分叉维护。

### 展示评分（5 项）

| 评分项（权重） | 本组证据 | 负责人 | 姓名 | 完成状态 | 对应页 |
|---|---|---|---|---|---|
| Introduction & Clarity of Topic — 问题动机、目标、显著性（15%） | 三研究问题 + 深圳人口 1700 万量级 × 充电桩空间错配的现实矛盾；荒漠识别与公平性测度的学术缺口 | C | Liu Mingjing | 待 11/07 G1 锁定路线后定稿 | §1 |
| Dataset, Preprocessing & Analysis — 数据来源、处理流程、分析口径（10%） | UrbanEV 原始 1,682 站（处理后 1,362 站），非全市普查；本研究样本为筛选后 275 个 TAZ（路线 B 下为规则格网）；`data_manifest.csv` 逐条登记 DOI／版本／sha256；`qa_report.md` 记录 CRS 与覆盖率 | A | YANG Linyu | 待 11/09 三张主表交付 | §2 |
| Methodology & Technical Soundness — 方法、技术实现、理论依据（20%） | Gaussian-2SFCA 完整公式推导：g(d) 归一化 Gaussian 核、R_j 零分母剔除、A_i 单位统一为 每千人桩数；两类荒漠定义（无覆盖 + 相对低可达） | A ／ B | YANG Linyu ／ Li Luoyang | 待 11/07 G1 路线锁定 | §3 |
| Experiment Design & Results — 实验设计、评估指标、结果、可行性讨论（35%） | 1／3／5km 三套可达性；三类敏感性（半径、阈值、口径）；人口加权 Gini + Lorenz + 最低 20% 群体指标 + P10 四项并列 | A ／ B | YANG Linyu ／ Li Luoyang | 待 11/16 `numbers_frozen.md` 冻结 | §4—6 |
| Delivery, Q&A & Engagement — 表达、视觉、问答、观众投入度（20%） | 7 分钟严格计时；40 题问答库（A／B 各 10 问 + C 兜底 20 问）；实际场地 11/30 演练录像；11/25 旁听别组收集提问类型 | C | Liu Mingjing | 进行中（11/06—11/21 阶段） | §5 讲稿 + Q&A |

### 报告评分（4 项，12/03 起，C 统稿）

| 报告评分项 | 证据 | 负责人 | 姓名 |
|---|---|---|---|
| Organization & Academic Writing（30%） | Heading 1／2／3 三级 + 双栏 A4 模板 | C | Liu Mingjing |
| Technical Depth & Analysis（35%） | IV Results 合并 A 的地图与 B 的数值；III Methods 分开署名 | A + B | YANG Linyu + Li Luoyang |
| Figures & References（15%） | Fig1—Fig3 图注含年份／样本边界／单位；10—12 篇文献带页码 | A + C | YANG Linyu + Liu Mingjing |
| Originality（20%） | 两类荒漠并集去重 + 站／桩分报 + 未观测区域不赋值零供给 | 全员 | YANG Linyu ／ Li Luoyang ／ Liu Mingjing |

## 三项约束

1. 不得将数据或幻灯片提交至 Git；原始数据仅存放于 `data/`。
2. 数值修改须先更新 `numbers_frozen.md`，不得在 PowerPoint 中直接修改。
3. 分析范围已冻结为 M1—M5，不新增模块。

## Story line（C 负责，11/07 前定稿）

**论证链（共 7 步）：**

1. 深圳公共充电总量在增长，但人口与设施存在空间错配。
2. 因此要看"人均可获得的桩"，而不是"桩的总数"。
3. 用 Gaussian-2SFCA 把供需拉到同一空间尺度。
4. 两类荒漠识别把"覆盖缺失"与"相对低可达"分开。
5. 人口加权 Gini 看分布是否公平。
6. 敏感性检验结论是否站得住。
7. 落到"先补哪"的政策优先序。

**一句话主线：** 不是深圳没桩，而是桩没长在人的地方；我们的判断标准是人口加权下的可达性分布，而不是设施总量。

## 8 页 PPT 大纲

| 页 | 标题 / 内容 | 时长 | 素材负责人 | 姓名 | 完成状态 |
|---|---|---|---|---|---|
| §1 | 题目、城市问题、三个研究问题 | 35 秒 | A | YANG Linyu | 占位待填，待 11/07 G1 后定稿 |
| §2 | 数据：年份、275 样本、人口代用指标、QA | 45 秒 | A | YANG Linyu | 待 11/09 三张主表交付 |
| §3 | 方法：2SFCA + 两类荒漠定义 | 55 秒 | A + B | YANG Linyu + Li Luoyang | 待 11/11（可达性）与 11/12（荒漠表） |
| §4 | 结果：可达性地图与空间差异 | 55 秒 | A | YANG Linyu | 待 11/13 成图 |
| §5 | 结果：荒漠人口、Gini 与 Lorenz | 65 秒 | B | Li Luoyang | 待 11/16 `numbers_frozen.md` 冻结 |
| §6 | 稳健性：1／5km 半径、10／30% 阈值 | 55 秒 | B | Li Luoyang | 待 11/16 `numbers_frozen.md` 冻结 |
| §7 | 政策含义与局限 | 55 秒 | C | Liu Mingjing | 待 11/17 v1 后补充 |
| §8 | 三个研究问题的回答（各一句） | 30 秒 | 全员 | YANG Linyu ／ Li Luoyang ／ Liu Mingjing | 待 12/01 G4 定版 |
| **合计** | 讲稿目标 6:40，留 25 秒页间过渡 | **395 秒** | — | — | — |

> 第 3—6 页合计 **230 秒**（55+55+65+55），占 7 分钟（420 秒）的 **54.8%**，对应展示评分中 Experiment Design & Results（35%）+ Methodology & Technical Soundness（20%）两项，是全篇重心。
> 注：此前本行写作“215 秒 / 51.2%”，与上表逐页相加不符，现按表内数值更正；230 秒亦满足计划 §7“第 3—6 页不少于 3 分钟”的要求。
