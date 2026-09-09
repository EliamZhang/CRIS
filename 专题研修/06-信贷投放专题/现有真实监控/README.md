# 现有真实监控 · 数据准备清单

> 本目录是「信贷投放与归因监控中心」看板的数据底座，看板文件见 `../04_工具_信贷投放与归因监控中心.html`。
> 用途：对照看板全部 **13 个监控模块**，明确已有真实数据与**还需准备的真实数据**；缺失部分已按看板数据契约生成样例 Excel（文件名带 `_样例`），照此格式准备真实数据即可。
> 样例数值全部为虚构，不代表业务水平；替换为真实数据后建议去掉文件名中的 `_样例` 后缀。

---

## 〇、文件命名规范

所有数据文件统一采用：**`序号_中文主题_英文表名_数据状态.xlsx`**

| 部分 | 规则 | 示例 |
|------|------|------|
| 序号 | 两位数字，真实月报层 01~05，明细样例层 06~12（按看板模块依赖顺序） | `03_`、`09_` |
| 中文主题 | 一眼看出监控什么 | `月度放款成本`、`回传日志` |
| 英文表名 | 与看板 JSON 契约的表名/来源 ID 一致（Leads/Funded/CPFL/GreenPct/Y26KPI/Records/Touches/Costs/Postbacks/Jobs/Experiment/MediaBilling） | `CPFL`、`Postbacks` |
| 数据状态 | `真实` = 已接入的真实数据；`样例` = 待替换为真实数据的格式模板 | `_真实.xlsx`、`_样例.xlsx` |

- 替换真实数据时保持序号与英文表名不变，仅将 `_样例` 改为 `_真实`
- 同一张表拆成多个文件时（如按月份分文件），在状态后缀前追加 `_2026M01` 等期间标识

---

## 一、看板数据架构（两层）

| 数据层 | 契约标识 | 现状 | 支撑的模块 |
|--------|----------|------|-----------|
| 真实月报层 | `schemaVersion = monthly-monitor-v1` | ✅ 已接入 5 份真实 Excel（下表） | 经营总览、渠道表现、CPFL与费用、Google经营、渠道结果归属、告警（真实阈值部分）、指标字典 |
| 明细快照层 | `schemaVersion = 2`（records / postbacks / jobs） | ⚠️ 看板目前只有内嵌 Sample Data，**真实明细待准备** | 转化漏斗、风险与用户、投放效率、ROI/LTV、归因模型/质量、渠道协同、回传监控、单笔追踪、增量、系统健康 |

**已接入的 5 份真实月报（勿重复准备）：**

| 文件 | 内容 | 看板中的用途 |
|------|------|--------------|
| 01_月度线索量_Leads_真实.xlsx | 月度线索量 × 渠道 | 渠道表现、Google 经营、告警阈值 |
| 02_月度放款量_Funded_真实.xlsx | 月度放款量 × 渠道 | 同上 |
| 03_月度放款成本_CPFL_真实.xlsx | 月度 CPFL（总/Google/Bing/Lead Partner） | 投放与成本（CPFL 监控） |
| 04_月度渠道质量_GreenPct_真实.xlsx | 月度渠道绿/橙/红/NA 占比 | 渠道与信贷质量（真实部分） |
| 05_年度KPI参照_Y26KPI_真实.xlsx | 年度 KPI 参照（转化率/审批率/规模等） | 经营总览 KPI 参照、指标字典 |

---

## 二、13 个模块 × 数据需求对照

| 模块 | 需要的数据 | 现状 |
|------|-----------|------|
| 1. 经营总览 | 真实月报（01~05）+ 获客明细（06） | ✅真实 + ⚠️明细待准备 |
| 2. 投放与成本 | 真实 CPFL（03）✅；首访 CPC/CPM/CTR（06+08 明细）；上游媒体账单（12） | ⚠️ 明细层缺失 |
| 3. 渠道与信贷质量 | 真实 Leads/Funded/Green%（01/02/04）✅；转化漏斗与风险（06） | ⚠️ 明细层缺失 |
| 4. ROI / LTV | 06 获客明细的价值字段（interest/fees/ltv 等） | ⚠️ 缺失 |
| 5. 自主归因 | 06 获客明细 + 07 触点明细（多触点路径、归因模型） | ⚠️ 缺失 |
| 6. Google 归因 | 真实 Google 列 ✅；09 回传日志 + 07 触点（资格与对账） | ⚠️ 明细层缺失 |
| 7. 渠道协同与蚕食 | 07 触点明细（跨渠道路径、First/Assist/Last） | ⚠️ 缺失 |
| 8. 增量与预算 | 11 实验 Holdout 结果（看板为手工输入，无需改 HTML） | ⚠️ 缺失 |
| 9. 回传监控 | 09 回传日志（链路、P90 时延、字段一致性） | ⚠️ 缺失 |
| 10. 系统健康 | 10 系统任务 SLA + 真实源快照 ✅ | ⚠️ 部分缺失 |
| 11. 告警中心 | 无需单独数据——由真实月报阈值（CPFL 涨幅/放款跌幅/Green 跌幅）与明细异常自动派生 | ✅ 派生 |
| 12. 单笔追踪 | 06+07+08+09 按 application_id / loan_id 联查 | ⚠️ 明细层缺失 |
| 13. 指标字典 | 静态定义 ✅；口径确认见第四节 | ✅ 静态 |

