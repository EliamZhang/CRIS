# 15_rule_d_class_tuning

## 项目定位

这是一个专门用于 D 类规则调优的项目。  
它的目标不是新增一套全新策略，而是围绕现有 D 类规则本身，回答：

- 哪条规则过松
- 哪条规则过严
- 调整阈值后坏账率和通过率如何变化
- 规则变量本身的风险分层是否支持当前阈值

相对于 `16`，这个项目更关注“规则本身怎么调”；而 `16` 更关注“在现有策略上新增什么规则更值”。

## 适合解决的业务问题

- 已有 D 类规则的阈值是否合理
- 哪条规则具有明显纯命中价值
- 哪些规则变量本身的风险梯度清晰，适合继续保留
- 调优前后，样本坏浓度和通过率会发生什么变化

## 方法论与实现原理

主逻辑位于 [src/rule_d_class_tuning.py](/C:/Users/zhangyuliang02/Desktop/rulelift/15_rule_d_class_tuning/src/rule_d_class_tuning.py)，核心配置类是 `ProjectConfig`。

项目分为三层分析。

### 1. 规则变量风险表现分析

针对规则涉及的变量，先做分箱或等级聚合，观察：

- `badprob`
- `lift`
- `max_lift_bin`

默认优先尝试 `scorecardpy` 的 tree 分箱；如果环境里没有安装 `scorecardpy`，则自动退化为按等级/取值聚合的内置分箱逻辑。

### 2. 固定规则集效果评估

配置中的 `rule_set` 定义了当前 D 类规则。默认每条规则包含：

- `name`
- `threshold`
- `operator`
- `comment`

项目会计算：

- 规则命中分布
- 纯命中贡献
- 规则调优前后的坏账率变化
- 调优前后的通过率变化

### 3. 阈值 grid search

针对 `rule_set` 中的规则变量，会基于候选阈值做自动搜索，并评估：

- `hit_rate`
- `bad_rate`
- `lift`
- `bad_capture`
- `grid_score`

这里的 `grid_score` 不是业务最终指标，而是用于在候选阈值中快速排序的内部综合分数。

## 输入数据契约

默认输入文件：

- `input/data_v3.xlsx`

输入要求：

- 文件格式：`Excel`
- 默认读取 `sheet_name = 0`
- 必须包含目标字段，默认是 `is_dlq_30d`

默认核心字段包括：

- `sample_id`
- `sample_month`
- `risk_score`
- `adr_stability_grade`
- `last_6m_avg_asset_total_grade`
- `ovd_order_cnt_6m_grade`
- `positive_biz_cnt_1y_grade`
- `repayment_ability_rank`
- `is_dlq_30d`

说明：

- `exclude_cols` 默认会排除 `sample_id`、`sample_month`、`risk_score`
- 实际参与规则变量分析的字段，是除排除列和目标列以外的字段

## 输出结果与如何使用

核心结果文件：

- `output/summary_report.xlsx`

常用 sheet 包括：

- `01_overall_summary`
  样本总览、整体坏账率和总体命中率
- `02_rule_lift_summary`
  规则变量最大 lift 摘要
- `03_rule_hit_sum_distribution`
  命中规则数分布
- `04_rule_pure_hit_summary`
  单规则纯命中贡献
- `05_tuning_effect_summary`
  调优前后坏账率和通过率变化
- `06_rule_hit_sample_detail`
  样本级命中明细
- `07_grid_search_rule_candidates`
  grid search 全量候选阈值
- `08_grid_search_top_rules`
  经过筛选的推荐阈值候选

辅助输出：

- `output/bins/*_bins.csv`
  各变量分箱明细
- `output/figures/top_variable_lift.png`
- `output/figures/rule_hit_count_distribution.png`
- `output/figures/before_after_tuning_effect.png`

推荐阅读顺序：

1. `02_rule_lift_summary`
2. `04_rule_pure_hit_summary`
3. `05_tuning_effect_summary`
4. `08_grid_search_top_rules`

## 配置与可调参数

配置集中在：

- [src/rule_d_class_tuning.py](/C:/Users/zhangyuliang02/Desktop/rulelift/15_rule_d_class_tuning/src/rule_d_class_tuning.py)
- `ProjectConfig`

关键配置项：

| 配置项 | 默认值 | 作用 |
|---|---|---|
| `data_file` | `input/data_v3.xlsx` | 输入文件 |
| `output_dir` | `output` | 输出目录 |
| `target_col` | `is_dlq_30d` | 标签列 |
| `id_col` | `sample_id` | 样本 ID |
| `month_col` | `sample_month` | 账期/月份字段 |
| `score_col` | `risk_score` | 分数字段 |
| `binning_method` | `scorecardpy` | 分箱方法优先级 |
| `rule_set` | 5 条默认规则 | 当前 D 类规则定义 |
| `top_n_plot` | `20` | 图中展示变量数 |
| `grid_top_n` | `30` | 推荐阈值条数 |
| `grid_min_hit_rate` | `0.01` | grid search 最小命中率 |
| `grid_max_hit_rate` | `0.50` | grid search 最大命中率 |
| `grid_min_lift` | `1.05` | grid search 最小 lift |
| `grid_min_bad_capture` | `0.01` | grid search 最小坏样本捕获 |

命令行支持：

```bash
python run.py --input input/data_v3.xlsx --output output
```

### 哪些地方最常需要改

1. `rule_set`
   规则定义是这个项目最核心的配置
2. `target_col`
   如果目标标签字段名变化，需要改这里
3. `binning_method`
   若要强制使用内置分箱，可手动改成非 `scorecardpy`
4. `grid_*`
   若想提高/放宽候选规则筛选标准，可调这里

## 运行方式

```bash
cd 15_rule_d_class_tuning
pip install -r requirements.txt
python run.py
```

## 结果解释建议

这个项目不应该只看“调后坏账率是不是下降了”，因为坏账率下降可能只是通过率大幅下降换来的。

建议重点联合看：

- `04_rule_pure_hit_summary`
  判断单条规则是否真的有独立贡献
- `05_tuning_effect_summary`
  看风险改善与通过率损失的平衡
- `08_grid_search_top_rules`
  看候选阈值是否具备更好的风险收益结构

一个值得认真考虑的阈值调整方案，通常应同时满足：

- 风险浓度确实改善
- 通过率损失可接受
- 规则阈值有业务解释性
- 不是极小样本驱动的偶然结果

## 适用边界与注意事项

- 这个项目重点是调现有 D 类规则，不是新增策略规则
- `scorecardpy` 不可用时会自动退化到内置分箱，结果口径会略有差异
- `grid_score` 只是候选排序指标，不能直接替代业务最终判断

## 与其他项目的关系

- `15` 调的是已有 D 类规则本身
- `16` 调的是在现有策略上新增规则是否值
- `17` 调的是新旧策略替换

一句话总结：  
这个项目是“围绕既有 D 类规则做阈值复核、纯命中分析和调优收益评估”的规则精调工具。
