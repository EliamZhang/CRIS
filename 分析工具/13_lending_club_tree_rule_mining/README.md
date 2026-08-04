# 13_lending_club_tree_rule_mining

## 项目定位

这是一个面向 Lending Club 场景的决策树规则挖掘项目。  
它和 `12_decision_tree_rule_mining` 的核心思想一致，都是通过浅层决策树自动发现多变量规则，但它的实现更偏“业务展示版”和“脚本化交付版”。

相比 `12`，这个项目更强调：

- 命令行参数完整
- 输出结果更扁平，便于直接交付
- 规则文本、编码映射和运行环境信息更适合留档

## 适合解决的业务问题

- 在 Lending Club 类贷款样本上，如何快速挖掘可解释的组合规则
- 如何以更直接的脚本方式复现 notebook 中的树规则挖掘流程
- 如何把树模型规则输出成更方便业务阅读和归档的材料

## 方法论与实现原理

主逻辑位于 [src/lending_club_tree_rule_mining.py](/C:/Users/zhangyuliang02/Desktop/rulelift/13_lending_club_tree_rule_mining/src/lending_club_tree_rule_mining.py)。

核心流程如下：

1. 读取输入 CSV
2. 做基础数据画像
3. 将目标标签从字符串映射成二分类
4. 对类别变量做 `LabelEncoder`
5. 对缺失值填充默认值
6. 训练浅层决策树
7. 从树路径抽取规则
8. 输出规则表、树图、编码表、运行配置和环境信息

从原理上看，它依然是“树模型自动发现规则”，但更偏向将结果以可交付形式沉淀下来。

## 输入数据契约

默认输入文件：

- `input/lending_club_loan_two.csv`

输入要求：

- 文件格式：`CSV`
- 必须包含目标字段，默认是 `loan_status`
- 默认标签定义：
  - `Charged Off` 为坏样本
  - `Fully Paid` 为好样本

默认会排除的字段：

- `issue_d`
- `address`
- `emp_title`
- `earliest_cr_line`
- `title`

如果迁移到其他数据集，优先检查：

- `target_col`
- `positive_label`
- `negative_label`
- `drop_cols`

## 输出结果与如何使用

核心结果文件：

- `output/summary_report.xlsx`

常用 sheet 包括：

- `feature_summary`
  字段基础统计
- `data_describe`
  描述性统计
- `target_distribution`
  目标分布
- `category_encoding_mapping`
  类别变量编码映射
- `model_metrics`
  模型整体指标
- `rule_mining_results`
  自动挖掘出来的规则清单

辅助输出：

- `output/decision_tree.dot`
  决策树 DOT 源文件
- `output/decision_tree.png`
  决策树结构图
- `output/target_distribution.png`
  目标分布图
- `output/run_config_and_environment.json`
  运行配置和环境信息

推荐阅读顺序：

1. `model_metrics`
2. `rule_mining_results`
3. `decision_tree.png`
4. `category_encoding_mapping`

## 配置与可调参数

配置集中在：

- [src/lending_club_tree_rule_mining.py](/C:/Users/zhangyuliang02/Desktop/rulelift/13_lending_club_tree_rule_mining/src/lending_club_tree_rule_mining.py)
- `Config`

关键配置项：

| 配置项 | 默认值 | 作用 |
|---|---|---|
| `input_path` | `input/lending_club_loan_two.csv` | 输入文件 |
| `output_dir` | `output` | 输出目录 |
| `target_col` | `loan_status` | 标签列 |
| `positive_label` | `Charged Off` | 坏样本标签 |
| `negative_label` | `Fully Paid` | 好样本标签 |
| `drop_cols` | 多个文本字段 | 排除列 |
| `missing_value` | `-9999` | 缺失值填充值 |
| `test_size` | `0.2` | 测试集比例 |
| `max_depth` | `3` | 树深度 |
| `min_samples_leaf` | `0.05` | 最小叶子约束 |
| `min_samples_split` | `0.05` | 最小分裂约束 |
| `criterion` | `gini` | 切分准则 |

命令行支持：

```bash
python run.py --input input/lending_club_loan_two.csv --output output --target-col loan_status --positive-label "Charged Off" --negative-label "Fully Paid" --max-depth 3
```

## 运行方式

```bash
cd 13_lending_club_tree_rule_mining
pip install -r requirements.txt
python run.py
```

## 结果解释建议

这个项目更适合作为“树规则展示和复盘材料”，而不是策略最终定稿依据。

建议关注：

- `rule_mining_results` 中每条规则的样本量和风险浓度
- `decision_tree.png` 中变量的切分顺序
- `category_encoding_mapping` 中类别变量编码关系

如果规则文本出现很多难以解释的编码阈值，说明：

- 变量编码映射需要同步解释
- 规则还需要人工翻译成业务含义

## 适用边界与注意事项

- 这是 Lending Club 风格的规则挖掘脚本，迁移到新数据集时要先审查字段语义
- 编码后规则在展示时更需要结合映射表一起看
- 它没有像 `12` 一样做树参数 grid search，因此更适合作为固定配置挖规则的交付脚本

## 与其他项目的关系

- `12` 更偏“规则挖掘 + 参数搜索”
- `13` 更偏“规则挖掘 + 展示交付”

一句话总结：  
这个项目是一个更偏交付、展示和留档的树规则挖掘脚本版本。
