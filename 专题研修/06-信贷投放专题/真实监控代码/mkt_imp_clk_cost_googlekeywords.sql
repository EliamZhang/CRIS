DROP TABLE IF EXISTS mkt.mkt_imp_clk_cost_keyword;

CREATE TABLE IF NOT EXISTS mkt.mkt_imp_clk_cost_keyword AS

WITH kw_sum AS (
    SELECT 
        biz_date,
        CASE
            WHEN campaign_name IN ('BRA - Search - Brand - All', 'BRA - Search - Brand - New') THEN 'brand'
            WHEN campaign_name = 'BRA - Search - Brand - Returning' THEN 'brand-rlsa'
            WHEN campaign_name IN ('DG - Demand Gen - New | Value', 'DG - Demand Gen - New | Volume') THEN 'demand-gen'
            WHEN campaign_name = 'DG - Demand Gen - Returning' THEN 'demand-gen-return'
            WHEN campaign_name = 'NBR - Search - Cash Loans | By Type | Volume' THEN 'nbr-by-type'
            WHEN campaign_name = 'NBR - Search - Cash Loans | Value' THEN 'nbr-cash-loans'
            WHEN campaign_name IN ('NBR - Search - Competitors | Value', 'NBR - Search - Competitors | Volume') THEN 'nbr-competitors'
            WHEN campaign_name = 'NBR - Search - Credit | Value' THEN 'nbr-credit'
            WHEN campaign_name = 'NBR - Search - Payday Loans | Value' THEN 'nbr-payday-loans'
            WHEN campaign_name IN ('NBR - Search - Master - New | Volume', 'NBR - Search - Master - Value', 'NBR - Search - Master | Volume', 'NBR - Search - Master - Volume') THEN 'nbr_master_volume'
            WHEN campaign_name IN ('PMAX - Performance Max | Value', 'PMAX - Value', 'PMAX - Value | All') THEN 'max_value'
            WHEN campaign_name IN ('PMAX - Value | New', 'PMAX - Value | New Customers') THEN 'max_value_new'
            WHEN campaign_name IN ('PMAX - Performance Max | Volume', 'PMAX - Volume', 'zPMAX - Performance Max | Volume') THEN 'max_volume'
            WHEN campaign_name IN ('PMAX - Volume (new)') THEN 'max_volume_new'
            WHEN campaign_name IN ('NBR - Search - Instant Loans | Volume', 'zNBR - Search - Instant Loans | Volume') THEN 'nbr-instant-loans'
            WHEN campaign_name = 'zNBR - Search - Fast Cash | Volume' THEN 'nbr-fast-cash'
            WHEN campaign_name LIKE 'APP%' OR campaign_name LIKE 'Android%' THEN campaign_name
            ELSE campaign_name
        END AS biz_campaign_name,
        keyword_text,
        SUM(impressions) AS impressions,
        SUM(clicks)      AS clicks,
        SUM(cost)        AS cost
    FROM edw.dwd_au_mkt_google_adset_keyword_view
    WHERE biz_date >= '2025-04-01'
      AND biz_date NOT IN ('2026-06-08','2026-06-09','2026-06-10','2026-06-11')
      AND NOT (UPPER(campaign_name) LIKE 'AKR%' OR UPPER(campaign_name) LIKE 'KLX%' OR UPPER(campaign_name) LIKE 'MEC%')  --排除Google盗号期间非Fundo campaign
    GROUP BY 1,2,3
),

kw_campaign_sum AS (
    -- 1. 按campaign聚合所有关键词的汇总展点消
    SELECT
        biz_date,
        biz_campaign_name,
        SUM(impressions) AS impressions,
        SUM(clicks)      AS clicks,
        SUM(cost)        AS cost
    FROM kw_sum
    GROUP BY 1,2
),

