# 10_univariate_rule_generation

## 项目定位

这是一个面向规则开发前置阶段的单变量规则生成项目。  
它的核心任务不是直接产出一整套可上线策略，而是从原始特征宽表中快速识别：

- 哪些变量本身具有较强风险区分能力
- 哪些阈值切分方式更适合形成规则
- 哪些单变量规则值得进入后续交叉分析、树模型挖掘或策略调优

如果把规则开发流程拆成“变量初筛 -> 候选规则发现 -> 组合规则评估 -> 策略化落地”，这个项目主要负责前两步中的单变量部分。

## 适合解决的业务问题

- 面对一批候选特征，哪些变量最值得优先关注
- 哪个变量单独看就能圈出更高风险样本
- 对于某个数值型变量，合理的规则阈值大概落在哪些区间
- 在可解释性前提下，哪些单变量规则具备进入下一轮验证的价值

不适合直接回答的问题：

- 多变量组合规则的最优形式
- 规则集整体覆盖和重叠关系
- 新旧策略替换收益

这些问题更适合交给 `11`、`12/13`、`14`、`16/17`。

## 方法论与实现原理

项目主逻辑位于 [src/univariate_rule_generation.py](/C:/Users/zhangyuliang02/Desktop/rulelift/10_univariate_rule_generation/src/univariate_rule_generation.py)，核心配置类是 `RuleGenerationConfig`。

整体流程如下：

1. 读取输入样本并校验目标字段  
   目标字段默认是 `target`，必须是严格的二分类 `0/1`。

2. 做变量基础统计  
   输出唯一值个数、缺失率、特殊缺失值占比、众数占比、字段类型等，用于快速发现低质量变量。

3. 自动识别连续变量与离散变量  
   默认通过 `discrete_unique_threshold` 区分变量类型。低基数字段会按离散变量处理，高基数字段会按连续变量处理。

4. 对变量做分箱，并计算 IV/WOE  
   连续变量默认优先使用决策树切点分箱，失败时退化为分位点切分；离散变量按取值聚合。  
   分箱后计算：
   - `badprob`
   - `woe`
   - `bin_iv`
   - `total_iv`

5. 自动生成候选阈值规则  
   数值型变量默认会围绕配置中的分位点列表生成两类规则：
   - `feature <= threshold`
   - `feature >= threshold`

6. 对候选规则做效果评估  
   重点评估：
   - `hit_cnt`
   - `hit_rate`
   - `bad_rate`
   - `lift`
   - `bad_capture`
   - `precision`
   - `recall`
   - `f1`

7. 根据筛选阈值输出推荐规则  
   默认会按 `lift_cutoff`、`hit_rate_down_cutoff`、`hit_rate_up_cutoff` 等条件过滤出更可用的规则。

从方法论上说，这个项目结合了“风险分箱分析”和“单变量阈值搜索”两种思路。  
它既关注变量解释力，也关注规则实用性。

## 输入数据契约

默认输入文件：

- `input/data_rule.csv`

输入要求：

- 文件格式：`CSV`
- 必须包含目标字段，默认是 `target`
- 目标字段必须能直接表示为 `0/1`
- 其余字段可以是数值型、等级型或低基数类别型

当前示例字段包括：

- `lmt`
- `job`
- `ncloseCreditCard`
- `basicLevel`
- `unpayNormalLoan`
- `target`

推荐的数据准备方式：

- 如果字段中存在业务特殊缺失值，提前统一编码，或在配置里通过 `missing_values` 指定
- 若某些字段明显不参与分析，可放入 `exclude_cols`
- 若只想分析指定字段，可在 `feature_cols` 中显式列出

## 输出结果与如何使用

运行完成后，重点查看：

- `output/summary_report.xlsx`

它是当前唯一需要重点查看的 Excel 结果文件。原始 CSV 会被自动汇总进该文件并删除。

核心 sheet 通常包括：

