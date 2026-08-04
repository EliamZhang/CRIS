# 16_strategy_d_class_tuning

## 项目定位

这是一个“在现有策略基础上新增规则并评估增益”的项目。  
它的核心问题不是“已有规则怎么调”，而是：

- 往现有策略里多加一条规则值不值得
- 新增单变量规则和新增交叉规则，哪个更优
- 新接入的变量是否真的带来了额外风险识别收益

因此，它更像一个“策略增量分析器”，而不是单纯的规则体检工具。

## 适合解决的业务问题

- 现有策略已经有规则，是否还需要加新规则
- 某个新变量接入后，是否能提升风险识别
- 单变量新增规则和双变量新增规则，哪个更有性价比
- 自动搜索到的新增规则是否优于当前默认方案

## 方法论与实现原理

主逻辑位于 [src/strategy_d_class_tuning.py](/C:/Users/zhangyuliang02/Desktop/rulelift/16_strategy_d_class_tuning/src/strategy_d_class_tuning.py)，配置集中在 `Config`。

项目同时保留三条分析线：

### 1. 现有规则集评估

配置项 `existing_rules` 定义当前在用规则。  
项目会先评估这些规则的命中分布和纯命中情况，作为策略基线。

### 2. 默认新增规则方案评估

项目内置两类新增方案：

- `single_var_rules`
  默认新增单变量规则
- `cross_rules`
  默认新增交叉规则

会分别输出其：

- 命中分布
- 纯命中贡献
- 调整前后坏账率
- 调整前后通过率

### 3. grid search 自动搜索新增规则

项目还支持自动从 `grid_candidate_features` 中搜索：

- 单变量阈值规则
- 双变量组合规则

自动搜索时，会保留规则元数据，而不是仅保留展示字符串，因此后续可以稳定追踪：

- `left_feature`
- `left_operator`
- `left_threshold`
- `right_feature`
- `right_operator`
- `right_threshold`

这意味着文档和结果表既可以业务阅读，也适合后续程序化消费。

## 输入数据契约

默认输入文件：

- `input/data_v4.xlsx`

输入要求：

- 文件格式：`Excel`
- 必须包含：
  - `sample_id`
  - `sample_month`
  - `is_dlq_30d`
  - `risk_score`
  - `ovd_order_cnt_6m_grade`
  - `positive_biz_cnt_1y_grade`
  - `adr_stability_grade`

默认业务语义：

- 仅对有表现标签的通过样本做主要效果评估
- `is_dlq_30d = 1` 视为坏样本

## 输出结果与如何使用

核心结果文件：

- `output/summary_report.xlsx`

常用 sheet：

- `00_data_overview`
  数据概况和输入字段信息
- `01_existing_var_metrics`
  现有变量的 IV / lift 摘要
- `01_existing_var_bins`
  现有变量分箱明细
- `02_new_var_metrics`
  新接入变量的 IV / lift 摘要
- `02_new_var_bins`
  新接入变量分箱明细
- `03_existing_rules_hit_dist`
  现有规则命中分布
- `03_existing_rules_hit_summary`
  现有规则命中摘要
- `04_single_rule_hit_dist`
  默认单变量新增规则命中分布
- `04_single_rule_hit_summary`
  默认单变量新增规则命中摘要
- `04_single_rule_effect`
  默认单变量新增规则效果
- `05_cross_lift_matrix`
  二维 lift 矩阵
- `05_cross_sample_pct_matrix`
  二维样本占比矩阵
- `06_cross_rule_hit_dist`
  默认交叉规则命中分布
- `06_cross_rule_hit_summary`
  默认交叉规则命中摘要
- `06_cross_rule_effect`
  默认交叉规则效果
- `07_grid_single_rule_candidates`
  grid search 单变量候选规则
- `07_grid_pair_rule_candidates`
  grid search 双变量候选规则
- `08_grid_top_rules`
  推荐新增规则

辅助输出：

- `output/05_cross_heatmap.png`
- `output/run_summary.json`

推荐阅读顺序：

1. `03_existing_rules_hit_summary`
2. `04_single_rule_effect`
3. `06_cross_rule_effect`
4. `08_grid_top_rules`

## 配置与可调参数

配置集中在：

- [src/strategy_d_class_tuning.py](/C:/Users/zhangyuliang02/Desktop/rulelift/16_strategy_d_class_tuning/src/strategy_d_class_tuning.py)
- `Config`

关键配置项：

| 配置项 | 默认值 | 作用 |
|---|---|---|
| `input_file` | `input/data_v4.xlsx` | 输入文件 |
| `output_dir` | `output` | 输出目录 |
| `target_col` | `is_dlq_30d` | 标签列 |
| `sample_id_col` | `sample_id` | 样本 ID |
| `sample_month_col` | `sample_month` | 月份字段 |
| `new_features` | `risk_score`, `ovd_order_cnt_6m_grade` | 新接入变量 |
| `cross_index` | `risk_score` | 热力图行维度 |
| `cross_columns` | `ovd_order_cnt_6m_grade` | 热力图列维度 |
| `existing_rules` | 若干表达式 | 当前已有规则 |
| `single_var_rules` | 若干表达式 | 默认新增单变量规则 |
| `cross_rules` | 若干表达式 | 默认新增交叉规则 |
| `grid_candidate_features` | 一组字段 | 自动搜索候选字段 |
| `grid_top_n` | `30` | 推荐规则条数 |
| `grid_min_hit_rate` | `0.01` | 最小命中率 |
| `grid_max_hit_rate` | `0.40` | 最大命中率 |
| `grid_min_lift` | `1.10` | 最小 lift |
| `grid_min_bad_capture` | `0.01` | 最小坏样本捕获 |

命令行支持：

```bash
python run.py --input input/data_v4.xlsx --output output
```

### 哪些地方最常需要改

1. `existing_rules`
   你的当前策略基线
2. `single_var_rules`
   你想验证的新增单变量方案
3. `cross_rules`
   你想验证的新增交叉规则方案
4. `grid_candidate_features`
   自动搜索允许纳入的变量范围

## 运行方式

```bash
cd 16_strategy_d_class_tuning
pip install -r requirements.txt
python run.py
```

## 结果解释建议

这个项目的关键不是“新增规则后风险是不是下降”，而是“新增规则带来的收益是否值得它造成的通过率损失”。

建议重点联看：

- `04_single_rule_effect`
- `06_cross_rule_effect`
- `08_grid_top_rules`

重点指标：

- `after_bad_rate`
- `after_pass_rate`
- `bad_rate_drop_abs`
- `pass_rate_drop_abs`
- `lift`
- `bad_capture`

如果一个新增规则：

- 风险改善很小
- 通过率损失很大
- 且纯命中贡献不明显

那它通常不值得纳入策略。

## 适用边界与注意事项

- 这个项目评估的是“增量规则价值”，不是整套策略替换
- 自动搜索结果依赖 `grid_candidate_features` 的边界，不是对全字段无限搜索
- `grid_score` 是内部排序指标，最终仍要结合业务约束判断

## 与其他项目的关系

- `15` 更关注已有规则怎么调
- `16` 更关注新增规则值不值
- `17` 更关注新旧整套策略替换

一句话总结：  
这个项目是“以现有策略为基线，量化新增规则是否带来净增益”的策略增量评估器。
