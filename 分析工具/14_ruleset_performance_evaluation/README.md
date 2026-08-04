# 14_ruleset_performance_evaluation

## 项目定位

这是一个规则集整体效果评估项目。  
它关注的不是“某一条规则好不好”，而是“这组规则放在一起整体表现如何”。

典型应用场景包括：

- 一套规则已经存在，需要做系统性复盘
- 想知道规则之间是否严重重叠
- 想判断某些规则是不是冗余、弱贡献或被其他规则完全覆盖
- 想同时看规则发现结果和现有规则集表现

## 适合解决的业务问题

- 整体规则集命中率、坏账率和 lift 如何
- 哪些规则之间高度重叠，可能重复筛到同一批人
- 哪些规则有纯命中贡献，哪些规则只是跟随别人命中
- 删除部分规则后，规则集结构会不会明显变化

## 方法论与实现原理

主逻辑位于 [src/ruleset_performance_evaluation.py](/C:/Users/zhangyuliang02/Desktop/rulelift/14_ruleset_performance_evaluation/src/ruleset_performance_evaluation.py)。

项目包含两块核心能力。

### 1. 自动候选规则挖掘

项目会基于 `rule_mining_jobs` 设定，用决策树在不同变量组合范围和树深度下自动挖规则，例如：

- 两个变量组合、树深 1
- 全部变量、树深 2
- 全部变量、树深 3

生成的候选规则会根据：

- `lift`
- `hit_rate`

等阈值进行筛选。

### 2. 规则集整体评估

项目内置了一套规则集命中逻辑，定义在 `build_rule_flags()` 中。  
当前示例规则依赖字段：

- `V01`
- `V02`
- `V05`
- `V06`
- `V10`

在规则集评估阶段，会重点输出：

- 每条规则的命中标记
- 规则间 mutual cover
- 完全覆盖关系
- pure hit 纯命中分析
- 总命中分布
- 整体 ruleset summary

从方法论上说，这个项目强调“规则组合结构分析”，而不是单条规则精细调优。

## 输入数据契约

默认输入文件：

- `input/100daysrisk_strategy_ruleset.xlsx`

输入要求：

- 文件格式：`Excel`
- 默认读取 `sheet_name = 0`
- 必须包含：
  - `ID`
  - `TARGET`
- 若要使用当前默认规则集评估逻辑，还必须包含：
  - `V01`
  - `V02`
  - `V05`
  - `V06`
  - `V10`

如果你的数据不是这组字段命名，那么最重要的改造点不是参数，而是 `build_rule_flags()`。

## 输出结果与如何使用

核心结果文件：

- `output/summary_report.xlsx`

常用 sheet：

- `describe`
  原始数据描述统计
- `simple_statistics`
  字段级基础统计
- `target_distribution`
  目标分布
- `variable_types`
  数值/非数值字段分类
- `mined_rules_all`
  自动挖掘出的全部候选规则
- `mined_rules_filtered`
  过滤后的候选规则
- `mutual_cover`
  规则两两覆盖关系
- `full_cover_rules`
  完全覆盖关系摘要
- `pure_hit`
  单规则纯命中贡献
- `hit_sum_distribution`
  命中 0/1/2/... 条规则的人群分布
- `total_hit_distribution`
  是否命中任一规则的分布
- `ruleset_summary`
  规则集整体效果摘要

辅助输出还包括：

- `output/figures/target_distribution.png`
- `output/tables/all_rule_flags.csv`
- `output/tables/selected_rule_flags.csv`

推荐阅读顺序：

1. `ruleset_summary`
2. `pure_hit`
3. `mutual_cover`
4. `mined_rules_filtered`

## 配置与可调参数

配置集中在：

- [src/ruleset_performance_evaluation.py](/C:/Users/zhangyuliang02/Desktop/rulelift/14_ruleset_performance_evaluation/src/ruleset_performance_evaluation.py)
- `Config`

关键配置项：

| 配置项 | 默认值 | 作用 |
|---|---|---|
| `input_file` | `100daysrisk_strategy_ruleset.xlsx` | 输入文件 |
| `sheet_name` | `0` | 读取的 sheet |
| `id_col` | `ID` | 样本唯一标识 |
| `target_col` | `TARGET` | 标签列 |
| `rule_mining_jobs` | `[(2,1),(None,2),(None,3)]` | 自动挖规则任务组合 |
| `min_lift` | `1.0` | 候选规则最小 lift |
| `max_hit_rate_pct` | `5.0` | 候选规则最大命中率 |
| `delete_rules` | `rule7, rule4, rule1, rule5` | 在规则集评估中剔除的规则 |

命令行支持：

```bash
python run.py --input input/100daysrisk_strategy_ruleset.xlsx --output output --sheet-name 0 --target TARGET --id-col ID
```

### 哪些地方最常需要改

1. `build_rule_flags()`
   如果规则定义不是当前示例规则，优先改这里
2. `delete_rules`
   如果想比较不同规则集组合，可以改这里
3. `rule_mining_jobs`
   如果想改变自动挖规则范围，可以改这里

## 运行方式

```bash
cd 14_ruleset_performance_evaluation
pip install -r requirements.txt
python run.py
```

## 结果解释建议

评估规则集时，建议避免只看整体命中率。

更关键的是：

- 有多少规则是真正提供独立贡献的
- 有多少规则只是与其他规则高度重叠
- 规则集是否被少数大规则主导

可重点观察：

- `pure_hit`
  看单条规则的独立价值
- `mutual_cover`
  看规则间是否互相覆盖
- `full_cover_rules`
  看是否存在被完全覆盖的规则

如果一条规则命中不少，但 pure hit 很低、且被其他规则完全覆盖，那么它往往不具备保留必要性。

## 适用边界与注意事项

- 当前规则集评估逻辑不是参数化规则引擎，而是代码内写死的示例规则定义
- 迁移到新数据时，必须同步检查字段和规则定义
- 自动挖掘出的规则与手工规则集评估是两条线，不能简单混为“同一口径评分”

## 与其他项目的关系

- `10/11/12/13` 更偏规则发现
- `14` 更偏规则集复盘和整体结构评估
- `15/16/17` 更偏规则和策略调优

一句话总结：  
这个项目是“从整套规则而不是单条规则的角度，分析覆盖、重叠和整体效果”的规则集体检工具。
