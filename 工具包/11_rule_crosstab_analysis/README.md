# 11_rule_crosstab_analysis

## 项目定位

这是一个规则交叉分析与双变量规则发现项目。  
它既保留“手工指定规则并做验证”的能力，也支持“从候选变量中自动搜索双变量交叉规则”。

它适合处在这样的分析阶段：

- 单变量已经看过，但业务上怀疑需要组合条件才有足够区分度
- 已经有几条业务规则，希望量化评估其覆盖和风险表现
- 想从数据中系统性发现 `A + B` 类型的组合规则，而不只是凭经验试

## 适合解决的业务问题

- 哪两个变量组合之后更容易圈出高风险人群
- 现有手工规则是否真的有效
- 哪些交叉格子只是覆盖“大多数人”，而不是高价值规则
- 在可解释性前提下，哪些双变量组合值得进入策略讨论

## 方法论与实现原理

主逻辑位于 [src/rule_crosstab_analysis.py](/C:/Users/zhangyuliang02/Desktop/rulelift/11_rule_crosstab_analysis/src/rule_crosstab_analysis.py)。

项目包含两条分析链路。

### 1. 固定规则评估

代码顶部定义了 `RULES` 列表，默认包括：

- `int_rate > 21.5 and grade == G`
- `int_rate > 21.5 and grade in (F, G)`

这些规则会被逐条评估，输出：

- `hit_cnt`
- `bad_cnt`
- `hit_rate`
- `bad_rate`
- `lift`
- `bad_capture`

这一部分适合验证已有业务假设。

### 2. 自动双变量交叉规则搜索

自动搜索不是暴力枚举所有字段和所有切点，而是基于一组约束做有控制的候选发现：

1. 优先从数值变量中筛选 IV 较高的字段
2. 对连续变量自动分箱
3. 允许低基数类别变量参与组合
4. 枚举字段对，对每个交叉格子计算规则指标
5. 用一组业务阈值过滤不具备实用价值的组合

当前会使用的核心约束包括：

- `AUTO_SEARCH_MIN_SAMPLE_COUNT`
- `AUTO_SEARCH_MIN_HIT_RATE`
- `AUTO_SEARCH_MAX_HIT_RATE`
- `AUTO_SEARCH_MIN_LIFT`
- `AUTO_SEARCH_MIN_BAD_RATE`
- `AUTO_SEARCH_MIN_BAD_CAPTURE`

这些约束的目的，是避免搜索结果被两类低价值候选淹没：

- 样本量极小、偶然高 lift 的噪声格子
- 覆盖几乎全量样本、没有筛选意义的大格子

因此，这个项目本质上是“受约束的规则发现”，不是无条件穷举。

## 输入数据契约

默认输入文件：

- `input/lending_club_loan_two.csv`

输入要求：

- 文件格式：`CSV`
- 必须包含目标字段，默认是 `loan_status`
- 若目标字段是字符串，默认映射：
  - `Fully Paid -> 0`
  - `Charged Off -> 1`

默认排除字段：

- `issue_d`
- `address`
- `emp_title`
- `earliest_cr_line`
- `title`

常见可参与分析的字段包括：

- `int_rate`
- `grade`
- `dti`
- `loan_amnt`
- `annual_inc`
- `revol_util`
- `open_acc`

## 输出结果与如何使用

核心结果文件：

- `output/summary_report.xlsx`

常用 sheet 含义：

- `07_iv_table`
  数值型变量 IV 汇总，帮助理解哪些字段更值得进入自动搜索
- `08_iv_bins_detail`
  IV 分箱细节，帮助理解连续变量切分区间
- `10_cross_loan_count`
  固定交叉表的样本量矩阵
- `11_cross_bad_count`
  固定交叉表的坏样本量矩阵
- `12_cross_bad_rate`
  固定交叉表的坏账率矩阵
- `16_rule_evaluation`
  手工规则评估结果
