# Google 回传监控与看板教程

我查了 Google 目前的官方教程。对于你这个**信贷业务的媒体回传监控**，建议不要只看“Google 有没有收到”，而是搭一套：

> **业务真实事件 → 待回传 → Google 接收 → Google 匹配/归因 → Google Ads 展示**

的端到端监控。

而且有一个 2026 年的重要变化：Google 从 **2026 年 6 月 15 日**开始，把新的 Offline Conversion / Enhanced Conversions for Leads 上传重点迁移到 **Data Manager API**。如果你们现在从 0 建，建议直接按 **Data Manager API + Enhanced Conversions** 设计，不要再以旧的 Google Ads API Offline Conversion Import 作为主方案。([support.google.com](https://support.google.com/google-ads/answer/15713840?hl=en&utm_source=chatgpt.com))

---

# 一、先把整个回传链路画出来

对于你们信贷业务，我建议是：

```text
Google Ads
   │
   │ click
   ▼
Landing Page
   │
   │ gclid / wbraid / gbraid
   ▼
Application
   │
   ├── application_id
   ├── user_id
   └── click_id
   │
   ▼
Risk / Loan System
   │
   ├── Application
   ├── Approval
   ├── Disbursement
   └── Repayment
   │
   ▼
Backend Truth Table
   │
   ▼
Postback Queue / Table
   │
   ▼
Google Data Manager API
   │
   ├── Accepted
   ├── Pending
   └── Error
   │
   ▼
Google Conversion Diagnostics
   │
   ▼
Google Ads Reporting
```

Google 的 Data Manager API 支持把 offline events 发给 Google Ads；事件可以携带 `gclid / gbraid / wbraid`、用户数据、conversion time、conversion value、transaction ID 等。Google 返回的请求中还有 `requestId`，可以作为链路追踪的重要字段。([developers.google.com](https://developers.google.com/data-manager/api/devguides/events/send-events?utm_source=chatgpt.com))

---

# 二、监控最重要的一点：不要只做一个“成功率”

我建议你的监控拆成 **4 层**。

| 层级 | 核心问题 | 示例 |
|---|---|---|
| 业务层 | 该回传的有没有回传 | 1000 个放款，是否都进入回传 |
| 技术层 | 发出去有没有成功 | 980 条请求，多少 Google 接收 |
| 时效层 | 回传够不够快 | 放款后多久发给 Google |
| 归因层 | Google 最终有没有认出来 | Backend 1000 笔，Google Ads 最终识别多少 |

这四层其实对应你之前提到的：

**覆盖率 + 时延 + 一致性 + 成功率。**

---

# 三、第一块看板：Coverage 回传覆盖率

这是最重要的一块。

例如今天真实发生：

```text
Backend truth

Application    10,000
Approval        3,000
Disbursement    2,000
Repayment       1,200
```

你实际准备回传：

```text
Postback

Application     9,950
Approval        2,970
Disbursement    1,960
Repayment       1,180
```

那么：

```text
Coverage
=
已进入回传链路事件数
/
Backend 真实事件数
```

例如：

```text
Disbursement Coverage
=
1960 / 2000
=
98%
```

### 为什么分母一定是 Backend Truth？

因为：

```text
错误做法：

Google 收到 1960
/
你发送 1960
=
100%
```

看起来非常健康。

实际上：

```text
后台真实放款 = 2000
Google 最终只有 1960
```

已经丢了 40 个。

所以真正的监控应该至少分成：

| Metric | 公式 |
|---|---|
| Eligible Coverage | 有 Google identifier 的事件 / Backend Truth |
| Send Coverage | 实际发送 / Backend Truth |
| API Success Rate | Google API Accepted / 实际发送 |
| Ads Coverage | Google 最终识别 / Backend Truth |

这样出问题以后才知道到底在哪一层。

---

# 四、第二块：Latency 回传时延

每一条 conversion 至少保存三个时间：

```text
event_time
send_time
google_response_time
```

例如：

```text
放款时间
10:00:00

系统开始回传
10:03:00

Google 接口返回
10:03:01
```

可以计算：

```text
Postback latency
=
send_time - event_time
```

不要只看平均值。

看：

```text
P50
P90
P99
```

例如：

| Event | P50 | P90 | P99 |
|---|---:|---:|---:|
| Application | 1 min | 4 min | 12 min |
| Approval | 3 min | 15 min | 40 min |
| Disbursement | 5 min | 30 min | 2 hr |

Google 官方特别强调 offline conversion 不应该拖太久；其 Attribution 文档目前建议，为了 Data-Driven Attribution 更稳定，offline conversion upload latency 尽量控制在 **7 天以内**。([support.google.com](https://support.google.com/google-ads/answer/1722023?hl=en&utm_source=chatgpt.com))

但对于你们公司的运维，我不会把 7 天当目标。

我会内部定得明显更严格，例如：

```text
P90 < 30 min     正常
30 min - 1 hr   Warning
> 1 hr          Alert
```

这部分属于你们自己的 SLA，而不是 Google 官方硬性阈值。

---

# 五、第三块：Google API Success

每一笔发送都必须落日志。

我建议至少保存：

```text
application_id
user_id
event_name

event_time
send_time

gclid
gbraid
wbraid

conversion_action_id
conversion_value
currency

request_id

http_status
google_status
error_code
error_message

retry_count
```

然后看：

```text
Total Sent
Successful
Pending
Failed
Success Rate
Retry Rate
```

Google 官方本身也有 Offline Data Diagnostics，可以看到：

- total event count
- successful event count
- pending event count
- success rate
- pending rate
- alerts
- last upload time
- daily summaries
- job summaries

Google Ads API 的 diagnostics 资源甚至可以按 account 和 conversion action 两级查询。([developers.google.com](https://developers.google.com/google-ads/api/docs/conversions/upload-summaries?utm_source=chatgpt.com))

所以你的内部看板最好和 Google 官方 diagnostics 做一次对照。

---

# 六、第四块：Error Distribution

不要只显示：

> Success Rate = 97.8%

一定要再放一个：

## Top Error

比如：

| Error | Count | Ratio |
|---|---:|---:|
| Missing Click ID | 320 | 34% |
| CLICK_NOT_FOUND | 210 | 22% |
| Duplicate Conversion | 130 | 14% |
| Invalid Conversion Action | 80 | 9% |
| Invalid Time | 50 | 5% |
| Other | 150 | 16% |

这样运营/研发看到以后马上知道应该查哪里。

Google 官方也提供 Offline Data Diagnostics 的 Alerts，并且会提示具体问题和 troubleshooting 建议。([support.google.com](https://support.google.com/google-ads/answer/13812240?hl=en&utm_source=chatgpt.com))

---

# 七、第五块：Identifier Coverage

这是我觉得你们特别应该加的一块。

因为 Google 能不能把：

```text
Disbursement
```

认回之前的广告点击，很大程度上取决于有没有有效 identifier。

例如：

```text
gclid
gbraid
wbraid
email / phone 等 user-provided data
```

Google 目前推荐 **Enhanced Conversions for Leads**，就是除了 click ID 之外，再使用经过处理的 first-party customer data 来提高 offline conversion 匹配和归因准确性。([support.google.com](https://support.google.com/google-ads/answer/15713840?hl=en&utm_source=chatgpt.com))

所以应该监控：

| Metric | Result |
|---|---:|
| Application 有 GCLID | 92% |
| Approval 有 GCLID | 91% |
| Disbursement 有 GCLID | 89% |
| 有 Enhanced Conversion user data | 96% |
| 无任何匹配标识 | 2.1% |

如果：

```text
API Success = 100%
```

但：

```text
Identifier Coverage = 70%
```

你的回传其实还是有很大问题。

因为：

> **Google“收到”不等于 Google“成功归因”。**

Google 官方也明确说明，即使 API 返回成功，也不一定代表该 conversion 最终完成 attribution。([developers.google.com](https://developers.google.com/google-ads/api/docs/conversions/upload-offline?authuser=0&hl=en&utm_source=chatgpt.com))

---

# 八、第六块：Google Ads 最终对账

这一步特别容易做错。

假设后台今天：

```text
2026-09-07

Disbursement = 1,000
```

你不能简单拿：

```text
Google Ads 2026-09-07 Conversions
```

直接比较。

因为 Google Ads 默认 conversion reporting 很多指标是按照**广告点击时间**归属的，而不是 conversion 实际发生时间。

比如：

```text
9月1日 click
9月7日 disburse
```

默认 Google Ads 可能把这个 conversion 记回 **9 月 1 日**。

Google 官方对此有明确说明。([developers.google.com](https://developers.google.com/google-ads/api/docs/conversions/legacy_oci_guide?utm_source=chatgpt.com))

---

# 九、正确的 Google 对账方法

Google 官方推荐线下 conversion 对账时使用：

> **All conv. (by conv. time)**

然后：

> segment by **Conversion action**

这样才能按照 conversion 实际发生时间去和你们 Backend 对。([support.google.com](https://support.google.com/google-ads/answer/10029210?hl=en&utm_source=chatgpt.com))

所以你的对账逻辑应该是：

```text
Backend
Disbursement
by event_time
```

vs.

```text
Google Ads
All conv. (by conv. time)

Conversion Action =
Disbursement
```

而不是默认的 Conversions。

---

# 十、还要考虑 Google 自身延迟

这点做告警非常重要。

Google 官方说明，offline conversions 上传后不会立即全部显示。

以 legacy click conversion 文档为例：

> last-click attribution 最多可能需要约 3 小时才能出现在 Google Ads 报表中；其他 attribution model 可能更久。([developers.google.com](https://developers.google.com/google-ads/api/docs/conversions/legacy_oci_guide?utm_source=chatgpt.com))

Google 在其他 conversion reporting 文档中也提醒，部分报表应考虑 **24–48 小时**的数据处理延迟。([support.google.com](https://support.google.com/google-ads/answer/6270625?hl=en&utm_source=chatgpt.com))

所以绝对不能这样告警：

```text
10:00 Backend 放款
10:05 Google 还没有显示

→ 报警
```

这是错误的。

建议：

```text
实时监控
→ API Accepted

T+数小时
→ Google Processing / Diagnostics

T+1
→ Google Ads vs Backend reconciliation
```

---

# 十一、Google 自己其实已经有一个监控页面

如果只是快速检查，不一定一开始就自己开发。

Google Ads 里面可以：

```text
Goals
↓
Summary
↓
找到 Conversion Action
↓
Status
↓
Diagnostics
```

里面可以看到：

```text
Data quality

Excellent
Good
Needs attention
No recent data

+
Alerts
```

Google 官方的 Enhanced Conversion Diagnostics 也可以直接看当前 tag / API 数据质量。([support.google.com](https://support.google.com/google-ads/answer/11956168?hl=en&utm_source=chatgpt.com))

另外 Data Manager 的 Connections 页面也有：

```text
Healthy

Needs attention

Urgent
```

这样的连接状态诊断。([support.google.com](https://support.google.com/google-ads-data-manager/answer/13944740?hl=en&utm_source=chatgpt.com))

---

# 十二、但公司内部还是应该自己建 Dashboard

如果是你让我从 0 搭，我会直接做下面这个页面。

## Google Postback Monitoring

```text
┌─────────────────────────────────────────────────────┐
│                Google Postback Health               │
│                                                     │
│ Backend Events  Sent  Accepted  Google Matched      │
│    10,000       9,850    9,800       9,420          │
│                                                     │
│ Coverage      API Success      Match Rate    P90    │
│   98.5%          99.5%           94.2%       18m    │
└─────────────────────────────────────────────────────┘
```

第二行：

```text
┌─────────────────────────┐ ┌─────────────────────────┐
│ Coverage Trend          │ │ Postback Latency        │
│                         │ │                         │
│ Application             │ │ P50                     │
│ Approval                │ │ P90                     │
│ Disbursement            │ │ P99                     │
└─────────────────────────┘ └─────────────────────────┘
```

第三行：

```text
┌─────────────────────────┐ ┌─────────────────────────┐
│ Error Distribution      │ │ Identifier Coverage     │
│                         │ │                         │
│ Missing GCLID           │ │ GCLID                   │
│ Click not found         │ │ WBRAID                  │
│ Duplicate               │ │ GBRAID                  │
│ Invalid Time            │ │ Enhanced Data           │
└─────────────────────────┘ └─────────────────────────┘
```

第四行：

```text
┌─────────────────────────────────────────────────────┐
│               Backend vs Google                     │
│                                                     │
│          Backend   Google    Diff    Match Rate     │
│ Application 10k     9.6k    -400      96%          │
│ Approval     3k     2.85k   -150      95%          │
│ Disbursed    2k     1.88k   -120      94%          │
└─────────────────────────────────────────────────────┘
```

---

# 十三、我建议你最终固定成“四维看板”

和你之前设计的回传监控方向基本一致：

| 模块 | 核心指标 | 回答的问题 |
|---|---|---|
| **Coverage** | Backend / Sent / Google | 有没有漏传 |
| **Latency** | P50 / P90 / P99 | 回传够不够及时 |
| **Quality** | Success / Error / Retry | 技术链路有没有问题 |
| **Consistency** | Backend vs Google | Google 最终认了多少 |

然后最上面加四个总指标：

```text
Coverage
98.6%

P90 Latency
23 min

API Success
99.7%

Google Match Rate
94.1%
```

管理层看这一行基本就够。

研发再往下面钻。

---

# 十四、表结构建议

我会至少建三张表。

### `google_conversion_truth`

```text
application_id
user_id
event_name
event_time
event_value
event_status
```

这是 **Backend Truth**。

### `google_postback_log`

```text
application_id
event_name

gclid
gbraid
wbraid

event_time
send_time

conversion_action_id
conversion_value

request_id
response_status
error_code
error_message

retry_count
```

这是 **发送日志**。

### `google_conversion_report`

```text
date
campaign_id
ad_group_id
conversion_action

all_conversions_by_conversion_time
conversion_value
```

这是 Google Ads 拉回来的数据。

最后做：

```text
Truth
   ↓
LEFT JOIN
Postback
   ↓
LEFT JOIN
Google Report
```

这样就能完成真正的端到端对账。

---

# 十五、你们信贷业务最好再多做一层

普通电商只需要：

```text
Purchase
```

但你们不是。

建议按：

```text
Application
↓
Approval
↓
Disbursement
↓
Repayment
```

分别监控。

最终看：

```text
              Backend   Sent   Google

Application    10000    9950    9600
Approval        3000    2970    2850
Disbursement    2000    1960    1880
Repayment       1200    1170    1080
```

这样一眼就能看到：

> **到底在哪一个业务阶段开始大量丢数据。**

---

# 十六、完整架构我建议做到这个程度

```text
                      Google Ads
                          │
                        Click
                          │
                          ▼
                GCLID / WBRAID / GBRAID
                          │
                          ▼
                     Application
                          │
                          ▼
                  Backend Truth Table
                          │
               ┌──────────┴──────────┐
               │                     │
          Risk / Loan             Tracking
               │                     │
        Approval / Loan        attribution ID
               │                     │
               └──────────┬──────────┘
                          │
                          ▼
                  Postback Event Table
                          │
                          ▼
                  Postback Service
                          │
                          ▼
                 Google Data Manager API
                          │
                ┌─────────┴─────────┐
                │                   │
             Success              Error
                │                   │
                ▼                   ▼
           Diagnostics        Retry / Alert
                │
                ▼
                 Google Ads Reporting
                          │
                          ▼
                   Reconciliation
                          │
                          ▼
                       Dashboard
```

我认为这才是一套真正完整的**媒体回传基础设施**，而不是单纯做一个 Google Ads 转化报表。

---

## 官方教程最值得你看的 5 个

[Google：Offline data diagnostics](https://support.google.com/google-ads/answer/13812240?hl=en&utm_source=chatgpt.com)

[Google：Enhanced conversions for leads](https://support.google.com/google-ads/answer/15713840?hl=en&utm_source=chatgpt.com)

[Google Developers：Data Manager API Send Events](https://developers.google.com/data-manager/api/devguides/events/send-events?utm_source=chatgpt.com)

[Google：Offline conversion discrepancies & errors](https://support.google.com/google-ads/answer/13321563?hl=en&utm_source=chatgpt.com)

[Google Developers：Monitor offline conversion diagnostics](https://developers.google.com/google-ads/api/docs/conversions/upload-summaries?utm_source=chatgpt.com)

如果把它变成你们公司的项目，我建议第一阶段就做成：**一张对账底表 + 四维看板 + 告警 + application_id 端到端追踪**。这样既能发现“漏传”，也能区分到底是**业务源头、回传服务、Google 接收还是 Google 归因**出了问题。
