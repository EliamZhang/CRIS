# 12_decision_tree_rule_mining

## 项目定位

这是一个基于决策树的多变量规则挖掘项目。  
它的目标不是训练一个用于上线打分的复杂模型，而是利用决策树的分裂路径，将“变量组合关系”转写为可解释规则。

相较于单变量阈值规则或手工双变量交叉，这个项目更适合解决：

- 多个变量共同作用时，最有区分度的规则路径是什么
- 手工枚举组合太低效时，如何让模型帮助发现候选规则
- 如何在保持可解释性的前提下，从数据中自动发现多变量 if-else 结构

## 适合解决的业务问题

- 哪些变量组合天然构成高风险叶子群体
- 同一批数据上，浅层树能挖出哪些可解释路径
- 不同树参数下，规则质量是否明显变化
- 是否存在“单变量不显著，但多变量路径显著”的组合

## 方法论与实现原理

主逻辑位于 [src/decision_tree_rule_mining.py](/C:/Users/zhangyuliang02/Desktop/rulelift/12_decision_tree_rule_mining/src/decision_tree_rule_mining.py)。

### 核心方法

1. 读取原始样本
2. 将目标变量映射为二分类标签
3. 对类别变量做 `LabelEncoder` 编码
4. 对缺失值做统一填充
5. 使用 `DecisionTreeClassifier` 训练浅层树
6. 从叶子节点反向回溯分裂路径，生成规则文本
7. 对每条规则统计样本量、坏账率、命中率、召回率、lift

这类方法的优势在于：

- 规则是模型自动发现的
- 规则仍然是 if-else 形式，便于解释
- 可以表达多变量非线性交互

### 为什么要做 grid search

同一份数据上，树参数会明显影响规则结构：

- `max_depth` 太浅，规则不够细
- `max_depth` 太深，规则容易过拟合
- `min_samples_leaf` 太小，叶子样本不稳定
- `criterion` 不同，切分偏好不同

因此项目新增了树参数 grid search，用于比较不同参数组合下的：

- `test_auc`
- `test_accuracy`
- `test_recall`
- 最佳规则的 `bad_rate` / `lift`

当前 grid search 已经按测试集规则表现参与评分，不再只看训练集上的规则好坏。

## 输入数据契约

默认输入文件：

- `input/lending_club_loan_two.csv`

输入要求：

- 文件格式：`CSV`
- 必须包含目标字段，默认是 `loan_status`
- 默认标签映射：
  - `Fully Paid -> 0`
  - `Charged Off -> 1`

默认不参与建模的字段：

- `loan_status`
- `issue_d`
- `address`
- `emp_title`
- `earliest_cr_line`
- `title`

说明：

- 这套默认排除逻辑主要是为了规避高噪声文本字段和明显泄漏风险字段
- 如果迁移到新数据集，最重要的是先重审 `exclude_cols`

## 输出结果与如何使用

核心结果文件：

- `output/summary_report.xlsx`

常用 sheet 包括：

- `tables__data_preview`
  原始样本预览
- `tables__data_describe`
  描述性统计
- `tables__simple_statistics`
  字段级基础统计
- `tables__field_dtypes_and_missing`
  类型与缺失分布
- `tables__categorical_encoding_mapping`
  类别变量编码映射
- `tables__model_metrics`
  训练集/测试集模型指标
- `tables__decision_tree_rules`
  主模型叶子规则清单
- `tables__tree_grid_search_results`
  所有参数组合的 grid search 结果
- `tables__tree_grid_search_top_configs`
  推荐参数组合

辅助输出还包括：

- `output/figures/decision_tree_structure.png`
- `output/figures/rule_lift_ranking.png`
- `output/tables/decision_tree_rules.md`
- `output/tables/run_summary.json`

推荐阅读顺序：

1. `tables__model_metrics`
2. `tables__decision_tree_rules`
3. `tables__tree_grid_search_top_configs`

## 配置与可调参数

配置集中在：

- [src/decision_tree_rule_mining.py](/C:/Users/zhangyuliang02/Desktop/rulelift/12_decision_tree_rule_mining/src/decision_tree_rule_mining.py)
- `Config`

关键配置项：

| 配置项 | 默认值 | 作用 |
|---|---|---|
| `input_path` | `input/lending_club_loan_two.csv` | 输入文件 |
| `output_dir` | `output` | 输出目录 |
| `target_col` | `loan_status` | 标签列 |
| `target_mapping` | `Fully Paid/Charged Off` | 标签映射 |
| `exclude_cols` | 若干文本和目标字段 | 不参与建模的列 |
| `test_size` | `0.2` | 测试集比例 |
| `tree_criterion` | `gini` | 决策树切分准则 |
| `tree_max_depth` | `3` | 主模型最大深度 |
| `tree_min_samples_leaf` | `0.05` | 最小叶子占比 |
| `tree_min_samples_split` | `0.05` | 最小分裂占比 |
| `grid_max_depths` | `(2, 3, 4, 5)` | 搜索深度 |
| `grid_min_samples_leaf` | `(0.01, 0.03, 0.05)` | 搜索叶子约束 |
| `grid_min_samples_split` | `(0.02, 0.05, 0.1)` | 搜索分裂约束 |
| `grid_criteria` | `("gini", "entropy")` | 搜索准则 |

命令行支持：

```bash
python run.py --input input/lending_club_loan_two.csv --output output --max-depth 3 --test-size 0.2
```

## 运行方式

```bash
cd 12_decision_tree_rule_mining
pip install -r requirements.txt
python run.py
```

## 结果解释建议

决策树规则不能只看模型 AUC，也不能只看规则 lift。

建议至少同时看三层信息：

1. 模型层  
   `test_auc`、`test_accuracy`、`test_recall`

2. 规则层  
   每条规则的 `sample_cnt`、`bad_rate`、`hit_rate`、`recall_rate`、`lift`

3. 参数层  
   grid search 下不同参数对规则稳定性和泛化能力的影响

一个参数组合值得保留，通常意味着：

- 测试集指标不过分差
- 规则数量适中
- 规则样本量不至于过小
- 规则文本对业务有可解释性

## 适用边界与注意事项

- 类别变量默认使用 `LabelEncoder`，这适合树模型挖规则，但不代表数值大小有业务顺序
- 该项目的定位是“规则发现”，不是生产评分卡训练
- 树太深时会得到很多细碎规则，解释成本和过拟合风险都会上升

## 与其他项目的关系

- `10` 是单变量规则前筛
- `11` 是双变量交叉发现
- `12` 是自动多变量规则挖掘
- `14` 则更适合评估已有规则集的组合效果

一句话总结：  
这个项目是“用浅层决策树把多变量关系翻译成可解释规则”的自动规则发现器。
