# 现有真实监控 · 数据准备清单

> 本目录是「信贷投放与归因监控中心」看板的数据底座，看板文件见 `../04_工具_信贷投放与归因监控中心.html`。
> 用途：对照看板全部 **13 个监控模块**，明确已有真实数据与**还需准备的真实数据**；缺失部分已按看板数据契约生成样例 Excel（文件名带 `_样例`），照此格式准备真实数据即可。
> 样例数值全部为虚构，不代表业务水平；替换为真实数据后建议去掉文件名中的 `_样例` 后缀。
> **全字段数据字典**见 `00_数据字典_DataDictionary.csv`：16 张表 147 个字段的长表，含中文意思、定义（含公式）、数据样例与备注。

---

## 〇、文件命名规范

所有数据文件统一采用：**`序号_中文主题_英文表名_数据状态.xlsx`**

| 部分 | 规则 | 示例 |
|------|------|------|
| 序号 | 两位数字，真实月报层 01~05，明细样例层 06~10，配套输入 11~12，上游源表与口径确认 13~16 | `03_`、`14_` |
| 中文主题 | 一眼看出监控什么 | `月度放款成本`、`回传事件时戳明细` |
| 英文表名 | 与看板 JSON 契约的表名/来源 ID 一致（Leads/Funded/CPFL/GreenPct/Y26KPI/Records/Touches/Costs/Postbacks/Jobs/Experiment/MediaBilling/GreenN/PostbackTimestamps/GoogleAdsReport/GeoExperiment） | `CPFL`、`Postbacks` |
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
| 3. 渠道与信贷质量 | 真实 Leads/Funded/Green%（01/02/04）✅；Green 样本量（13）；转化漏斗与风险（06） | ⚠️ 明细层缺失 |
| 4. ROI / LTV | 06 获客明细的价值字段（interest/fees/ltv 等） | ⚠️ 缺失 |
| 5. 自主归因 | 06 获客明细 + 07 触点明细（多触点路径、归因模型） | ⚠️ 缺失 |
| 6. Google 归因 | 真实 Google 列 ✅；09 回传日志 + 07 触点（资格与对账）；15 平台对账报表 | ⚠️ 明细层缺失 |
| 7. 渠道协同与蚕食 | 07 触点明细（跨渠道路径、First/Assist/Last） | ⚠️ 缺失 |
| 8. 增量与预算 | 11 实验 Holdout（手工输入）；16 Geo Lift 地域实验（证据方法） | ⚠️ 缺失 |
| 9. 回传监控 | 09 回传日志（链路、字段一致性）+ 14 事件时戳（P90 时延上游） | ⚠️ 缺失 |
| 10. 系统健康 | 10 系统任务 SLA + 真实源快照 ✅ | ⚠️ 部分缺失 |
| 11. 告警中心 | 无需单独数据——由真实月报阈值（CPFL 涨幅/放款跌幅/Green 跌幅）与明细异常自动派生 | ✅ 派生 |
| 12. 单笔追踪 | 06+07+08+09 按 application_id / loan_id 联查 | ⚠️ 明细层缺失 |
| 13. 指标字典 | 静态定义 ✅；口径确认见第四节 | ✅ 静态 |

---

## 三、缺失数据的样例文件说明（11 份）

> 明细层 06~10 可组装为 `schemaVersion=2` 的 JSON 快照导入看板；列名已与看板 JSON 契约字段名完全一致（camelCase），无需改名。
> 通用约定：日期为文本 `YYYY-MM-DD`；布尔写 `TRUE`/`FALSE`；空值留空（代表 null）；金额为 AUD 两位小数。
> 13~16 为**上游源表与口径确认文件，不直接导入看板**，用于补全看板词典点名的缺失口径与对账证据。

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

### 13_月度渠道质量样本量_GreenN_样例.xlsx（24 行）— Green 口径确认

