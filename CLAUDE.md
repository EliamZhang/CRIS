# CLAUDE.md — CRIS 项目索引

> 消费金融风控知识库 + 工具代码库。查找任何内容前，先看本文件定位，再打开对应目录。

## 项目概述

本仓库包含三大部分：

| 目录 | 内容 | 说明 |
|------|------|------|
| [工具包/](工具包/) | 风控规则分析 Python 工具包（rulelift，8 个子项目） | 可运行的代码，统一 `python run.py` 入口 |
| [方法论/](方法论/) | 风控方法论知识库（docx/xlsx/md） | 含独立的 [CLAUDE.md](方法论/CLAUDE.md) 索引 |
| [课程资料/](课程资料/) | 外部课程资料（PDF 课件、图片、实操代码） | 7 个篇目，含已解压的 ipynb 与数据 |

另有 `draft/`（策略文档草稿）与 `draft/rulelift/`（工具包相关草稿）。

---

## 一、工具包（rulelift）

路径：`工具包/`

8 个独立的风控规则分析子项目（`10_` ~ `17_`），每个可单独运行：

| 子项目 | 作用 |
|--------|------|
| `10_univariate_rule_generation` | 单变量候选规则生成 |
| `11_rule_crosstab_analysis` | 双变量交叉分析 |
| `12_decision_tree_rule_mining` | 决策树规则挖掘 |
| `13_lending_club_tree_rule_mining` | Lending Club 场景树规则挖掘 |
| `14_ruleset_performance_evaluation` | 规则集性能评估 |
| `15_rule_d_class_tuning` | 规则 D 类调优 |
| `16_strategy_d_class_tuning` | 策略新增评估 |
| `17_strategy_replacement_tuning` | 策略置换评估 |

**约定**：
- 统一入口 `python run.py`，结果汇总在各自 `output/summary_report.xlsx`
- 业务逻辑在 `src/*.py`；输入放 `input/`；运行后 csv 会被清理
- 大文件不入库：`input/lending_club_loan_two.csv` 等在 `.gitignore` 中
- 细节见 [工具包/README.md](工具包/README.md) 及各子项目 README

---

## 二、方法论知识库

路径：`方法论/`

文档格式：`.docx` 正文 + `.xlsx` 配套数据 + `.md` 专题深度文档。**完整索引见 [方法论/CLAUDE.md](方法论/CLAUDE.md)**，涵盖：

- `信贷全流程方法论/`：基础版（10 模块 docx+xlsx）
- `信贷全流程方法论 - 增强版/`：内容更详细的增强版
- `核心指标监控/`：风控指标监控文档与测算 Excel
- `策略开发及优化/`：4 个核心 md（策略开发方法论、策略调优方法论、贷前策略与产品设计、贷中策略方法论）
- `产品介绍/`：产品介绍方法论（最近提交涉及）

---

## 三、课程资料

路径：`课程资料/`

外部课程《100天成为风控专家》的学习资料，按主题分 7 个篇目：

| 篇目 | 主要内容 |
|------|----------|
| `01-信贷业务与风控场景` | 信贷业务介绍/场景/岗位/机构（整理 md） |
| `02-策略开发与规则体系` | 规则认识、规则生成（单变量/交叉表/决策树）、规则集、性能测试 |
| `03-策略调优与A-D类优化` | 调优方法论、A类/D类调优、拒绝回捞、客群下探、策略置换 |
| `04-报表分析与资产质量监控` | Vintage 报表、迁徙率报表 |
| `05-风控评估指标体系` | Lift、PSI、KS、AUC、CSI 指标 |
| `06-评分卡模型篇` | 模型设计/开发/变量筛选/分箱/WOE/逻辑回归/校准/监控等 17 个专题 |
| `07-机器学习模型篇` | Optuna+LGBM 调参、SHAP 解释、模型部署 |

**目录约定**（各篇目内）：
- `NN-主题/`：PDF 课件 + 已解压的实操代码（ipynb + 数据文件）
- `NN-主题-图片/`：PDF 逐页拆出的单页 PNG（150 DPI）
- `NN-主题-合并图片/`：单页图合成的大图（每张含 2~6 页，带红色页码标注）
- 顶层常有 `.md` 专题综述文件（如 `信贷业务体系与风控场景_专题综述.md`）

**已知事项**：
- 超大文件（>40MB 数据文件，如 951MB 的 repay_plan_data_new.csv）在 `.gitignore` 中，不入库
- 课程资料目前只在 `feature/课程资料-图片与解压文件` 分支，main 分支没有
- 部分 PDF 是纯图片型（如 03-岗位职能），文本需 OCR（Tesseract 已安装，中文包在 `~/tessdata/`）

---

## 四、draft（草稿）

路径：`draft/`

策略开发/调优/贷前/贷中/规则开发等文档的草稿与合并版；`draft/rulelift/` 为工具包相关草稿。正式整理后的文档在 `方法论/策略开发及优化/`。

---

## 五、常用操作

- **PDF → 图片**：`fitz`（PyMuPDF）逐页渲染 PNG；合并大图用 Pillow 网格拼接（参考各 `-合并图片/` 目录的生成方式）
- **zip 解压**：中文文件名 zip 需 GBK 修复（`raw.encode("cp437").decode("gbk")`）后用 zipfile 解压
- **图片型 PDF 转文本**：Tesseract OCR，`TESSDATA_PREFIX=$HOME/tessdata`，`pytesseract` + 灰度放大预处理
- **git**：当前活跃分支 `feature/课程资料-图片与解压文件`；main 为发布主线