campaign_sum AS (
    -- 2. campaign总展点消
    SELECT
        biz_date,
        CASE
            WHEN campaign_name IN ('BRA - Search - Brand - All', 'BRA - Search - Brand - New') THEN 'brand'
            WHEN campaign_name = 'BRA - Search - Brand - Returning' THEN 'brand-rlsa'
            WHEN campaign_name IN ('DG - Demand Gen - New | Value', 'DG - Demand Gen - New | Volume') THEN 'demand-gen'
            WHEN campaign_name = 'DG - Demand Gen - Returning' THEN 'demand-gen-return'
            WHEN campaign_name = 'NBR - Search - Cash Loans | By Type | Volume' THEN 'nbr-by-type'
            WHEN campaign_name = 'NBR - Search - Cash Loans | Value' THEN 'nbr-cash-loans'
            WHEN campaign_name IN ('NBR - Search - Competitors | Value', 'NBR - Search - Competitors | Volume') THEN 'nbr-competitors'
            WHEN campaign_name = 'NBR - Search - Credit | Value' THEN 'nbr-credit'
            WHEN campaign_name = 'NBR - Search - Payday Loans | Value' THEN 'nbr-payday-loans'
            WHEN campaign_name IN ('NBR - Search - Master - New | Volume', 'NBR - Search - Master - Value', 'NBR - Search - Master | Volume', 'NBR - Search - Master - Volume') THEN 'nbr_master_volume'
            WHEN campaign_name IN ('PMAX - Performance Max | Value', 'PMAX - Value', 'PMAX - Value | All') THEN 'max_value'
            WHEN campaign_name IN ('PMAX - Value | New', 'PMAX - Value | New Customers') THEN 'max_value_new'
            WHEN campaign_name IN ('PMAX - Performance Max | Volume', 'PMAX - Volume', 'zPMAX - Performance Max | Volume') THEN 'max_volume'
            WHEN campaign_name IN ('PMAX - Volume (new)') THEN 'max_volume_new'
            WHEN campaign_name IN ('NBR - Search - Instant Loans | Volume', 'zNBR - Search - Instant Loans | Volume') THEN 'nbr-instant-loans'
            WHEN campaign_name = 'zNBR - Search - Fast Cash | Volume' THEN 'nbr-fast-cash'
            WHEN campaign_name LIKE 'APP%' OR campaign_name LIKE 'Android%' THEN campaign_name
            ELSE campaign_name
        END AS biz_campaign_name,
        SUM(impressions) AS impressions,
        SUM(clicks)      AS clicks,
        SUM(cost)        AS cost
    FROM edw.dws_mkt_media_campaign_hour_report_data
    WHERE channel = 'google'
      AND biz_date >= '2025-04-01'
      AND biz_date NOT IN ('2026-06-08','2026-06-09','2026-06-10','2026-06-11')
      AND NOT (UPPER(campaign_name) LIKE 'AKR%' OR UPPER(campaign_name) LIKE 'KLX%' OR UPPER(campaign_name) LIKE 'MEC%')  --排除Google盗号期间非Fundo campaign
    GROUP BY 1,2
),

null_keyword_rows AS (
    -- 3. 关联campaign总表，计算每个campaign缺失的null关键词流量，构造keyword='null'的虚拟行
    SELECT
        t1.biz_date,
        t1.biz_campaign_name,
        'Null' AS keyword_text,
        t1.impressions - COALESCE(t2.impressions, 0) AS impressions,
        t1.clicks - COALESCE(t2.clicks, 0) AS clicks,
        t1.cost - COALESCE(t2.cost, 0) AS cost
    FROM campaign_sum t1
    LEFT JOIN kw_campaign_sum t2 
    ON t1.biz_campaign_name = t2.biz_campaign_name
    AND t1.biz_date = t2.biz_date
    AND t1.biz_campaign_name IN (SELECT DISTINCT biz_campaign_name FROM kw_campaign_sum)
    -- 过滤差值>0，避免无缺失流量生成空行；
    WHERE (t1.impressions - COALESCE(t2.impressions, 0)) > 0
       OR (t1.clicks - COALESCE(t2.clicks, 0)) > 0
       OR (t1.cost - COALESCE(t2.cost, 0)) > 0
),