---

## 三、缺失数据的样例文件说明（7 份）

> 明细层 06~10 可组装为 `schemaVersion=2` 的 JSON 快照导入看板；列名已与看板 JSON 契约字段名完全一致（camelCase），无需改名。
> 通用约定：日期为文本 `YYYY-MM-DD`；布尔写 `TRUE`/`FALSE`；空值留空（代表 null）；金额为 AUD 两位小数。

### 06_获客明细主表_Records_样例.xlsx（60 行）— 明细层核心主表

每个首访获客实体一行（新客一人一首贷；老客可跨实体复用 userId，样例中 USR-2016/USR-2031/USR-2044 各出现 2 次）。

| 字段 | 说明 | 字段 | 说明 |
|------|------|------|------|
| id | 获客实体 ID，全表唯一 | funded | 放款日期（未放款留空） |
| userId | 用户 ID，新客全表唯一 | impressions / clicks / sessions | 首访媒体曝光/点击/会话 |
| applicationId | 申请 ID（提交申请后才有） | loanAmount | 放款本金（未放款为 0） |
| loanId | 贷款 ID（放款后才有） | interest / fees | 生命周期利息/费用预测 |
| cohort | 首访日期（`YYYY-MM-DD`） | fundingCost / servicingCost | 资金成本/服务成本 |
| channel | 首访渠道（8 个固定值，见下） | expectedLoss | 预期信用损失 |
| campaign | 首访 Campaign | ltv | 上游折现贡献预测（未放款为 0） |
| brand | brand / nonbrand / na（仅 Google Search 区分） | fraud | 已确认欺诈 TRUE/FALSE（未提交申请留空） |
| customer | new / old | firstDue / m1bad | 首期应还日 / 首期 30+ 逾期标签 |
| region / device / product | NSW/VIC/QLD；mobile/desktop；fixed/loc | thirdDue / m3bad | 第三期应还日 / 第三期 30+ 逾期标签 |
| started / submitted / qualified / approved | 漏斗阶段日期（逐级非空） | | |

- **渠道固定值**：Google Search、Google PMax、Meta、TikTok、Affiliate、CRM、Organic、Direct
- **风险标签成熟度规则（重要）**：`m1bad`/`m3bad` 只有在「应还日 + 30 天 ≤ 快照日期（asOf）」时才填 TRUE/FALSE，否则**必须留空**（未成熟）；样例 asOf = 2026-09-07，5 月放款的贷款 m3 已成熟、8 月放款的全部留空，可对照参考
- 未放款记录：loanAmount 与全部金额/价值字段为 0，applicationId 之后阶段留空

### 07_触点明细_Touches_样例.xlsx（78 行）— 自主归因 / 渠道协同

| 字段 | 说明 |
|------|------|
| recordId | 关联 06 的 id |
| touchId | 触点 ID（同实体内唯一；样例 V-2028 有两条完全相同触点，演示看板去重） |
| day | 触点日期，≥ cohort、≤ asOf |
| channel / campaign | 触点渠道 / Campaign |
| brand | brand / nonbrand / na |
| kind | click（付费渠道）/ session（自然、自有、Direct） |
| consent | 是否获得同意（V-2023 全部 FALSE、V-2015 的品牌搜索触点 FALSE，演示资格缺失场景） |

- **每实体的第一条触点必须与主表 cohort/channel/campaign/brand 完全一致**（看板以此校验首访维度）
- 样例含多触路径（Meta→品牌搜索→Direct、Organic→搜索→Organic 等），供协同/归因模型演示

### 08_成本分摊明细_Costs_样例.xlsx（76 行）— 投放效率 / ROAS 分母

| 字段 | 说明 |
|------|------|
| recordId | 关联 06 的 id |
| channel / campaign | 分摊到哪个渠道/Campaign |
| amount | 分摊金额 AUD（**获客 Cohort 分摊口径，不是媒体日账单**） |

- Organic / Direct 为 0 成本（看板以「—」显示，不当作免费获客优势）
- 每个渠道/Campaign 组合一行；样例金额按渠道量级虚构（Google Search 9~27、Meta/TikTok 15~47、CRM 1~3.7）

### 09_回传日志_Postbacks_样例.xlsx（153 行）— 回传监控 / Google 归因

