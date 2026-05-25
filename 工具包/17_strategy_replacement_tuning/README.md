# 17_strategy_replacement_tuning

## 项目定位

这是一个新旧策略替换分析项目。  
它关注的不是某一条规则，而是“新策略是否值得替换旧策略”。

相比 `15` 和 `16`，这个项目站得更高，回答的问题是：

- 新评分策略的通过率是否更高
- 新策略放过的人群风险如何
- 旧策略放过但新策略拒绝的人群风险如何
- 不同 cutoff / 旧等级拒绝组合下，哪种替换方案更优

## 适合解决的业务问题

- 能否用新风险分替代旧评分卡等级决策
- 新策略会带来多少通过率提升
- 新策略放进来的人是否风险可接受
- 哪组替换参数最值得业务讨论

## 方法论与实现原理

主逻辑位于 [src/strategy_replacement_tuning.py](/C:/Users/zhangyuliang02/Desktop/rulelift/17_strategy_replacement_tuning/src/strategy_replacement_tuning.py)，配置集中在 `AnalysisConfig`。

项目的核心思路是“新旧策略交叉矩阵 + 风险估算”。

### 1. 定义新旧策略拒绝逻辑

默认定义为：

- 新策略：`risk_score >= cutoff` 视为拒绝
- 旧策略：`card_level in reject_levels` 视为拒绝

### 2. 计算新旧策略交叉决策矩阵

项目会生成以下矩阵：

- 样本量矩阵
- 坏样本量矩阵
- 原始坏账率矩阵
- 通过率矩阵

其核心价值是把样本拆成四类：

- 新旧都通过
- 新旧都拒绝
- 旧拒绝但新通过
- 旧通过但新拒绝

### 3. 对旧拒绝但新通过的人群做风险估算

这是该项目最关键的方法论部分。

在很多真实业务样本里，“旧策略拒绝”的人往往没有真实表现标签，因为他们没有进入后续放款或贷后观察流程。  
为了解决这一问题，项目采用风险分分箱估算：

- 先在有表现样本中按 `risk_score` 分箱
- 计算每个风险分箱的历史坏账率
- 再将旧拒绝样本映射到对应风险分箱
- 用该箱体的历史坏账率估算其潜在坏样本数

这使得项目可以在“不完全可观测”的条件下，对策略替换做近似量化。

### 4. 做 cutoff / 旧拒绝等级组合 grid search

项目会自动搜索：

- 新分数 cutoff
- 旧等级 reject set

并输出排序结果。  
`grid_score` 会综合考虑：

- `pass_rate_uplift`
- 新放入样本的估算坏账率
- 被替换出去样本的历史坏账率

当前主流程和 grid search 已统一使用安全矩阵取值逻辑，避免在某些组合下因矩阵缺行缺列而崩溃。

## 输入数据契约

默认输入文件：

- `input/data_v5.xlsx`

支持格式：

- `xlsx`
- `xls`
- `csv`

必须包含字段：

- `sample_id`
- `sample_month`
- `risk_score`
- `card_level`
- `is_dlq_30d`

默认业务含义：

- `risk_score` 越高风险越高
- `card_level` 等级顺序默认按 `A -> B -> C -> D -> E`
- `is_dlq_30d = 1` 为坏样本
- 缺少表现标签的样本会被保留，用于新旧策略替换估算

## 输出结果与如何使用

核心结果文件：

- `output/summary_report.xlsx`

常用 sheet：

- `sample_overview`
  样本总览与有无标签情况
- `binning_detail_risk_score`
  新风险分分箱表现
- `binning_detail_card_level`
  旧等级分层表现
- `variable_binning_summary`
  变量分箱摘要
- `decision_matrix_bad_count_original`
  原始坏样本交叉矩阵
- `decision_matrix_total_count`
  原始样本量交叉矩阵
- `decision_matrix_bad_rate_original`
  原始坏账率交叉矩阵
- `decision_matrix_pass_rate`
  通过率交叉矩阵
- `reject_distribution_risk_score`
  旧拒绝样本在新风险分下的分布
- `replacement_estimation`
  旧拒绝样本估算坏样本数
- `decision_matrix_bad_count_after_replacement`
  替换估算后的坏样本矩阵
