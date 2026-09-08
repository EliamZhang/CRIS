# 澳大利亚信贷产品 Google Ads 0→1 投放教程

可以。下面按你现在最需要理解的方式来讲：**假设你要在澳大利亚从 0 开一个新的消费信贷产品，然后通过 Google Ads 获取新客。**

先记住一句话：

> **Google 投放不是“建个广告 → 买流量”，而是“产品 → 页面 → 流量 → 申请 → 风控 → 放款 → 数据回传 → Google 自动找更好的客户”的完整闭环。**

---

# 一、先理解整个 0→1 流程

整个链路其实只有 8 步：

```text
① 定义信贷产品
        ↓
② 合规 / Google 金融资质
        ↓
③ 建 Landing Page / 申请流程
        ↓
④ Google Ads + 数据埋点
        ↓
⑤ 建 Search Campaign
        ↓
⑥ 用户搜索 → 点击 → 申请
        ↓
⑦ 风控 → Approval → Disbursement
        ↓
⑧ 把结果回传 Google
        ↓
Google 学习什么样的人更容易放款
        ↓
继续投放 / 优化 / 放量
```

真正重要的是 **⑧ → ⑤ 这个闭环**。

---

# 二、Step 1：先把“我要卖什么”定义清楚

不要先开 Google Ads。

第一件事是写一个非常简单的 **Product Brief**。

例如你要上线一个 Personal Loan，需要至少确定：

| 项目 | 你需要确定什么 |
|---|---|
| 产品 | Personal Loan / LOC / 其他 |
| Target Customer | 什么用户 |
| Loan Amount | 额度范围 |
| Term | 借多久 |
| Interest / Fee | 利率和费用 |
| Eligibility | 谁可以申请 |
| Risk Policy | 什么客户拒绝 |
| Approval | 怎么审批 |
| Disbursement | 怎么放款 |
| Repayment | 怎么还款 |

然后明确一个核心商业公式：

**获客成本 < 客户价值**

例如：

```text
Google Spend
    ↓
Click
    ↓
Application
    ↓
Approval
    ↓
Disbursement
    ↓
Interest / Revenue
    ↓
Credit Loss
    ↓
Profit
```

所以以后不能只看 CPC。

最终你应该关注：

> **Cost per Disbursement + Loan LTV / ROI**

---

# 三、Step 2：先解决合规，否则 Google 都可能不给你投

如果是在澳大利亚做 consumer credit，一般需要持有 Australian Credit Licence，或者获得持牌机构授权后才能开展相应 credit activity。ASIC 同时要求贷款机构履行 Responsible Lending 义务，例如了解客户财务情况、核实相关信息，并判断贷款是否不适合该客户。

参考：
- ASIC — Do you need a credit licence?  
  https://asic.gov.au/for-finance-professionals/credit-licensees/do-you-need-a-credit-licence/

而 Google 对澳大利亚金融广告还有单独的 **Financial Services Verification**。

目前澳大利亚的流程大致是：

```text
ASIC / 对应监管资质
        ↓
第三方 G2RS Verification
        ↓
Google Advertiser Verification
        ↓
Google Financial Services Verification
        ↓
Ads Account 获得金融服务投放资格
```

Google 明确要求，在澳大利亚向寻找金融服务的用户展示广告，广告主通常需要完成金融服务验证；Google 会核实监管授权或豁免情况。

参考：
- Google Ads Policy — Australia Financial Services Verification  
  https://support.google.com/adspolicy/answer/15332527?hl=zh-Hans

所以公司内部通常要先找：

**Legal / Compliance + Google Ads Account Owner**

确认：

```text
ACL / licence
Google Advertiser Verification
Google Financial Service Verification
Domain
Advertiser Entity
Payment Profile
```

全部是谁的。

---

# 四、Step 3：把 Landing Page 做出来

Google 广告最终要把用户送到一个页面。

比如：

```text
Google 搜索：
"personal loan australia"

        ↓

广告：
Flexible Personal Loans
Apply Online

        ↓

Landing Page

Personal Loan
[产品介绍]

Loan amount
Loan term
Fees
Eligibility

[Check eligibility]
```

这里有个非常重要的问题。

**金融产品不能只做一个漂亮 Landing Page。**

Google 要求金融服务页面明确披露企业实际地址和相关费用等信息；个人贷款还需要醒目披露最短/最长还款期限、最高 APR 以及代表性的贷款总成本示例。并且 Google 只允许宣传要求在放款后 **61 天或更长时间**才能全额还清的 personal loans。

参考：
- Google Ads Policy — Personal loans  
  https://support.google.com/adspolicy/answer/15187149?hl=en

ASIC 在 2026 年更新的 RG 234 也强调，金融产品和信贷广告不得误导消费者。

参考：
- ASIC RG 234 — Advertising financial products and services, including credit  
  https://www.asic.gov.au/regulatory-resources/find-a-document/regulatory-guides/rg-234-advertising-financial-products-and-services-including-credit

