# input 目录说明

将项目输入文件统一放在这里。

当前默认输入文件：

- `data_v4.xlsx`

默认字段要求：

| 字段名 | 含义 |
|---|---|
| sample_id | 样本 ID |
| sample_month | 样本月份 |
| adr_stability_grade | 地址稳定等级，已有策略变量 |
| ovd_order_cnt_6m_grade | 最近 6 个月逾期次数等级，新接入变量 |
| positive_biz_cnt_1y_grade | 最近一年履约等级，已有策略变量 |
| risk_score | 风险模型分数，新接入变量 |
| is_dlq_30d | 30 天逾期标签，1=坏，0=好，空值表示未进入通过样本表现期 |