看板词典点名：真实 Green 表「缺样本量及分层定义」、告警中心提示「原表未提供样本分母」。

| 字段 | 说明 |
|------|------|
| month / channel | 月份（`YYYY-MM`）/ 渠道（与 04 一致） |
| green_n / orange_n / red_n / na_n | 各分层样本数；四列合计 = 该渠道当月判定样本总量 |

- **样例与 04 文件比例对齐**（取 04 最后 3 个月 2026-01~03，按渠道选择样本总量后按比例拆分，误差 ≤0.5pp 舍入）
- 真实数据准备：提供每渠道每月的**判定样本总量与各层计数**，用于核验 Green% 分母、判断小样本渠道（如 Tiktok/Meta 不足百笔）占比是否可信
- 不直接导入看板；确认分层定义与样本口径后，可支撑「Green% 变化是否由结构变化驱动」的告警核查

### 14_回传事件时戳明细_PostbackTimestamps_样例.xlsx（57 行）— P90 时延上游

看板词典注明：P90 首次发送时延「正式需 event_time/first_sent_time」。

| 字段 | 说明 |
|------|------|
| eventId / businessKey / event | 与 09 一致（仅已发送事件） |
| eventTime | 业务事件发生时间（`YYYY-MM-DD HH:MM`，Sydney 本地时间） |
| firstSentTime | 首次发送时间（事件时间 + 发送时延） |
| latencyMin | 时延分钟数（firstSentTime − eventTime，与 09 的 latency 一致） |

- **组装 JSON 时只保留 09 的 latency 字段**；本表是上游加工模板，真实数据的 latency 应从事件日志时戳算出，不把上传日当事件日
- 样例 57 行与 09 中 sent=TRUE 的行一一对应，时延值完全一致

### 15_Google平台对账报表_GoogleAdsReport_样例.xlsx（32 行）— Google 归因对账

看板 Google 模块明确「未伪造广告平台 DDA 报表」——平台侧数据需从 Google Ads 后台导出，与本表格式一致。

| 字段 | 说明 |
|------|------|
| month / campaign | 月份 / Campaign（与 12 的 Google 行一致） |
| conversionAction | 转化动作（application_submitted / qualified_lead / application_approved / loan_funded） |
| currency | 币种 |
| cost | 该 Campaign 当月费用（样例与 12 的 mediaCost 对齐；**平台导出按动作行重复，加总时需按 Campaign 去重**） |
| clicks | 点击（与 12 对齐） |
| conversions / conversionValue | 平台统计的转化次数 / 转化价值（样例 loan_funded 按 7500 AUD/笔） |

- 对账用法：把 15 的平台 conversions 与 09 内部回传的 Reported 对比（见看板「按 Conversion Action 对账」），差异即归因丢失/重复的来源
- **平台数与内部数允许不一致**（口径不同：平台 DDA 归因 vs 公司业务键），差异要解释而不是抹平

### 16_地域实验GeoLift_GeoExperiment_样例.xlsx（6 行）— 增量证据方法

看板证据表点名：「未提供真实地域试验」。

| 字段 | 说明 |
|------|------|
| experimentId / experimentName | 实验编号 / 名称 |
| region | 地域（州） |
| group | test（投放增量）/ control（维持原投放） |
| periodStart / periodEnd | 实验期 |
| prePeriodFirstLoans | 实验前同周期首贷基线（用于基线平衡检查） |
| mediaSpendAud | 实验期媒体费 AUD |
| firstLoanUsers | 实验期新客首贷数 |
| contributionAud | 实验期贡献 AUD（不含本金） |

- 看板「增量与预算」不直接导入本表；结果用于证据表的 Geo Lift 行（按地域聚类推断，需统计工具出区间估计）
- 验证重点：地域随机化、基线平衡（test/control 的 prePeriod 差异）、跨区污染（用户跨州）

---

## 四、待确认口径清单（看板「指标字典」目前标记为待确认）

