[log.md](https://github.com/user-attachments/files/34476652/log.md)
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
| 11/06 | C（Liu Mingjing） | 交付 story line 与 8 页 PPT 大纲：三段式单线叙事；8 页合计 395 秒，第 3—6 页合计 215 秒（占 51.2%），与 35% 实验设计 + 20% 方法两项对齐 | 讲稿目标 6:40，第 5 页 65 秒为最长；大纲已并入 README |
| 11/06 | C（Liu Mingjing） | 已确认：两份评分标准已取得，不强制要求回归或预测，范围无需扩展；展示为 12/02 第 8 个出场，地点 6A609；GitHub 已邀请其余两名成员 | 环境与数据尚未开始，D0 于今日 23:00 执行 |
| 11/06 | B（Li Luoyang） | 完成 6 单元人工算例与 `tests_equity.py`：均匀供给、单区供给两例通过，共 12 项断言；M3/M4 计算内核置于 `src/equity_desert.py`（数字开头的模块名无法被 import，故与 `04_equity_desert.py` 拆开）；本机实测 Python 3.12.7 + pandas 2.2.2，无 geopandas（M3/M4 不需要） | 11/08 口径卡待拍板的六项见 `handoff/2026-11-07/manual_example_6u.md` §10；G1 前须与 A 确认 `accessibility` 字段口径（含 `d0`、站覆盖标记、边界标记） |