keywords_all AS (
-- 4. 合并原始关键词数据 + null虚拟行，生成最终明细表
    SELECT DISTINCT 
        biz_date,
        biz_campaign_name,
        keyword_text,
        impressions,
        clicks,
        cost
    FROM 
        (SELECT DISTINCT
            biz_date,
            biz_campaign_name,
            keyword_text,
            impressions,
            clicks,
            cost
        FROM kw_sum
        UNION ALL
        SELECT DISTINCT
            biz_date,
            biz_campaign_name,
            keyword_text,
            impressions,
            clicks,
            cost
        FROM null_keyword_rows
      )
),

driver AS (
-- 5. driver：日期 + campaign + keyword 全维度
    SELECT DISTINCT
        dt.biz_date,
        dt.biz_week,
        dt.biz_month,
        kw.biz_campaign_name,
        kw.keyword_text
    FROM
        (SELECT DISTINCT
            application_date AS biz_date,
            CASE
                WHEN MONTH(DATE(application_date)) = 12 AND WEEKOFYEAR(DATE(application_date)) = 1
                    THEN CONCAT(CAST(YEAR(DATE(application_date)) + 1 AS STRING), 'W', LPAD(CAST(WEEKOFYEAR(DATE(application_date)) AS STRING), 2, '0'))
                WHEN MONTH(DATE(application_date)) = 1 AND WEEKOFYEAR(DATE(application_date)) IN (52, 53)
                    THEN CONCAT(CAST(YEAR(DATE(application_date)) - 1 AS STRING), 'W', LPAD(CAST(WEEKOFYEAR(DATE(application_date)) AS STRING), 2, '0'))
                ELSE CONCAT(CAST(YEAR(DATE(application_date)) AS STRING), 'W', LPAD(CAST(WEEKOFYEAR(DATE(application_date)) AS STRING), 2, '0'))
            END AS biz_week,
            date_format(application_date,'yyyy-MM') AS biz_month
        FROM ba.customer_profile_rawdata
        WHERE application_date>='2025-04-01') dt
    FULL JOIN 
        (SELECT DISTINCT 
                biz_campaign_name, 
                keyword_text
        FROM 
            (SELECT DISTINCT 
                biz_campaign_name, 
                keyword_text
            FROM keywords_all
            UNION ALL
            SELECT DISTINCT
                attributed_campaign AS biz_campaign_name, 
                attributed_term AS keyword_text
            FROM ba.customer_profile_rawdata
            WHERE application_date >= '2025-04-01'
              AND attributed_utm = 'google'
              AND attributed_campaign IN (SELECT DISTINCT biz_campaign_name FROM kw_campaign_sum)
              AND attributed_term <> 'Null')
        WHERE biz_campaign_name IN (SELECT DISTINCT biz_campaign_name FROM kw_campaign_sum)
        ) kw
    ON 1 = 1
)

