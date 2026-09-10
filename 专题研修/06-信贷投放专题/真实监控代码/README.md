# 真实监控代码 · SQL 脚手架

> 本目录用于沉淀「信贷投放与归因监控中心」背后的**真实监控 SQL**：生产环境各源表的建表/口径定义与加工逻辑。
> 当前为**空的脚手架**：18 个表各一个 `.sql` 文件，仅含表名与待补充说明，字段与逻辑留待逐个填写。
> 每张表的字段口径参照 `../现有真实监控/00_数据字典_DataDictionary.csv` 的登记方式（表名/字段/中文意思/定义含公式/样例/备注）。

---

## 一、文件清单（18 个）

| 分组 | 表名（文件名同） | 大致内容（按表名推断，待核实） |
|------|------------------|-------------------------------|
| **Coupon / 唤回** | `coupon_customer_status_rawdata` | 优惠券客户状态原始数据 |
| | `coupon_daily_raw_list` | 优惠券每日清单原始表 |
| | `ewa_abandoned_winback_email_push` | 弃贷唤回 · 邮件推送记录 |
| | `ewa_abandoned_winback_sms_push` | 弃贷唤回 · 短信推送记录 |
| **Iterable / 触达** | `ewa_iterable_targeting_history` | Iterable 圈选（targeting）历史 |
| | `iterable_dashboard` | Iterable 看板汇总数据 |
| | `iterable_responses` | Iterable 响应数据（送达/打开/点击等） |
| | `iterable_targeting_history` | Iterable 圈选历史（EWA 之外的通用记录） |
| **归因 / 成本 / 画像** | `marketing_cost_actual_split` | 营销费用实际分摊 |
| | `mkt_attribution_first_touch_7d` | 首触归因（7 天窗口） |
| | `mkt_attribution_fundo` | Fundo 归因 |
| | `mkt_customer_profile` | 客户画像 |
| | `mkt_customer_profile_fundo` | 客户画像（Fundo） |
| | `mkt_imp_clk_cost` | 曝光 / 点击 / 成本（全渠道） |
| | `mkt_imp_clk_cost_bing` | 曝光 / 点击 / 成本 · Bing |
| | `mkt_imp_clk_cost_fundo` | 曝光 / 点击 / 成本 · Fundo |
| | `mkt_imp_clk_cost_googlekeywords` | 曝光 / 点击 / 成本 · Google 关键词 |
| | `mkt_t7_funded_forecast` | T+7 放款预测 |

---

## 二、与「现有真实监控」的对应关系（初步）

| 主题 | 本目录源表 | 现有真实监控资产 |
|------|-----------|------------------|
| 媒体曝光/点击/成本 | `mkt_imp_clk_cost` + 各平台拆分表 | 12_媒体投放费用明细_MediaBilling_样例 |
| 归因 | `mkt_attribution_first_touch_7d` / `mkt_attribution_fundo` | 07_触点明细_Touches_样例（多触路径） |
| 客户画像 | `mkt_customer_profile` / `..._fundo` | 06_获客明细主表_Records_样例 |
| 唤起/触达 | `iterable_*` / `ewa_*` | 真实月报层 Owned Channels（CRM 近似） |
| 费用分摊 | `marketing_cost_actual_split` | 08_成本分摊明细_Costs_样例 |
| 放款预测 | `mkt_t7_funded_forecast` | 02_月度放款量_Funded_真实 |

> 对应关系为按表名推断，填写各表口径时核实修正。

---

## 三、填写约定

- 每个文件标注四件事：**表名、用途（支撑看板哪个模块/监控什么）、上游系统、更新频率**
- 字段口径写明类型与公式；日期/布尔/金额格式与 `../现有真实监控/` 的通用约定保持一致
- 后续按域拆分再调整目录结构（保持文件名 = 表名不变）