- `19_auto_cross_feature_metadata`
  自动搜索实际纳入的候选字段元信息
- `20_auto_cross_pair_summary`
  每个字段对的最佳格子摘要
- `21_auto_cross_rule_candidates`
  自动搜索得到的全部候选交叉规则
- `22_auto_cross_search_config`
  本次搜索所用阈值配置
- `23_auto_cross_top_rules`
  综合排序后的推荐规则

辅助输出还包括：

- `14_cross_bad_rate_heatmap.png`
- `15_cross_sample_pct_heatmap.png`
- `30_auto_pair_heatmap_*.png`

推荐阅读顺序：

1. 先看 `16_rule_evaluation`
   判断现有规则是否有意义
2. 再看 `20_auto_cross_pair_summary`
   看哪些字段对最值得关注
3. 最后看 `23_auto_cross_top_rules`
   聚焦最终推荐的双变量规则

## 配置与可调参数

配置集中在：

- [src/rule_crosstab_analysis.py](/C:/Users/zhangyuliang02/Desktop/rulelift/11_rule_crosstab_analysis/src/rule_crosstab_analysis.py)

最需要关注的配置块：

- `RULES`
  手工评估规则
- `INT_RATE_BINS` / `DTI_BINS`
  固定分析时使用的预设切分
- `AUTO_SEARCH_*`
  自动搜索阈值和搜索规模控制

关键配置项：

| 配置项 | 作用 |
|---|---|
| `RULES` | 手工指定要评估的业务规则 |
| `AUTO_SEARCH_MAX_FEATURES` | 自动搜索纳入的最大字段数 |
| `AUTO_SEARCH_MAX_CATEGORY_UNIQUE` | 类别字段允许参与搜索的最大基数 |
| `AUTO_SEARCH_MAX_BIN_COUNT` | 连续变量自动分箱时的最大箱数 |
| `AUTO_SEARCH_MIN_SAMPLE_COUNT` | 规则最小样本量 |
| `AUTO_SEARCH_MIN_HIT_RATE` | 最小命中率 |
| `AUTO_SEARCH_MAX_HIT_RATE` | 最大命中率 |
| `AUTO_SEARCH_MIN_LIFT` | 最小 lift |
| `AUTO_SEARCH_MIN_BAD_RATE` | 最小坏账率 |
| `AUTO_SEARCH_MIN_BAD_CAPTURE` | 最小坏样本捕获 |
| `AUTO_SEARCH_TOP_N_RULES` | 最终推荐规则数量 |

命令行支持：

```bash
python run.py --input input/lending_club_loan_two.csv --output output
```

## 运行方式

```bash
cd 11_rule_crosstab_analysis
pip install -r requirements.txt
python run.py
```

## 结果解释建议

看双变量规则时，重点不是“命中越多越好”，而是“在合理命中率下是否显著提升风险浓度”。

建议重点关注：

- `hit_rate`
  太高通常意味着规则只是描述常见人群
- `bad_rate`
  命中样本本身的风险水平
- `lift`
  相对整体风险的放大倍数
- `bad_capture`
  对坏样本的捕获能力

经验上，一个适合进入后续讨论的交叉规则，通常应满足：

- 命中率不过大
- lift 明显高于 1
- bad_capture 不为零且有业务价值
- 字段组合具有可解释性

## 适用边界与注意事项

- 这不是全自动策略生成器，仍需要人工判断规则合理性
- 自动搜索会偏向“可解释的双变量格子”，而不是黑箱最优分类
- 如果字段很多但质量差，搜索结果也会被噪声拖累
- 该项目重点是规则发现，不直接给出策略替换后的通过率收益

## 与其他项目的关系

- `10` 适合先做单变量筛选
- `11` 适合做双变量交叉发现
- `12/13` 适合进一步挖掘更复杂的多变量规则

一句话总结：  
这个项目是“把业务经验规则和数据驱动交叉规则放在同一框架下评估”的双变量规则工作台。
