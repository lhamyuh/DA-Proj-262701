# log

记录格式：`日期 | 成员 | 事项 | 影响 / 待办`。按时间顺序追加；同一日多项事项可合并为一条。
口径、阈值、数据版本与重交规则的变更，行首标注 `[口径]`。

| 日期 | 成员 | 事项 | 影响 / 待办 |
|---|---|---|---|
| 11/05 | 全员 | 计划定稿：范围冻结为 M1—M5；展示场次确定为 12/02（周三） | 按计划 §5 分工启动 |
| 11/05 | A（YANG Linyu） | 本机环境实测：`python` 为 3.8.1，未安装 geopandas；C 盘余 18.3 GB，D 盘余 39.4 GB | 11/06 建立 `ev311` 环境并执行 D0 自检 |
| 11/05 | 全员 | 在 AutoDL 容器 `/root` 下误执行 `git init`；`commit` 因未配置身份失败，`push` 因无引用失败，未推送任何内容；已执行 `rm -rf /root/.git` 撤销 | 改在 Windows 课程目录以 `git init -b main` 重建仓库 |
| 11/05 | 全员 | 建立 OneDrive 共享文件夹与 GitHub 私有仓库 https://github.com/lhamyuh/DA-Proj-262701；数据存放位置改为项目内 `data/`（已加入 `.gitignore`） | 三人完成 clone/push 与云盘访问测试 |
| 11/06 | 全员 | 成员代号实名化：A＝YANG Linyu、B＝Li Luoyang、C＝Liu Mingjing；同步更新 README「分工」表与检查表负责人列；GitHub 协作者姓名按此核对 | 后续 log 记录统一使用「代号（姓名）」格式 |
| 11/06 | C（Liu Mingjing） | 交付评分项—证据—负责人—完成状态检查表：展示 5 项（15+10+20+35+20）+ 报告 4 项（30+35+15+20），共 9 行；每行含证据、负责人、完成状态、对应页 | 检查表已并入 README；状态栏为 11/06 当日口径，不得出现预期数值，11/16 冻结后由 C 回填 |
| 11/06 | C（Liu Mingjing） | 交付 story line 与 8 页 PPT 大纲：三段式单线叙事；8 页合计 395 秒，第 3—6 页合计 **230 秒（占 7 分钟的 54.8%）**，与 35% 实验设计 + 20% 方法两项对齐 | 讲稿目标 6:40，第 5 页 65 秒为最长；大纲已并入 README。原文记为“215 秒 / 51.2%”，与逐页相加不符，已按表值更正 |
| 11/06 | C（Liu Mingjing） | 已确认：两份评分标准已取得，不强制要求回归或预测，范围无需扩展；展示为 12/02 第 8 个出场，地点 6A609；GitHub 已邀请其余两名成员 | 环境与数据尚未开始，D0 于今日 23:00 执行 |
| 11/06 | B（Li Luoyang） | 完成 6 单元人工算例与 `tests_equity.py`：均匀供给、单区供给两例通过，共 12 项断言；M3/M4 计算内核置于 `src/equity_desert.py`（数字开头的模块名无法被 import，故与 `04_equity_desert.py` 拆开）；本机实测 Python 3.12.7 + pandas 2.2.2，无 geopandas（M3/M4 不需要） | 11/08 口径卡待拍板的六项见 `handoff/2026-11-07/manual_example_6u.md` §10；G1 前须与 A 确认 `accessibility` 字段口径（含 `d0`、站覆盖标记、边界标记） |
| 11/06 | A（YANG Linyu） | 建立 `ev311`（python 3.11.15）。conda 22.11.1 的经典求解器误装 geopandas 0.9.0（依赖 shapely 的 `cascaded_union`，shapely 2 已删除）与 rasterstats 0.14.0，导致导入失败；已用 pip 升级为 geopandas 1.2.0 / rasterstats 0.21.0 / pyogrio 0.13.0 | 导入检查通过；新增 `activate_env.ps1` 设置 GDAL_DATA 与 PROJ_LIB，消除 gdalvrt.xsd 警告 |
| 11/06 | A（YANG Linyu） | **D0 判定：环境项通过，数据项未通过**。`data/raw` 为空，尚未开始下载 | 11/07 09:00 前站点表必须到手；G1 仍按 11/07 17:00；若 12:00 仍未到手，通报全组并启用备选源或 1 km 人口档 |
| 11/06 | 全员 | `README.md` 与 `log.md` 首行各有一条来自聊天附件的残留链接，已删除 | 后续同步文件请直接覆盖正文，勿带入附件链接 |
| 11/06 | 全员 | 更正 `README.md` 两处数值：① 展示页第 3—6 页合计由“215 秒 / 51.2%”改为“230 秒 / 54.8%”；② 数据评分项中“UrbanEV 9985 站点／563 节”无来源，改为“原始 1,682 站（处理后 1,362 站），样本为 275 个 TAZ” | 请 C 复核 ①、B 复核 ②；后续引用数据集规模一律标注来源 |
| 11/10 | A（YANG Linyu） | **数据获取完成**：Dryad 包 305.4 MB（结构：外层 zip 含 `UrbanEVDataset.zip` + README 数据字典）、七普 100 m 人口 132.2 MB（Figshare，RAR，bsdtar 可解）、深圳区界 69 KB（DataV）。仅解出 6 个静态表（1.7 MB），未解压 1,682 个逐站 CSV（4.9 GB，动态分析已删不需要） | 审计：4 个文件全 PASS |
| 11/10 | A（YANG Linyu） | **G1 锁定：路线 B（1 km 格网）**。依据：数据集**无任何 TAZ 多边形**，仅有质心与面积，无法做 TAZ 级人口聚合；不采用 Voronoi。研究区 = 市界内 ∩ 距 TAZ 质心 ≤1.4 km（按 275 区面积合计 982.5 km² 标定） | 结论见 `outputs/qa/g1_conclusion.md`；G1 逾期 3 天 |
| 11/10 | A（YANG Linyu） | **M1 完成**：`station_master`（1,682 站）、`zone_master`（市域 2,127 格网，含 in_study 949）、QA 报告。校验：市域人口 17,446,224 vs 七普 1,756 万（偏差 0.6%）；研究区人口 1,450 万（83.1%）；区内站 1,562 / 桩 22,818 | M1 原定 11/09，实际 11/10 |
| 11/10 | A（YANG Linyu） | **M2 完成**：Gaussian-2SFCA 三套半径（1/3/5 km）。区内中位可达性 0.00063 / 0.00134 / 0.00139 桩·人⁻¹；3 km 下 7 个格网半径内无站点 | M2 原定 11/11，提前 1 天 |
| 11/10 | A（YANG Linyu） | 修正一处方法错误：初版把需求集限定在研究区、供给却含区外站点，导致边缘站供需比被放大（A_i 在 3→5 km 出现 8 倍跳变）；改为需求集用市域全部 2,127 格网 | 现 A_i 中位 1.34 桩/千人与全市 1.43 一致 |
| 11/10 | A（YANG Linyu） | 交付给 B 的交接包 `handoff/2026-11-10/`（zone_master.csv、accessibility.csv、station_master.csv、README、sha256.txt） | B 可开始 M3/M4；只使用 `in_study == True` |
| 11/10 | A（YANG Linyu） | 记录两个技术坑：① `rasterio.transform.rowcol/from_bounds` 在本环境硬崩溃（0xC06D007F），须手算窗口偏移；② TAZ 为点几何，`geometry.area` 恒为 0，面积须取表内 `area` 字段 | 已写入脚本注释 |
| 11/10 | A（YANG Linyu） | 研究区加入孔洞填充：1.4 km 缓冲并集在城区内部留有空洞，被排除的常住人口不合规；改为在区界内做 `binary_fill_holes`（只填内部空洞、不外扩），研究区由 949 → **997 格网**，人口覆盖由 83.1% → **84.4%** | 后续统计以 997 为准；B 的交接包已同步更新 |
| 11/10 | A（YANG Linyu） | **matplotlib 崩溃的根因是 MKL 线程层**（见下），不是 matplotlib 自身；修复后 matplotlib 可用，但 Fig1/Fig2 已用 Pillow 渲染完成，不再重做 | 若需重出图，先执行 `.\activate_env.ps1` |
| 11/10 | A（YANG Linyu） | **Fig1、Fig2 出图完成**（300 dpi，`outputs/figures/`）；站点 QA 完成：1,682 站全部落在市界内、无零坐标、125 组共址（264 站） | Fig1/Fig2 原定 11/13，提前 3 天 |
| 11/10 | A（YANG Linyu） | 交付 `report/sections/a_data_methods.md`：数据段与 2SFCA 方法段（中英各 ≤250 字）、Fig1/Fig2 图注、地图讲解要点 5 条、站点 QA 摘要 | 原定 11/15，提前 5 天；C 可直接取用 |
| 11/10 | A（YANG Linyu） | **环境根因找到**：本机 Intel MKL 线程层与 numpy 2.4 冲突，任何进入 BLAS 的调用（`np.corrcoef`、`np.dot`、matplotlib 绘图、部分 pandas 分组）会以 0xC06D007F 直接崩溃且无 traceback。**解法：`MKL_THREADING_LAYER=SEQUENTIAL`**（已写入 `activate_env.ps1`；`GNU` 无效） | 全组按此设置；此前 matplotlib“不可用”的结论应修改为“未设 SEQUENTIAL 时崩溃” |
| 11/10 | A（YANG Linyu） | 分环统计（距人口加权重心）：每千人桩数中位数 0–3 km **0.98**、3–6 km 0.95、6–10 km 1.26、10–15 km **1.65**、15–25 km 1.28、>25 km 1.32；人口与每千人桩数的 Spearman 相关仅 **0.20**。即核心区桩最密但人均最低 | 成为幻灯片首条实证结论；表见 `outputs/tables/a_ring_profile.csv` |
| 11/10 | A（YANG Linyu） | 最低 20% 可达性格网 = **200 个**，涉及人口 **2,023,405**；格网内无站但 3 km 内有站的有 530 个（再次证明不能用 `n_stations` 判覆盖） | 供 B 的 M3 对照；B 算出并集后应与 200 万量级一致 |
| 11/10 | A（YANG Linyu） | **A 独立工作范围全部完成**：M1、M2、Fig1、Fig2、方法段、站点 QA、交接包、分环统计表。后续由 B 接 M3/M4 | A 在 11/16 G2 前只做复核与答疑 |
