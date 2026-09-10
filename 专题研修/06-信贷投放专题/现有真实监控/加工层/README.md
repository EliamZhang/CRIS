# 监控加工层

本目录在不修改 01~16 原始 Excel 的前提下，提供统一分析表和 HTML 导入快照。

## 文件说明

| 文件 | 内容 | 使用方式 |
|------|------|----------|
| `00_加工层数据字典_CuratedDataDictionary.csv` | 加工层 13 张数据表、126 个字段的定义与血缘 | 查字段类型、主键、来源和 HTML 路径 |
| `01_监控加工模型_CuratedModel.xlsx` | 统一分析模型，共 15 个工作表 | 分析、对账和接口开发 |
| `02_月度监控快照_monthly-monitor-v1_真实.json` | 01~05 的完整真实月度快照 | HTML“数据接入”直接导入 |
| `03_明细监控快照_schemaVersion2_样例.json` | 06~10 组装后的完整明细样例 | HTML“数据接入”直接导入；真实替换前不可当作生产数据 |

## 合并原则

- `monthly_channel_metrics`：合并 01、02、03、04、13 到 `month + channel` 粒度。CPFL 保留原值，不用媒体账单倒推；13 当前仅有 24 个样例键，其余样本量保持为空。
- `postback_events`：09 左连接 14，补入 `eventTime` 和 `firstSentTime`。HTML 所需 `latency` 保留在同一事件表中。
- `experiment_header` 与 `experiment_arms`：统一 11 Holdout 和 16 Geo Lift，同时保留实验类型与随机化单元。
- `google_ads_conversions`：由 15 生成，只保留转化动作粒度字段；成本、点击和币种以 12 `media_billing` 为唯一月度来源，避免跨动作重复加总。
- `records`、`touches`、`costs` 保持独立关系表，防止一对多平铺导致放款、触点和成本重复。生成 JSON 时再把 07/08 嵌入 06。
- `kpi_reference` 与实际月度指标分开保存，避免目标/预测/实际性质未确认时混算。

## 使用边界

- `snapshot_meta.dataClass=sample` 表示当前明细快照仍为虚构样例；替换真实数据后改为 `real`。
- 渠道映射中标记“待确认”或“待处理”的行不会自动参与跨层合并。
- 负 CPFL 和空 Green 分层保留原值，由 HTML 告警提示，不在加工层静默修正。
- HTML 只接收 JSON，不直接读取本目录中的 Excel。