SELECT
    driver.biz_date,
    driver.biz_week,
    driver.biz_month,
    driver.biz_campaign_name,
    driver.keyword_text,
    
     -- 媒体侧指标：Google关键词明细汇总
    COALESCE(kw.impressions, 0) AS keyword_impressions,
    COALESCE(kw.clicks, 0)      AS keyword_clicks,
    COALESCE(kw.cost, 0)*1.1    AS keyword_cost,
    
    COALESCE(r.registration, 0) AS registration,
    
    -- funnel metrics (from b)
    COALESCE(b.`application`, 0)              AS `application`,
    COALESCE(b.completed_application, 0)      AS completed_application,
    COALESCE(b.approved_application, 0)       AS approved_application,
    COALESCE(b.principal_cnt, 0)              AS principal_cnt,
    COALESCE(b.principal_amt, 0)              AS principal_amt,

    COALESCE(b.auto_approved_application, 0)  AS auto_approved_application,
    COALESCE(b.manual_approved_application, 0) AS manual_approved_application,
    COALESCE(b.auto_declined_application, 0)  AS auto_declined_application,
    COALESCE(b.manual_declined_application, 0) AS manual_declined_application,
    COALESCE(b.auto_withdrawn_application, 0) AS auto_withdrawn_application,
    COALESCE(b.manual_withdrawn_application, 0) AS manual_withdrawn_application,

    COALESCE(b.requested_amt, 0)              AS requested_amt,
    COALESCE(b.requested_amt_of_funded, 0)    AS requested_amt_of_funded,
    COALESCE(b.approved_amt, 0)               AS approved_amt,

    COALESCE(b.green_completed_application, 0) AS green_completed_application,
    COALESCE(b.finv_green_completed_application, 0) AS finv_green_completed_application,
    COALESCE(b.age, 0)                        AS age,
    COALESCE(b.income, 0)                     AS income,
    COALESCE(b.expenses, 0)                   AS expenses,
    COALESCE(b.gross_surplus, 0)              AS gross_surplus,

    COALESCE(b.new_application, 0)            AS new_application,
    COALESCE(b.new_completed_application, 0)  AS new_completed_application,
    COALESCE(b.new_approved_application, 0)   AS new_approved_application,
    COALESCE(b.new_principal_cnt, 0)          AS new_principal_cnt,
    COALESCE(b.new_principal_amt, 0)          AS new_principal_amt,

    COALESCE(b.new_user_application, 0)       AS new_user_application,
    COALESCE(b.new_user_completed_application, 0) AS new_user_completed_application,
    COALESCE(b.new_user_approved_application, 0)  AS new_user_approved_application,
    COALESCE(b.new_user_principal_cnt, 0)     AS new_user_principal_cnt,
    COALESCE(b.new_user_principal_amt, 0)     AS new_user_principal_amt,

    -- t0~t7 (from b)
    COALESCE(b.t0_completed, 0) AS t0_completed,
    COALESCE(b.t1_completed, 0) AS t1_completed,
    COALESCE(b.t2_completed, 0) AS t2_completed,
    COALESCE(b.t7_completed, 0) AS t7_completed,

    COALESCE(b.t0_approved, 0) AS t0_approved,
    COALESCE(b.t1_approved, 0) AS t1_approved,
    COALESCE(b.t2_approved, 0) AS t2_approved,
    COALESCE(b.t7_approved, 0) AS t7_approved,

    COALESCE(b.t0_auto_approved, 0) AS t0_auto_approved,
    COALESCE(b.t1_auto_approved, 0) AS t1_auto_approved,
    COALESCE(b.t2_auto_approved, 0) AS t2_auto_approved,
    COALESCE(b.t7_auto_approved, 0) AS t7_auto_approved,

    COALESCE(b.t0_manual_approved, 0) AS t0_manual_approved,
    COALESCE(b.t1_manual_approved, 0) AS t1_manual_approved,
    COALESCE(b.t2_manual_approved, 0) AS t2_manual_approved,
    COALESCE(b.t7_manual_approved, 0) AS t7_manual_approved,

    COALESCE(b.t0_auto_declined, 0) AS t0_auto_declined,
    COALESCE(b.t1_auto_declined, 0) AS t1_auto_declined,
    COALESCE(b.t2_auto_declined, 0) AS t2_auto_declined,
    COALESCE(b.t7_auto_declined, 0) AS t7_auto_declined,

    COALESCE(b.t0_manual_declined, 0) AS t0_manual_declined,
    COALESCE(b.t1_manual_declined, 0) AS t1_manual_declined,
    COALESCE(b.t2_manual_declined, 0) AS t2_manual_declined,
    COALESCE(b.t7_manual_declined, 0) AS t7_manual_declined,

    COALESCE(b.t0_dispersal, 0) AS t0_dispersal,
    COALESCE(b.t1_dispersal, 0) AS t1_dispersal,
    COALESCE(b.t2_dispersal, 0) AS t2_dispersal,
    COALESCE(b.t7_dispersal, 0) AS t7_dispersal,

    COALESCE(b.t0_dispersal_amount, 0) AS t0_dispersal_amount,
    COALESCE(b.t1_dispersal_amount, 0) AS t1_dispersal_amount,
    COALESCE(b.t2_dispersal_amount, 0) AS t2_dispersal_amount,
    COALESCE(b.t7_dispersal_amount, 0) AS t7_dispersal_amount,

    -- forecast (from f)
    COALESCE(f.pred_funded, 0) AS pred_funded,
    COALESCE(f.pred_funded_new, 0) AS pred_funded_new,
    
    COALESCE(f.pred_funded_amt, 0) AS pred_funded_amt,
    COALESCE(f.pred_funded_amt_new, 0) AS pred_funded_amt_new,
    
    CASE WHEN driver.biz_date <= date_sub(current_date(), 1) AND driver.biz_date >= date_sub(current_date(), 14)
            THEN GREATEST(COALESCE(f.pred_funded, 0), COALESCE(b.principal_cnt, 0))
        WHEN driver.biz_date < date_sub(current_date(), 14)
            THEN COALESCE(b.principal_cnt, 0)
        END AS funded_final,
    CASE WHEN driver.biz_date <= date_sub(current_date(), 1) AND driver.biz_date >= date_sub(current_date(), 14)
            THEN GREATEST(COALESCE(f.pred_funded_new, 0), COALESCE(b.new_user_principal_cnt, 0))
        WHEN driver.biz_date < date_sub(current_date(), 14)
            THEN COALESCE(b.new_user_principal_cnt, 0)
        END AS funded_final_new,
        
    CASE WHEN driver.biz_date <= date_sub(current_date(), 1) AND driver.biz_date >= date_sub(current_date(), 14)
            THEN GREATEST(COALESCE(f.pred_funded_amt, 0), COALESCE(b.principal_amt, 0))
        WHEN driver.biz_date < date_sub(current_date(), 14)
            THEN COALESCE(b.principal_amt, 0)
        END AS funded_amt_final,
    CASE WHEN driver.biz_date <= date_sub(current_date(), 1) AND driver.biz_date >= date_sub(current_date(), 14)
            THEN GREATEST(COALESCE(f.pred_funded_amt_new, 0), COALESCE(b.new_user_principal_amt, 0))
        WHEN driver.biz_date < date_sub(current_date(), 14)
            THEN COALESCE(b.new_user_principal_amt, 0)
        END AS funded_amt_final_new