所以 Landing Page 通常至少包含：

```text
Product information
Loan amount
Term
Rate / Fee
Representative example
Eligibility
Responsible lending information
Company information
ACL / regulatory information
Privacy Policy
Terms & Conditions
Contact
```

---

# 五、Step 4：设计用户申请 Funnel

这一层其实就是你比较熟悉的信贷业务。

用户点广告以后：

```text
Google
 ↓
Landing Page
 ↓
Apply
 ↓
手机号 / Email
 ↓
基本个人信息
 ↓
Employment
 ↓
Income
 ↓
Bank Statement / Open Banking
 ↓
Credit Bureau
 ↓
Risk Model
 ↓
Decision
 ↓
Approved / Declined
 ↓
Disbursement
```

这个时候，你需要给每一步定义 **event**。

例如：

| Event | 含义 |
|---|---|
| page_view | 到页面 |
| apply_start | 开始申请 |
| application_submit | 提交申请 |
| kyc_pass | KYC通过 |
| approval | 审批通过 |
| disbursement | 放款 |
| repayment | 还款 |

这一步非常重要。

因为 Google 后面就是靠这些数据学习。

---

# 六、Step 5：把 Google 的“身份”一路带到放款

这是投放技术链路最核心的地方。

一个用户搜索：

> personal loan online

然后点你的 Google 广告。

Google 会留下广告归因信息，例如 click identifier。

你的系统需要做到：

```text
Google Click
     ↓
gclid / attribution id
     ↓
application_id
     ↓
user_id
     ↓
risk decision
     ↓
approval
     ↓
disbursement
```

所以建议至少有一张 attribution 表：

```text
user_id
application_id
gclid
campaign_id
ad_group_id
keyword
click_time
application_time
approval_time
disbursement_time
loan_amount
```

于是你才能知道：

> **这笔贷款到底是哪条 Google 广告带来的。**

这就是你最近在研究的 **媒体回传 / attribution tracking** 的本质。

---

# 七、Step 6：正式创建 Google Campaign

对于一个全新的 Loan Product，我建议第一阶段先理解和使用：

## Search Campaign

因为 Search 是用户主动表达借款需求。

例如用户搜索：

```text
personal loan
personal loan australia
apply personal loan
online personal loan
```

Google Ads 的基本结构是：

```text
Google Ads Account
│
├── Campaign
│
│   Personal Loan - Search
│
├── Ad Group 1
│   Personal Loan
│
│   ├── personal loan
│   ├── "personal loan"
│   └── [personal loan]
│
├── Ad Group 2
│   Online Loan
│
└── Ads
    Headline
    Description
    Landing Page
```

Google 官方 Search Campaign 本身也是按照 **Campaign → Ad Group → Keywords → Ads** 的结构建立，并支持 broad、phrase 和 exact 等 keyword match type。

参考：
- Google Ads Help — Search campaign / keywords  
  https://support.google.com/google-ads/answer/9510373?hl=en

---

# 八、Keyword 到底是什么？

这个是 Google Search 最重要的概念。

例如用户搜索：

> best personal loan australia

你可以买：

```text
personal loan
```

Google 判断这个搜索和你的关键词相关，就进入竞价。

例如第一版可以分成：

### 高意图词

```text
apply personal loan
personal loan online
personal loan australia
quick personal loan
```

### 产品词

```text
personal loan
small personal loan
online loan
```

然后每天看：

```text
Search Terms
```

也就是：

> 用户到底搜了什么词以后点了我的广告？

不断：

```text
好词 → 加进去
垃圾词 → Negative Keyword
```

---

# 九、Step 7：广告上线以后，看什么指标？

刚开始不要一口气盯几十个指标。

先看漏斗：

```text
Impression
    ↓
Click
    ↓ CTR
Application
    ↓ CVR
Approval
    ↓ Approval Rate
Disbursement
    ↓
Repayment
```

对应成本：

```text
Spend / Click
= CPC

Spend / Application
= CPA_application

Spend / Approval
= CPA_approval

Spend / Disbursement
= CPA_disbursement
```

例如：

```text
Spend                $10,000

Clicks                2,000
Applications            400
Approved                160
Disbursed               120
```

那么：

```text
CPC
= 10,000 / 2,000
= $5

Cost / Application
= $25

Cost / Approval
= $62.5

Cost / Disbursement
= $83.3
```

**信贷真正应该盯的是后面几个。**

而不是：

> CPC 很便宜，所以 Campaign 很好。

---

# 十、Step 8：最关键——把 Approval / Disbursement 回传 Google

假设 Google 带来了两个人：

```text
Customer A
click
→ apply
→ decline

Customer B
click
→ apply
→ approve
→ disburse
```

如果你只告诉 Google：

```text
A = Application
B = Application
```

Google认为：

> 两个人一样好。

这是错的。

你真正应该告诉 Google：

