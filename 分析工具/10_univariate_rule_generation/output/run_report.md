# 规则生成运行报告

## 一、样本概况

- 输入文件：`C:\Users\zhangyuliang02\Desktop\rulelift\10_univariate_rule_generation\input\data_rule.csv`
- 样本量：132,029
- 字段数：31
- 目标字段：`target`
- 整体坏账率：0.726356%

## 二、配置摘要

```text
{'input_path': WindowsPath('C:/Users/zhangyuliang02/Desktop/rulelift/10_univariate_rule_generation/input/data_rule.csv'), 'output_dir': WindowsPath('C:/Users/zhangyuliang02/Desktop/rulelift/10_univariate_rule_generation/output'), 'target_col': 'target', 'exclude_cols': ['target'], 'feature_cols': None, 'missing_values': [-999], 'discrete_unique_threshold': 20, 'max_bins': 5, 'min_bin_pct': 0.05, 'binning_method': 'tree', 'smoothing': 0.5, 'quantile_list': [0.005, 0.01, 0.02, 0.05, 0.95, 0.98, 0.99, 0.995], 'lift_cutoff': 1.5, 'hit_rate_down_cutoff': 0.01, 'hit_rate_up_cutoff': 0.06, 'bad_capture_down_cutoff': 0.0, 'save_figures': True, 'figure_dpi': 160}
```

## 三、Top IV 变量

| variable            |       iv | feature_type   |
|:--------------------|---------:|:---------------|
| lmt                 | 0.195028 | continuous     |
| lmt_amt_bucket      | 0.181492 | discrete       |
| lmt_business_bin    | 0.181492 | discrete       |
| limit_recommend_amt | 0.168633 | continuous     |
| lmt_capacity_level  | 0.165453 | discrete       |
| expense_proxy_level | 0.141035 | discrete       |
| expense_proxy_amt   | 0.138948 | continuous     |
| income_proxy_amt    | 0.125818 | continuous     |
| income_proxy_level  | 0.120696 | discrete       |
| strategy_segment    | 0.118632 | discrete       |

## 四、Top 规则候选

| variable            | rule                       |   hit_rate |   hit_bad_rate |   bad_capture |    lift |        f1 |
|:--------------------|:---------------------------|-----------:|---------------:|--------------:|--------:|----------:|
| lmt                 | lmt <= 0.563               |  0.0105204 |      0.0201584 |     0.0291971 | 2.77528 | 0.0238501 |
| limit_recommend_amt | limit_recommend_amt <= 500 |  0.026426  |      0.0194898 |     0.0709072 | 2.68323 | 0.0305755 |
| limit_recommend_amt | limit_recommend_amt <= 500 |  0.026426  |      0.0194898 |     0.0709072 | 2.68323 | 0.0305755 |
| limit_recommend_amt | limit_recommend_amt <= 500 |  0.026426  |      0.0194898 |     0.0709072 | 2.68323 | 0.0305755 |
| income_proxy_amt    | income_proxy_amt <= 1500   |  0.0100281 |      0.0188822 |     0.0260688 | 2.59958 | 0.021901  |
| income_proxy_amt    | income_proxy_amt <= 1500   |  0.0100281 |      0.0188822 |     0.0260688 | 2.59958 | 0.021901  |
| basicLevel          | is missing                 |  0.017125  |      0.0176913 |     0.0417101 | 2.43562 | 0.0248447 |
| basic_level_clean   | basic_level_clean <= 0     |  0.017125  |      0.0176913 |     0.0417101 | 2.43562 | 0.0248447 |
| basic_level_clean   | basic_level_clean <= 0     |  0.017125  |      0.0176913 |     0.0417101 | 2.43562 | 0.0248447 |
| basic_level_clean   | basic_level_clean == 0     |  0.017125  |      0.0176913 |     0.0417101 | 2.43562 | 0.0248447 |

## 五、输出文件

- `01_variable_statistics.csv`：变量初筛统计
- `02_iv_summary.csv`：变量 IV 汇总
- `03_bins_detail.csv`：变量分箱明细、WOE、bin IV
- `04_rule_candidates_all.csv`：所有候选规则
- `05_rule_candidates_selected.csv`：按配置阈值筛选后的规则
- `figures/`：每个变量的分箱坏账率图片