FROM driver driver

LEFT JOIN keywords_all kw
  ON driver.biz_date = kw.biz_date
  AND driver.biz_campaign_name = kw.biz_campaign_name
  AND driver.keyword_text = kw.keyword_text

LEFT JOIN
(
    SELECT
        application_date,
        attributed_campaign,
        COALESCE(attributed_term, 'Null') AS attributed_term,

        COUNT(DISTINCT application_id) AS `application`,
        COUNT(DISTINCT CASE WHEN application_status NOT IN ('0.Incomplete', '1.In Progress') THEN application_id END) AS completed_application,
        COUNT(DISTINCT CASE WHEN LEFT(application_status,1) IN ('3', '4') THEN application_id END) AS approved_application,
        COUNT(DISTINCT CASE WHEN application_status = '4.Funded' THEN application_id END) AS principal_cnt,
        SUM(CASE WHEN application_status = '4.Funded' AND total_amount IS NOT NULL THEN total_amount ELSE 0 END) AS principal_amt,

        COUNT(DISTINCT CASE WHEN LEFT(application_status,1) IN ('3', '4') AND assessment_status LIKE '%Auto Approved%' THEN application_id END) AS auto_approved_application,
        COUNT(DISTINCT CASE WHEN LEFT(application_status,1) IN ('3', '4') AND assessment_status LIKE '%Manual Approved%' THEN application_id END) AS manual_approved_application,
        COUNT(DISTINCT CASE WHEN application_status = '2.3.Risk Declined' AND assessment_status LIKE '%Auto Declined%' THEN application_id END) AS auto_declined_application,
        COUNT(DISTINCT CASE WHEN application_status = '2.3.Risk Declined' AND assessment_status LIKE '%Manual Declined%' THEN application_id END) AS manual_declined_application,
        COUNT(DISTINCT CASE WHEN application_status = '2.1.Submitted Withdrawn' AND assessment_status LIKE '%Auto Withdrawn%' THEN application_id END) AS auto_withdrawn_application,
        COUNT(DISTINCT CASE WHEN application_status = '2.1.Submitted Withdrawn' AND assessment_status LIKE '%Manual Withdrawn%' THEN application_id END) AS manual_withdrawn_application,

        SUM(CASE WHEN application_status NOT IN ('0.Incomplete', '1.In Progress') AND requested_loan_amount IS NOT NULL THEN requested_loan_amount ELSE 0 END) AS requested_amt,
        SUM(CASE WHEN application_status = '4.Funded' AND requested_loan_amount IS NOT NULL THEN requested_loan_amount ELSE 0 END) AS requested_amt_of_funded,
        SUM(CASE WHEN LEFT(application_status,1) IN ('3', '4') THEN total_amount ELSE 0 END) AS approved_amt,

        COUNT(DISTINCT CASE WHEN application_status NOT IN ('0.Incomplete', '1.In Progress') AND risk_level = '01.GREEN' THEN application_id END) AS green_completed_application,
        COUNT(DISTINCT CASE WHEN application_status NOT IN ('0.Incomplete', '1.In Progress') AND finv_color_code = '01.GREEN' THEN application_id END) AS finv_green_completed_application,
        SUM(CASE WHEN age IS NOT NULL THEN age ELSE 0 END) AS age,
        SUM(CASE WHEN application_status NOT IN ('0.Incomplete', '1.In Progress') AND total_income IS NOT NULL AND total_income < 200000 THEN total_income ELSE 0 END) AS income,
        SUM(CASE WHEN application_status NOT IN ('0.Incomplete', '1.In Progress') AND total_expenses IS NOT NULL AND total_expenses < 200000 THEN total_expenses ELSE 0 END) AS expenses,
        SUM(CASE WHEN application_status NOT IN ('0.Incomplete', '1.In Progress')
          AND gross_surplus IS NOT NULL AND total_income < 200000 AND total_expenses < 200000 THEN gross_surplus ELSE 0 END) AS gross_surplus,

        COUNT(DISTINCT CASE WHEN application_tag = 'New' THEN application_id END) AS new_application,
        COUNT(DISTINCT CASE WHEN application_tag = 'New' AND application_status NOT IN ('0.Incomplete', '1.In Progress') THEN application_id END) AS new_completed_application,
        COUNT(DISTINCT CASE WHEN application_tag = 'New' AND LEFT(application_status,1) IN ('3', '4') THEN application_id END) AS new_approved_application,
        COUNT(DISTINCT CASE WHEN application_tag = 'New' AND application_status = '4.Funded' THEN application_id END) AS new_principal_cnt,
        SUM(CASE WHEN application_tag = 'New' AND application_status = '4.Funded' AND total_amount IS NOT NULL THEN total_amount ELSE 0 END) AS new_principal_amt,

        COUNT(DISTINCT CASE WHEN user_tag = 'New' THEN application_id END) AS new_user_application,
        COUNT(DISTINCT CASE WHEN user_tag = 'New' AND application_status NOT IN ('0.Incomplete', '1.In Progress') THEN application_id END) AS new_user_completed_application,
        COUNT(DISTINCT CASE WHEN user_tag = 'New' AND LEFT(application_status,1) IN ('3', '4') THEN application_id END) AS new_user_approved_application,
        COUNT(DISTINCT CASE WHEN user_tag = 'New' AND application_status = '4.Funded' THEN application_id END) AS new_user_principal_cnt,
        SUM(CASE WHEN user_tag = 'New' AND application_status = '4.Funded' AND total_amount IS NOT NULL THEN total_amount ELSE 0 END) AS new_user_principal_amt,

        COUNT(CASE WHEN last_step='9.submitted' AND completed_step_day=0 THEN application_id END) AS t0_completed,
        COUNT(CASE WHEN last_step='9.submitted' AND completed_step_day<=1 THEN application_id END) AS t1_completed,
        COUNT(CASE WHEN last_step='9.submitted' AND completed_step_day<=2 THEN application_id END) AS t2_completed,
        COUNT(CASE WHEN last_step='9.submitted' AND completed_step_day<=7 THEN application_id END) AS t7_completed,

        COUNT(CASE WHEN LEFT(application_status,1) IN ('3','4') AND risk_approved_day=0 THEN application_id END) AS t0_approved,
        COUNT(CASE WHEN LEFT(application_status,1) IN ('3','4') AND risk_approved_day<=1 THEN application_id END) AS t1_approved,
        COUNT(CASE WHEN LEFT(application_status,1) IN ('3','4') AND risk_approved_day<=2 THEN application_id END) AS t2_approved,
        COUNT(CASE WHEN LEFT(application_status,1) IN ('3','4') AND risk_approved_day<=7 THEN application_id END) AS t7_approved,

        COUNT(CASE WHEN LEFT(application_status,1) IN ('3','4') AND assessment_status LIKE '%Auto Approved%' AND risk_approved_day=0 THEN application_id END) AS t0_auto_approved,
        COUNT(CASE WHEN LEFT(application_status,1) IN ('3','4') AND assessment_status LIKE '%Auto Approved%' AND risk_approved_day<=1 THEN application_id END) AS t1_auto_approved,
        COUNT(CASE WHEN LEFT(application_status,1) IN ('3','4') AND assessment_status LIKE '%Auto Approved%' AND risk_approved_day<=2 THEN application_id END) AS t2_auto_approved,
        COUNT(CASE WHEN LEFT(application_status,1) IN ('3','4') AND assessment_status LIKE '%Auto Approved%' AND risk_approved_day<=7 THEN application_id END) AS t7_auto_approved,

        COUNT(CASE WHEN LEFT(application_status,1) IN ('3','4') AND assessment_status LIKE '%Manual Approved%' AND risk_approved_day=0 THEN application_id END) AS t0_manual_approved,
        COUNT(CASE WHEN LEFT(application_status,1) IN ('3','4') AND assessment_status LIKE '%Manual Approved%' AND risk_approved_day<=1 THEN application_id END) AS t1_manual_approved,
        COUNT(CASE WHEN LEFT(application_status,1) IN ('3','4') AND assessment_status LIKE '%Manual Approved%' AND risk_approved_day<=2 THEN application_id END) AS t2_manual_approved,
        COUNT(CASE WHEN LEFT(application_status,1) IN ('3','4') AND assessment_status LIKE '%Manual Approved%' AND risk_approved_day<=7 THEN application_id END) AS t7_manual_approved,

        COUNT(CASE WHEN application_status='2.3.Risk Declined' AND assessment_status LIKE '%Auto Declined%' AND risk_declined_day=0 THEN application_id END) AS t0_auto_declined,
        COUNT(CASE WHEN application_status='2.3.Risk Declined' AND assessment_status LIKE '%Auto Declined%' AND risk_declined_day<=1 THEN application_id END) AS t1_auto_declined,
        COUNT(CASE WHEN application_status='2.3.Risk Declined' AND assessment_status LIKE '%Auto Declined%' AND risk_declined_day<=2 THEN application_id END) AS t2_auto_declined,
        COUNT(CASE WHEN application_status='2.3.Risk Declined' AND assessment_status LIKE '%Auto Declined%' AND risk_declined_day<=7 THEN application_id END) AS t7_auto_declined,

        COUNT(CASE WHEN application_status='2.3.Risk Declined' AND assessment_status LIKE '%Manual Declined%' AND risk_declined_day=0 THEN application_id END) AS t0_manual_declined,
        COUNT(CASE WHEN application_status='2.3.Risk Declined' AND assessment_status LIKE '%Manual Declined%' AND risk_declined_day<=1 THEN application_id END) AS t1_manual_declined,
        COUNT(CASE WHEN application_status='2.3.Risk Declined' AND assessment_status LIKE '%Manual Declined%' AND risk_declined_day<=2 THEN application_id END) AS t2_manual_declined,
        COUNT(CASE WHEN application_status='2.3.Risk Declined' AND assessment_status LIKE '%Manual Declined%' AND risk_declined_day<=7 THEN application_id END) AS t7_manual_declined,

        COUNT(CASE WHEN application_status='4.Funded' AND dispersal_day=0 THEN application_id END) AS t0_dispersal,
        COUNT(CASE WHEN application_status='4.Funded' AND dispersal_day<=1 THEN application_id END) AS t1_dispersal,
        COUNT(CASE WHEN application_status='4.Funded' AND dispersal_day<=2 THEN application_id END) AS t2_dispersal,
        COUNT(CASE WHEN application_status='4.Funded' AND dispersal_day<=7 THEN application_id END) AS t7_dispersal,

        SUM(CASE WHEN application_status='4.Funded' AND dispersal_day=0 THEN total_amount ELSE 0 END) AS t0_dispersal_amount,
        SUM(CASE WHEN application_status='4.Funded' AND dispersal_day<=1 THEN total_amount ELSE 0 END) AS t1_dispersal_amount,
        SUM(CASE WHEN application_status='4.Funded' AND dispersal_day<=2 THEN total_amount ELSE 0 END) AS t2_dispersal_amount,
        SUM(CASE WHEN application_status='4.Funded' AND dispersal_day<=7 THEN total_amount ELSE 0 END) AS t7_dispersal_amount

    FROM
    (
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
            DATEDIFF(DATE(dispersal_date), DATE(application_date)) AS dispersal_day
        FROM ba.customer_profile_rawdata
        WHERE application_date >= '2025-04-01'
        AND attributed_utm = 'google'
    ) base_data
    GROUP BY 1,2,3
) b
ON driver.biz_date = b.application_date
AND driver.biz_campaign_name = b.attributed_campaign
AND driver.keyword_text = b.attributed_term