```text
A = Application only

B =
Application
Approval
Disbursement
```

这样 Google 才逐渐学会：

> 哪一种搜索、用户上下文和流量更容易产生真正的放款。

Google 官方目前也推荐 lead generation 场景使用 **Enhanced Conversions / offline conversion** 把线下或后端结果传回 Google，以提高归因与 bidding 的准确性。2026 年相关 offline 数据接入正在迁移到 Google Ads Data Manager / Data Manager API。

参考：
- Google Ads Help — Offline conversion / enhanced conversions  
  https://support.google.com/google-ads/answer/15081888?hl=en

---

# 十一、这时候 Google 才真正开始“机器学习”

第一阶段可以优化：

```text
Maximize Conversions

目标：
Application
```

等数据稳定之后变成：

```text
Target CPA

目标：
Approval
```

再进一步：

```text
Maximize Conversion Value
 / Target ROAS

目标：
Disbursement / Value
```

Google 的 Smart Bidding 目前主要包括 Maximize Conversions、Target CPA、Maximize Conversion Value 和 Target ROAS。

参考：
- Google Ads Help — Smart Bidding  
  https://support.google.com/google-ads/answer/11095984?hl=en

对于信贷业务，我会把成熟过程理解成：

```text
Level 1

Google
↓
找最多 Application
```

↓

```text
Level 2

Google
↓
找最多 Approval
```

↓

```text
Level 3

Google
↓
找最多 Disbursement
```

↓

```text
Level 4

Google
↓
找高价值 + 好风险客户
↓
LTV / Profit Optimization
```

**Level 4 才是真正成熟的金融投放。**

---

# 十二、信贷里特别容易犯的一个错误

假设两个 Campaign：

| | Campaign A | Campaign B |
|---|---:|---:|
| Application | 1,000 | 700 |
| CPA | $20 | $25 |
| Approval Rate | 10% | 30% |
| Approved | 100 | 210 |

如果营销只看：

```text
Application CPA
```

A 看起来更好。

但实际上：

```text
A cost / approval
= $200

B cost / approval
= $83
```

**B 才是真正的好流量。**

所以金融投放一定要把：

> **Marketing 数据 × Risk 数据 × Loan 数据**

接起来。

这也是为什么你现在做的 **媒体回传质量、用户质量模型、风险模型**，实际上最后都能和投放连成一条链路。

---

# 十三、一个完整的 Google 信贷投放架构

你可以直接把整个事情记成下面这张图：

```text
                 GOOGLE ADS
                     │
            Campaign / Keyword
                     │
                     ▼
               Landing Page
                     │
                 Apply
                     │
                     ▼
              Application
                     │
        ┌────────────┴────────────┐
        │                         │
       KYC                  Bank Statement
        │                         │
        └────────────┬────────────┘
                     │
                Risk Model
                     │
              ┌──────┴──────┐
           Decline        Approval
                             │
                         Disbursement
                             │
                          Repayment
                             │
                             ▼
                    Data Warehouse
                             │
                  attribution / postback
                             │
                             ▼
                       GOOGLE ADS
                             │
                    Smart Bidding
                             │
                             ▼
                 找更多高质量客户
```

这张图理解了，**Google 信贷投放基本就理解了 70%。**

---

# 十四、如果让我真的从 0 开这个项目，我会按这个顺序做

| 阶段 | 做什么 | 最终产物 |
|---|---|---|
| 1 | Product Design | 产品规则 |
| 2 | Compliance | Licence + Google Verification |
| 3 | Landing Page | 可投页面 |
| 4 | Application Funnel | 完整申请流程 |
| 5 | Tracking | Google Click → application_id |
| 6 | Conversion | Application / Approval / Disbursement |
| 7 | Search Campaign | Keyword + Ads |
| 8 | Small-scale Test | 小预算测试 |
| 9 | Funnel Analysis | CVR / Approval / Disbursement |
| 10 | Postback | 后端结果回 Google |
| 11 | Smart Bidding | CPA / Value Optimization |
| 12 | Scale | 放量 |

---

## 你现在最值得先掌握的 5 个东西

不用一开始学 Google Ads 所有功能。

先把这五个搞明白：

**① Campaign / Ad Group / Keyword 是什么**

**② Search → Click → Application 是怎么产生的**

**③ gclid / attribution 是什么**

**④ Conversion / Offline Conversion 是什么**

**⑤ Google 怎么通过 Approval / Disbursement 回传优化流量**

这几个理解之后，再去学 Demand Gen、PMax、Audience、ROAS 等会容易很多。

另外有一条金融广告的红线要记住：不要基于用户的**低信用分、高负债、财务困难等负面财务状态**去构建个性化广告受众；Google 将 negative financial status 视为敏感类别，并限制 advertiser-curated audiences 的使用。

参考：
- Google Ads Policy — Personalized advertising  
  https://support.google.com/adspolicy/answer/143465?hl=en