- `decision_matrix_bad_rate_after_replacement`
  替换估算后的坏账率矩阵
- `grid_search_results`
  全量搜索结果
- `grid_search_top_configs`
  推荐替换配置

辅助输出：

- `output/final_summary.json`
- `output/analysis_report.txt`
- `output/bad_rate_by_risk_score.png`
- `output/bad_rate_by_card_level.png`
- `output/replacement_estimation_by_risk_score_bin.png`
- `output/final_strategy_summary.png`

推荐阅读顺序：

1. `decision_matrix_pass_rate`
2. `decision_matrix_bad_rate_original`
3. `replacement_estimation`
4. `grid_search_top_configs`
5. `analysis_report.txt`

## 配置与可调参数

配置集中在：

- [src/strategy_replacement_tuning.py](/C:/Users/zhangyuliang02/Desktop/rulelift/17_strategy_replacement_tuning/src/strategy_replacement_tuning.py)
- `AnalysisConfig`

关键配置项：

| 配置项 | 默认值 | 作用 |
|---|---|---|
| `input_path` | `input/data_v5.xlsx` | 输入文件 |
| `output_dir` | `output` | 输出目录 |
| `sample_id_col` | `sample_id` | 样本 ID |
| `month_col` | `sample_month` | 月份字段 |
| `new_score_col` | `risk_score` | 新策略分数 |
| `old_card_col` | `card_level` | 旧策略等级 |
| `target_col` | `is_dlq_30d` | 标签列 |
| `new_score_reject_cutoff` | `6` | 新策略拒绝阈值 |
| `old_card_reject_levels` | `("D","E")` | 旧策略拒绝等级 |
| `risk_score_bins` | `(0,2,3,4,5,6,10)` | 风险分固定分箱 |
| `card_level_order` | `("A","B","C","D","E")` | 等级排序 |
| `save_plots` | `True` | 是否输出图 |
| `grid_min_score_cutoff` | `2` | 搜索最小 cutoff |
| `grid_max_score_cutoff` | `8` | 搜索最大 cutoff |
| `grid_top_n` | `20` | 推荐替换方案数量 |

命令行支持：

```bash
python run.py --input input/data_v5.xlsx --output output --score-cutoff 6 --old-reject-levels D,E
```

关闭图片输出：

```bash
python run.py --input input/data_v5.xlsx --output output --score-cutoff 6 --old-reject-levels D,E --no-plots
```

### 哪些地方最常需要改

1. `new_score_reject_cutoff`
   新策略拒绝阈值
2. `old_card_reject_levels`
   旧策略拒绝边界
3. `risk_score_bins`
   风险分估算的分箱方式
4. `card_level_order`
   等级顺序

## 运行方式

```bash
cd 17_strategy_replacement_tuning
pip install -r requirements.txt
python run.py
```

## 结果解释建议

这个项目最容易被误读的地方，是把“估算坏账率”当成“真实坏账率”。  
需要明确区分：

- `observed_bad_rate`
  有真实表现样本上的历史坏账率
- `estimated_bad_rate`
  对旧拒绝、新通过人群的风险估算

因此在做业务结论时，建议重点看三件事：

1. `pass_rate_uplift`
   新策略到底多放过了多少人
2. `new_pass_old_reject_estimated_bad_rate`
   新放进来的人风险大概多高
3. `old_pass_new_reject_observed_bad_rate`
   被新策略替换出去的人历史风险如何

如果“新放入人群的估算风险明显低于被替换出去人群的历史风险”，且通过率又更高，那么替换方案通常更有业务吸引力。

## 适用边界与注意事项

- 该项目的结论依赖“风险分箱估算”假设，不等同于真实放量后的最终表现
- 如果新旧策略覆盖的客群结构发生较大漂移，估算误差会放大
- `grid_score` 是候选排序工具，不应替代正式业务收益测算

## 与其他项目的关系

- `15` 看规则怎么调
- `16` 看新增规则值不值
- `17` 看整套新旧策略能不能替换

一句话总结：  
这个项目是“在存在拒绝样本无真实表现的情况下，量化评估新旧策略替换可行性”的策略替换分析框架。