| 字段 | 说明 |
|------|------|
| recordId | 关联 06 的 id |
| businessKey | **业务ID:事件**（funded 用 loanId，其余事件用 applicationId） |
| eventId | 事件 ID |
| event / day | 事件类型 / 业务发生日期（须等于主表对应阶段日期） |
| eligible | 有 Google 资格（30 天内带 consent 的 Google 触点） |
| matchable | 可匹配到业务键（样例含 2 行 eligible=T 但 matchable=F 的异常） |
| queued / sent / accepted / processed / reported | 子集链路，后级为 TRUE 则前级必须 TRUE |
| rawCount | 原始回传计数（含重复；V-2028 的 funded 为 2，演示重复回传） |
| mmp | 是否 MMP 确认 |
| latency | 首次发送时延（分钟），仅 sent=TRUE 时有值 |
| amountOk / statusOk / timeOk | 金额/状态/时间一致性（样例含各 1 行 FALSE 的异常） |

- **每个已发生的业务事件必须有且仅有一行，包括无 Google 资格的事件**（Organic/CRM/Direct 的事件 eligible=FALSE 也要列全）——看板拒绝选择性日志
- 事件距 asOf 不足 3 天时 reported 应为 FALSE（T+3 观察期，见 V-2008、V-2021）

### 10_系统任务SLA_Jobs_样例.xlsx（7 行）— 系统健康

| 字段 | 说明 |
|------|------|
| name / owner | 任务名 / 归属团队 |
| freshness / sla | 数据新鲜度（分钟）/ SLA 阈值（分钟） |
| success | 成功率（0~100 数值，不带 %） |

- 样例含 1 行 freshness 超 SLA（Platform Cost Ingestion），演示「超时」状态

### 11_增量实验Holdout_Experiment_样例.xlsx（4 行）— 增量与预算

| 字段 | 说明 |
|------|------|
| experimentId / experimentName | 实验编号 / 名称 |
| group | test / control |
| periodStart / periodEnd | 实验期 |
| assignedUsers | 组内分配用户数（N） |
| firstLoanUsers | 组内新客首贷数（Y） |
| adSpendAud / contributionAud | 组内广告费 / 贡献（AUD，不含本金） |

- **注意**：看板「增量与预算」模块为手工输入（nt/nc/yt/yc/st/sc/vt/vc 八个值），本文件用于记录真实 Holdout 结果，填写后手动录入看板即可，无需改 HTML
- 对照组的 adSpend 可为 0（渠道关闭实验），看板会以「—」处理非正分母

### 12_媒体投放费用明细_MediaBilling_样例.xlsx（36 行）— 口径确认源表

| 字段 | 说明 |
|------|------|
| month | 月份（`YYYY-MM`，与真实月报文件一致） |
| channel / campaign | 渠道 / Campaign（含真实月报层的 Bing、Lead Partner、GEO、Owned Channels） |
| currency | 币种（样例为 AUD——即第四节「currency 待确认」的确认入口） |
| mediaCost | 媒体费（**媒体服务日账单口径**，与 08 的 Cohort 分摊口径不同，勿混算） |
| impressions / clicks | 曝光 / 点击（可复算 CPM/CTR/CPC） |

- **不是看板直接导入文件**：用于确认 CPFL 费用范围、币种、日期基准，并核对 CPFL 上游来源

---

## 四、待确认口径清单（看板「指标字典」目前标记为待确认）

| 口径项 | 含义 | 确认建议 |
|--------|------|----------|
| currency | 币种 | 由 12 文件的 currency 列确认（样例按 AUD） |
| kpiNature | Y26KPI 的性质 | 与业务负责人确认是目标/预测/实际值 |
| greenDefinition | Green/Orange/Red/NA 的定义 | 确认各颜色档的业务定义与判定来源 |
| cpflCostScope | CPFL 分子费用范围 | 确认是否仅媒体费、是否含代理费/工具费 |
| dateBasis | 月份日期基准 | 确认自然月/账单周期/数据提取日 |

---

## 五、真实数据准备顺序建议

1. **P0 — 06 获客明细主表**：一张表打通转化漏斗、风险与用户、ROI/LTV、单笔追踪四个模块，价值最高
2. **P1 — 07 触点明细 + 08 成本分摊明细**：解锁自主归因、渠道协同、投放效率
3. **P2 — 09 回传日志**：解锁回传监控、Google 归因诊断
4. **P3 — 10 系统任务 SLA + 11 实验 Holdout + 12 媒体账单**：系统健康、增量验证、口径确认

准备完成后：将 06~10 按看板「数据接入」对话框的 schemaVersion=2 契约组装为 JSON 快照（列名一致，可直接转换），导入即可替换看板内的 Sample Data。

---

## 六、样例文件约定（重要边界）

- 所有 `_样例` 文件数值为虚构演示，**绝不与 5 份真实月报混算**（看板也强制两层隔离）
- 替换真实数据时保持表名（sheet 名）、列名、类型约定不变，并按第〇节规范重命名（`_样例` → `_真实`）
- 生产数据接入应在受控后端完成权限、脱敏、调度与审计；本看板与样例均不含账户密钥