LEFT JOIN 
    (SELECT registration_date,
        attributed_campaign,
        COALESCE(attributed_term, 'Null') AS attributed_term,
        SUM(user_cnt) AS registration
    FROM ba.user_registration
    WHERE registration_date >= '2025-04-01'
      AND attributed_utm = 'google'
    GROUP BY 1,2,3
) r 
ON driver.biz_date = r.registration_date
AND driver.biz_campaign_name = r.attributed_campaign
AND driver.keyword_text = r.attributed_term

LEFT JOIN 
    (SELECT 
        application_date,
        attributed_campaign,
        COALESCE(attributed_term, 'Null') AS attributed_term,
        SUM(pred_funded) AS pred_funded,
        SUM(pred_funded_amt) AS pred_funded_amt,
        SUM(CASE WHEN user_tag='New' THEN pred_funded ELSE 0 END) AS pred_funded_new,
        SUM(CASE WHEN user_tag='New' THEN pred_funded_amt ELSE 0 END) AS pred_funded_amt_new
    FROM 
        (SELECT *,
            ROW_NUMBER() OVER (PARTITION BY application_date, user_tag, attributed_utm, attributed_campaign, attributed_term ORDER BY observe_date DESC) AS seq_no
        FROM mkt.mkt_t7_cpfl_forecast)
    WHERE seq_no = 1
      AND attributed_utm = 'google'
    GROUP BY 1,2,3
    ) f
ON driver.biz_date = f.application_date 
AND driver.biz_campaign_name = f.attributed_campaign
AND driver.keyword_text = f.attributed_term

WHERE COALESCE(kw.impressions, 0) + COALESCE(kw.clicks, 0) + COALESCE(kw.cost, 0) + COALESCE(r.registration, 0) + COALESCE(b.`application`, 0) > 0
;