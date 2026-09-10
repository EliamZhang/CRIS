-- DROP TABLE IF EXISTS mkt.mkt_t7_cpfl_forecast;
-- CREATE TABLE IF NOT EXISTS mkt.mkt_t7_cpfl_forecast (
--   application_date         STRING,
--   user_tag                 STRING,
--   attributed_utm           STRING,
--   attributed_campaign      STRING,
--   cumu_funded              BIGINT,
--   cumu_funded_amt          DOUBLE,
--   m_funded                 DOUBLE,
--   m_funded_amt             DOUBLE,
--   pred_funded              DOUBLE,
--   pred_funded_amt          DOUBLE
-- )
-- PARTITIONED BY (observe_date STRING);  

-- ALTER TABLE mkt.mkt_t7_cpfl_forecast
-- ADD COLUMNS (attributed_term STRING COMMENT '归因term,历史数据为NULL');
-- ALTER TABLE mkt.mkt_t7_cpfl_forecast
-- ADD COLUMNS (attributed_category STRING COMMENT '归因category,历史数据为NULL');
-- ALTER TABLE mkt.mkt_t7_cpfl_forecast
-- ADD COLUMNS (cost_category STRING COMMENT '归因cost category,历史数据为NULL');


WITH

base_data AS (
  SELECT 
    *,
    DATEDIFF(DATE(completed_step_time), DATE(application_date)) AS completed_step_day,
    DATEDIFF(DATE(last_status_time), DATE(application_date)) AS last_status_day,
    DATEDIFF(DATE(risk_approved_time), DATE(application_date)) AS risk_approved_day,
    DATEDIFF(DATE(risk_declined_time), DATE(application_date)) AS risk_declined_day,
    DATEDIFF(DATE(conversion_check_time), DATE(application_date)) AS conversion_check_day,
    DATEDIFF(DATE(conversion_declined_time), DATE(application_date)) AS conversion_declined_day,
    DATEDIFF(DATE(converted_time), DATE(application_date)) AS converted_day,
    DATEDIFF(DATE(withdrawn_time), DATE(application_date)) AS withdrawn_day,
    DATEDIFF(DATE(dispersal_date), DATE(application_date)) AS dispersal_day,
    DATEDIFF(to_date('${yyyy-mm-dd}'), DATE(application_date)) AS t_n
  FROM ba.customer_profile_rawdata
  WHERE DATEDIFF(to_date('${yyyy-mm-dd}'), DATE(application_date)) >= 0  -- 至少有到昨天，有T0数据
    AND DATEDIFF(to_date('${yyyy-mm-dd}'), DATE(application_date)) < 21  -- 只需预测没有T14数据的日期
),

cumu_data AS (
  SELECT
    application_date,
    t_n,
    user_tag,
    attributed_category,
    cost_category,
    attributed_utm,
    attributed_campaign,
    attributed_term,                     -- 新增
    COUNT(CASE WHEN application_status='4.Funded' AND dispersal_day<=t_n THEN application_id END) AS cumu_funded,
    SUM(CASE WHEN application_status='4.Funded' AND dispersal_day<=t_n THEN total_amount ELSE 0 END) AS cumu_funded_amt
  FROM base_data
  GROUP BY 1,2,3,4,5,6,7,8
),

pred_t14 AS (
    SELECT
        a.*,
        m_funded,
        m_funded_amt,
        ROUND(a.cumu_funded / COALESCE(b.m_funded, 1), 4) AS pred_funded,
        ROUND(a.cumu_funded_amt / COALESCE(b.m_funded_amt, 1), 4) AS pred_funded_amt
    FROM cumu_data a
    LEFT JOIN 
        (SELECT *
        FROM ba.forecast_metrics_maturity_curve
        WHERE observe_date=to_date('${yyyy-mm-dd}')) b
      ON a.user_tag = b.user_tag
      AND a.t_n = b.t
)

INSERT OVERWRITE TABLE mkt.mkt_t7_cpfl_forecast PARTITION (observe_date)
SELECT
  application_date,
  user_tag,
  attributed_utm,
  attributed_campaign,
  cumu_funded,
  cumu_funded_amt,
  m_funded,
  m_funded_amt,
  pred_funded,
  pred_funded_amt,
  attributed_term,
  attributed_category,
  cost_category,                       -- 新增
  to_date('${yyyy-mm-dd}') AS observe_date
FROM pred_t14;