- `01_variable_statistics`
  变量基础质量画像，用于排查低信息量字段
- `02_iv_summary`
  变量级 IV 汇总，用于做变量优先级排序
- `03_bins_detail`
  分箱明细，用于理解风险分层和阈值位置
- `04_rule_candidates_all`
  全量候选规则，用于完整查看搜索空间
- `05_rule_candidates_selected`
  通过筛选阈值后的推荐规则

辅助输出还包括：

- `output/figures/*.png`
  变量分箱 bad rate 图
- `output/run_report.md`
  本次运行的简要文字摘要

实际使用时，建议按以下顺序阅读结果：

1. 先看 `02_iv_summary`
   明确哪些变量本身更有解释力
2. 再看 `03_bins_detail`
   理解风险单调性和分箱稳定性
3. 最后看 `05_rule_candidates_selected`
   判断哪些规则具备进入下一阶段的价值

## 配置与可调参数

主要配置集中在：

- [src/univariate_rule_generation.py](/C:/Users/zhangyuliang02/Desktop/rulelift/10_univariate_rule_generation/src/univariate_rule_generation.py)
- `RuleGenerationConfig`

关键配置项：

| 配置项 | 默认值 | 作用 |
|---|---|---|
| `input_path` | `input/data_rule.csv` | 输入文件 |
| `output_dir` | `output` | 输出目录 |
| `target_col` | `target` | 目标字段 |
| `exclude_cols` | `None` | 需要排除的字段 |
| `feature_cols` | `None` | 需要强制参与分析的字段 |
| `missing_values` | `[-999]` | 特殊缺失值定义 |
| `discrete_unique_threshold` | `20` | 连续/离散变量区分阈值 |
| `max_bins` | `5` | 最大分箱数 |
| `min_bin_pct` | `0.05` | 最小箱占比 |
| `binning_method` | `tree` | 分箱方法，优先树切分 |
| `quantile_list` | 多个分位点 | 候选阈值生成基础 |
| `lift_cutoff` | `1.5` | 推荐规则最小 lift |
| `hit_rate_down_cutoff` | `0.01` | 推荐规则最小命中率 |
| `hit_rate_up_cutoff` | `0.06` | 推荐规则最大命中率 |

命令行也支持覆盖部分配置：

```bash
python run.py --input input/data_rule.csv --output output --target target --lift 1.8 --hit-rate-min 0.01 --hit-rate-max 0.05
```

建议的修改顺序：

1. 先改输入、目标字段和分析字段范围
2. 再改分箱参数
3. 最后改规则筛选阈值

## 运行方式

```bash
cd 10_univariate_rule_generation
pip install -r requirements.txt
python run.py
```

## 结果解释建议

看单变量规则时，不建议只看 `lift`。  
至少要同时结合以下指标：

- `hit_rate`
  命中率太低时，规则虽然尖锐，但业务价值可能不足
- `bad_rate`
  反映命中样本风险水平
- `bad_capture`
  反映规则对坏样本的覆盖能力
- `precision` / `recall`
  反映规则识别精度和召回平衡

经验上，真正有业务落地价值的规则，通常需要同时满足：

- 有足够样本量
- 有明显高于整体的坏账率
- 不只是极端小样本造成的高 lift
- 规则阈值具有可解释性

## 适用边界与注意事项

- 这是单变量项目，不会自动产出双变量或多变量组合规则
- 对类别变量的处理更偏“规则发现”而不是严格建模编码
- 如果输入变量非常少，结果更像演示样本而不是生产级分析
- 如果目标样本严重失衡，建议结合命中量一起看，不要只看相对指标

## 与其他项目的关系

- `10` 适合做单变量前筛
- `11` 适合把筛出来的变量做交叉分析
- `12/13` 适合进一步做树模型规则挖掘
- `14` 适合在已有规则集基础上做整体评估

一句话总结：  
这个项目是“把宽表变量变成一批可解释单变量规则候选”的基础设施。