| 口径项 | 含义 | 确认建议 |
|--------|------|----------|
| currency | 币种 | 由 12 文件的 currency 列确认（样例按 AUD） |
| kpiNature | Y26KPI 的性质 | 与业务负责人确认是目标/预测/实际值 |
| greenDefinition | Green/Orange/Red/NA 的定义 | 由 13 的样本量数据支撑，确认各档业务定义与判定来源 |
| cpflCostScope | CPFL 分子费用范围 | 确认是否仅媒体费、是否含代理费/工具费（可对照 12） |
| dateBasis | 月份日期基准 | 确认自然月/账单周期/数据提取日 |
| leadsDefinition | Leads 去重口径 | 确认 01 的 Leads 是用户/申请、是否去重 |
| fundedScope | Funded 首贷/复贷范围 | 确认 02 的 Funded 计贷款数还是客户数、是否含复贷 |

**渠道映射（真实月报层 ↔ 明细快照层，口径待确认）：**

| 真实月报层 | 明细快照层 | 说明 |
|-----------|-----------|------|
| Google | Google Search + Google PMax | 按 Campaign 拆分 |
| Meta | Meta | 一致 |
| Tiktok | TikTok | 一致 |
| Organic | Organic | 一致 |
| Owned Channels | CRM（近似） | 归属规则需确认（推送/站内信/邮件） |
| Lead Partner | Affiliate（近似） | 归属规则需确认 |
| Bing | —（明细层无对应渠道） | 明细层 CH 不含 Bing，导入前需决定归属 |
| GEO | —（明细层无对应渠道） | 应用商店流量，同上 |
| — | Direct（明细层独有） | 真实月报层未单列 |

---

## 五、真实数据准备顺序建议

1. **P0 — 06 获客明细主表**：一张表打通转化漏斗、风险与用户、ROI/LTV、单笔追踪四个模块，价值最高
2. **P1 — 07 触点明细 + 08 成本分摊明细**：解锁自主归因、渠道协同、投放效率
3. **P2 — 09 回传日志 + 14 事件时戳**：解锁回传监控、Google 归因诊断（时延指标）
4. **P3 — 10 系统任务 SLA + 11 实验 Holdout + 16 Geo Lift + 15 平台报表**：系统健康、增量验证、对账证据
5. **P4 — 12 媒体账单 + 13 样本量**：CPFL 与 Green 口径确认，堵上真实月报层的口径缺口

准备完成后：将 06~10 按看板「数据接入」对话框的 schemaVersion=2 契约组装为 JSON 快照（列名一致，可直接转换），导入即可替换看板内的 Sample Data。组装时需附 meta 元数据块：

```
meta = {
  schemaVersion: 2,                       // 固定
  asOf: "<快照日期 YYYY-MM-DD>",          // 数据快照时点
  currency: "AUD",                        // 币种（口径确认后填写）
  timezone: "Australia/Sydney",           // 固定
  valuationVersion: "<价值版本号>",        // 由模型负责人提供
  costBasis: "acquisition_cohort_allocated", // 固定口径
  dataClass: "real",                      // 替换样例后改为 real；样例为 sample
  mode: "<显示名称>"                       // 看板顶栏显示的数据来源名
}
```

---

## 六、样例文件约定（重要边界）

- 所有 `_样例` 文件数值为虚构演示，**绝不与 5 份真实月报混算**（看板也强制两层隔离）
- 替换真实数据时保持表名（sheet 名）、列名、类型约定不变，并按第〇节规范重命名（`_样例` → `_真实`）
- 看板证据表提到的 **MMM（营销组合模型）不单独成表**：MMM 需要 01/02/12 的历史月度序列 + 季节、定价、风控策略变更等外部因子，属于建模项目输入，先准备好 01/02/12 的历史数据即可启动
- 生产数据接入应在受控后端完成权限、脱敏、调度与审计；本看板与样例均不含账户密钥
