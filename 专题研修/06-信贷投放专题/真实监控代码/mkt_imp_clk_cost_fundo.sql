DROP TABLE IF EXISTS mkt.mkt_imp_clk_cost_fundo;
CREATE TABLE IF NOT EXISTS mkt.mkt_imp_clk_cost_fundo AS
SELECT driver.biz_date
    ,driver.biz_week
    ,driver.biz_month
    ,driver.channel
    ,driver.biz_campaign_name
  
    ,COALESCE(a.impressions, 0) AS impressions
    ,COALESCE(a.clicks, 0) AS clicks
    ,COALESCE(a.cost, 0)*1.1 AS cost
  
    ,0 AS registration
    
    ,COALESCE(b.application, 0) AS application
    ,COALESCE(b.completed_application, 0) AS completed_application
    ,COALESCE(b.approved_application, 0) AS approved_application
    ,COALESCE(b.principal_cnt, 0) AS principal_cnt
    ,COALESCE(b.principal_amt, 0) AS principal_amt
    
    ,COALESCE(b.auto_approved_application, 0) AS auto_approved_application
    ,COALESCE(b.manual_approved_application, 0) AS manual_approved_application
    ,COALESCE(b.auto_declined_application, 0) AS auto_declined_application
    ,COALESCE(b.manual_declined_application, 0) AS manual_declined_application
    ,COALESCE(b.auto_withdrawn_application, 0) AS auto_withdrawn_application
    ,COALESCE(b.manual_withdrawn_application, 0) AS manual_withdrawn_application

    ,COALESCE(b.requested_amt, 0) AS requested_amt
    ,COALESCE(b.requested_amt_of_funded, 0) AS requested_amt_of_funded
    ,COALESCE(b.approved_amt, 0) AS approved_amt
    
    ,COALESCE(b.green_completed_application, 0) AS green_completed_application
    ,COALESCE(b.finv_green_completed_application, 0) AS finv_green_completed_application
    ,COALESCE(b.age, 0) AS age
    ,COALESCE(b.income, 0) AS income
    ,COALESCE(b.expenses, 0) AS expenses
    ,COALESCE(b.gross_surplus, 0) AS gross_surplus

    ,COALESCE(b.new_application, 0) AS new_application
    ,COALESCE(b.new_completed_application, 0) AS new_completed_application
    ,COALESCE(b.new_approved_application, 0) AS new_approved_application
    ,COALESCE(b.new_principal_cnt, 0) AS new_principal_cnt
    ,COALESCE(b.new_principal_amt, 0) AS new_principal_amt
    
    ,COALESCE(b.new_user_application, 0) AS new_user_application
    ,COALESCE(b.new_user_completed_application, 0) AS new_user_completed_application
    ,COALESCE(b.new_user_approved_application, 0) AS new_user_approved_application
    ,COALESCE(b.new_user_principal_cnt, 0) AS new_user_principal_cnt
    ,COALESCE(b.new_user_principal_amt, 0) AS new_user_principal_amt
    -- 新增的t0-t7系列指标（Mia260130）
    ,COALESCE(b.t0_completed, 0) AS t0_completed
    ,COALESCE(b.t1_completed, 0) AS t1_completed
    ,COALESCE(b.t2_completed, 0) AS t2_completed
    ,COALESCE(b.t7_completed, 0) AS t7_completed

    ,COALESCE(b.t0_approved, 0) AS t0_approved
    ,COALESCE(b.t1_approved, 0) AS t1_approved
    ,COALESCE(b.t2_approved, 0) AS t2_approved
    ,COALESCE(b.t7_approved, 0) AS t7_approved

    ,COALESCE(b.t0_auto_approved, 0) AS t0_auto_approved
    ,COALESCE(b.t1_auto_approved, 0) AS t1_auto_approved
    ,COALESCE(b.t2_auto_approved, 0) AS t2_auto_approved
    ,COALESCE(b.t7_auto_approved, 0) AS t7_auto_approved

    ,COALESCE(b.t0_manual_approved, 0) AS t0_manual_approved
    ,COALESCE(b.t1_manual_approved, 0) AS t1_manual_approved
    ,COALESCE(b.t2_manual_approved, 0) AS t2_manual_approved
    ,COALESCE(b.t7_manual_approved, 0) AS t7_manual_approved

    ,COALESCE(b.t0_auto_declined, 0) AS t0_auto_declined
    ,COALESCE(b.t1_auto_declined, 0) AS t1_auto_declined
    ,COALESCE(b.t2_auto_declined, 0) AS t2_auto_declined
    ,COALESCE(b.t7_auto_declined, 0) AS t7_auto_declined

    ,COALESCE(b.t0_manual_declined, 0) AS t0_manual_declined
    ,COALESCE(b.t1_manual_declined, 0) AS t1_manual_declined
    ,COALESCE(b.t2_manual_declined, 0) AS t2_manual_declined
    ,COALESCE(b.t7_manual_declined, 0) AS t7_manual_declined

    ,COALESCE(b.t0_dispersal, 0) AS t0_dispersal
    ,COALESCE(b.t1_dispersal, 0) AS t1_dispersal
    ,COALESCE(b.t2_dispersal, 0) AS t2_dispersal
    ,COALESCE(b.t7_dispersal, 0) AS t7_dispersal

    ,COALESCE(b.t0_dispersal_amount, 0) AS t0_dispersal_amount
    ,COALESCE(b.t1_dispersal_amount, 0) AS t1_dispersal_amount
    ,COALESCE(b.t2_dispersal_amount, 0) AS t2_dispersal_amount
    ,COALESCE(b.t7_dispersal_amount, 0) AS t7_dispersal_amount
    
    -- forecast (from f)
    ,COALESCE(f.pred_funded, 0) AS pred_funded
    ,COALESCE(f.pred_funded_new, 0) AS pred_funded_new
    
    ,COALESCE(f.pred_funded_amt, 0) AS pred_funded_amt
    ,COALESCE(f.pred_funded_amt_new, 0) AS pred_funded_amt_new
    
    ,CASE WHEN driver.biz_date <= date_sub(current_date(), 1) AND driver.biz_date >= date_sub(current_date(), 14)
            THEN GREATEST(COALESCE(f.pred_funded, 0), COALESCE(b.principal_cnt, 0))
        WHEN driver.biz_date < date_sub(current_date(), 14)
            THEN COALESCE(b.principal_cnt, 0)
        END AS funded_final
    ,CASE WHEN driver.biz_date <= date_sub(current_date(), 1) AND driver.biz_date >= date_sub(current_date(), 14)
            THEN GREATEST(COALESCE(f.pred_funded_new, 0), COALESCE(b.new_user_principal_cnt, 0))
        WHEN driver.biz_date < date_sub(current_date(), 14)
            THEN COALESCE(b.new_user_principal_cnt, 0)
        END AS funded_final_new
        
    ,CASE WHEN driver.biz_date <= date_sub(current_date(), 1) AND driver.biz_date >= date_sub(current_date(), 14)
            THEN GREATEST(COALESCE(f.pred_funded_amt, 0), COALESCE(b.principal_amt, 0))
        WHEN driver.biz_date < date_sub(current_date(), 14)
            THEN COALESCE(b.principal_amt, 0)
        END AS funded_amt_final
    ,CASE WHEN driver.biz_date <= date_sub(current_date(), 1) AND driver.biz_date >= date_sub(current_date(), 14)
            THEN GREATEST(COALESCE(f.pred_funded_amt_new, 0), COALESCE(b.new_user_principal_amt, 0))
        WHEN driver.biz_date < date_sub(current_date(), 14)
            THEN COALESCE(b.new_user_principal_amt, 0)
        END AS funded_amt_final_new

FROM
    (SELECT biz_date, biz_week, biz_month, channel, biz_campaign_name
    FROM 
        (SELECT DISTINCT biz_date
            ,CASE WHEN MONTH(DATE(biz_date))=12 AND WEEKOFYEAR(DATE(biz_date))=1 
                      THEN CONCAT(CAST(YEAR(DATE(biz_date)) + 1 AS STRING), 'W', LPAD(CAST(WEEKOFYEAR(DATE(biz_date)) AS STRING), 2, '0')) 
                  WHEN MONTH(DATE(biz_date))=1 AND WEEKOFYEAR(DATE(biz_date)) IN (52,53) 
                      THEN CONCAT(CAST(YEAR(DATE(biz_date)) - 1 AS STRING), 'W', LPAD(CAST(WEEKOFYEAR(DATE(biz_date)) AS STRING), 2, '0')) 
                  ELSE CONCAT(CAST(YEAR(DATE(biz_date)) AS STRING), 'W', LPAD(CAST(WEEKOFYEAR(DATE(biz_date)) AS STRING), 2, '0')) 
                  END AS biz_week
            ,date_format(biz_date,'yyyy-MM') AS biz_month
        FROM edw.dws_mkt_media_campaign_hour_report_data
        WHERE channel IS NOT NULL
        AND biz_date>='2025-04-01') dt
    FULL JOIN
        (SELECT DISTINCT channel
              ,case when campaign_name IN ('BRA - Search - Brand - All', 'BRA - Search - Brand - New') then 'brand'
                    when campaign_name = 'BRA - Search - Brand - Returning' then 'brand-rlsa'
                    when campaign_name IN ('DG - Demand Gen - New | Value', 'DG - Demand Gen - New | Volume') then 'demand-gen'
                    when campaign_name = 'DG - Demand Gen - Returning' then 'demand-gen-return'
                    when campaign_name = 'NBR - Search - Cash Loans | By Type | Volume' then 'nbr-by-type'
                    when campaign_name = 'NBR - Search - Cash Loans | Value' then 'nbr-cash-loans'
                    when campaign_name IN ('NBR - Search - Competitors | Value', 'NBR - Search - Competitors | Volume') then 'nbr-competitors'
                    when campaign_name = 'NBR - Search - Credit | Value' then 'nbr-credit'
                    when campaign_name = 'NBR - Search - Payday Loans | Value' then 'nbr-payday-loans'
                    when campaign_name IN ('NBR - Search - Master - New | Volume', 'NBR - Search - Master - Value', 'NBR - Search - Master | Volume', 'NBR - Search - Master - Volume') then 'nbr_master_volume'
                    when campaign_name IN ('PMAX - Performance Max | Value', 'PMAX - Value', 'PMAX - Value | All') then 'max_value'
                    when campaign_name IN ('PMAX - Value | New', 'PMAX - Value | New Customers') then 'max_value_new'
                    when campaign_name IN ('PMAX - Performance Max | Volume', 'PMAX - Volume', 'zPMAX - Performance Max | Volume') then 'max_volume'
                    WHEN campaign_name IN ('PMAX - Volume (new)') THEN 'max_volume_new'
                    when campaign_name IN ('NBR - Search - Instant Loans | Volume', 'zNBR - Search - Instant Loans | Volume') then 'nbr-instant-loans'
                    when campaign_name = 'zNBR - Search - Fast Cash | Volume' then 'nbr-fast-cash'
                    WHEN campaign_name LIKE 'APP%' OR campaign_name LIKE 'Android%' THEN campaign_name
                end as biz_campaign_name  -- 业务campaign name，便于跟业务数据关联上
        FROM edw.dws_mkt_media_campaign_hour_report_data
        WHERE channel IS NOT NULL
        AND biz_date>='2025-04-01'
        AND NOT (UPPER(campaign_name) LIKE 'AKR%' OR UPPER(campaign_name) LIKE 'KLX%' OR UPPER(campaign_name) LIKE 'MEC%')  --排除Google盗号期间非Fundo campaign
        ) camp
    ON 1=1
    WHERE biz_campaign_name IS NOT NULL
    ORDER BY 1,2,3,4,5) driver
LEFT JOIN  
    (SELECT
        biz_date
        ,channel
       ,case when campaign_name IN ('BRA - Search - Brand - All', 'BRA - Search - Brand - New') then 'brand'
              when campaign_name = 'BRA - Search - Brand - Returning' then 'brand-rlsa'
              when campaign_name IN ('DG - Demand Gen - New | Value', 'DG - Demand Gen - New | Volume') then 'demand-gen'
              when campaign_name = 'DG - Demand Gen - Returning' then 'demand-gen-return'
              when campaign_name = 'NBR - Search - Cash Loans | By Type | Volume' then 'nbr-by-type'
              when campaign_name = 'NBR - Search - Cash Loans | Value' then 'nbr-cash-loans'
              when campaign_name IN ('NBR - Search - Competitors | Value', 'NBR - Search - Competitors | Volume') then 'nbr-competitors'
              when campaign_name = 'NBR - Search - Credit | Value' then 'nbr-credit'
              when campaign_name = 'NBR - Search - Payday Loans | Value' then 'nbr-payday-loans'
              when campaign_name IN ('NBR - Search - Master - New | Volume', 'NBR - Search - Master - Value', 'NBR - Search - Master | Volume', 'NBR - Search - Master - Volume') then 'nbr_master_volume'
              when campaign_name IN ('PMAX - Performance Max | Value', 'PMAX - Value', 'PMAX - Value | All') then 'max_value'
              when campaign_name IN ('PMAX - Value | New', 'PMAX - Value | New Customers') then 'max_value_new'
              when campaign_name IN ('PMAX - Performance Max | Volume', 'PMAX - Volume', 'zPMAX - Performance Max | Volume') then 'max_volume'
              WHEN campaign_name IN ('PMAX - Volume (new)') THEN 'max_volume_new'
              when campaign_name IN ('NBR - Search - Instant Loans | Volume', 'zNBR - Search - Instant Loans | Volume') then 'nbr-instant-loans'
              when campaign_name = 'zNBR - Search - Fast Cash | Volume' then 'nbr-fast-cash'
              WHEN campaign_name LIKE 'APP%' OR campaign_name LIKE 'Android%' THEN campaign_name
          end as biz_campaign_name  -- 业务campaign name，便于跟业务数据关联上
        ,sum(impressions) as impressions
        ,sum(clicks) as clicks
        ,sum(cost) as cost
    FROM edw.dws_mkt_media_campaign_hour_report_data
    WHERE channel IS NOT NULL
    AND biz_date>='2025-04-01'
    GROUP BY 1,2,3) a
ON driver.biz_date = a.biz_date
AND driver.channel = a.channel
AND driver.biz_campaign_name = a.biz_campaign_name
LEFT JOIN 
    (SELECT 
        cpr.application_date,
        CASE WHEN af.attribution_source IS NULL THEN 'N/A' ELSE af.attribution_source END AS attributed_utm,
        CASE WHEN af.attribution_campaign IS NULL THEN 'N/A' ELSE af.attribution_campaign END AS attributed_campaign,
        COUNT(DISTINCT cpr.application_id) AS application,
        COUNT(DISTINCT CASE WHEN cpr.application_status NOT IN ('0.Incomplete', '1.In Progress') THEN cpr.application_id END) AS completed_application,
        COUNT(DISTINCT CASE WHEN LEFT(cpr.application_status,1) IN ('3', '4') THEN cpr.application_id END) AS approved_application,
        COUNT(DISTINCT CASE WHEN cpr.application_status = '4.Funded' THEN cpr.application_id END) AS principal_cnt,
        SUM(CASE WHEN cpr.application_status = '4.Funded' AND cpr.total_amount IS NOT NULL THEN cpr.total_amount ELSE 0 END) AS principal_amt,
        
        COUNT(DISTINCT CASE WHEN LEFT(cpr.application_status,1) IN ('3', '4') AND cpr.assessment_status LIKE '%Auto Approved%' THEN cpr.application_id END) AS auto_approved_application,
        COUNT(DISTINCT CASE WHEN LEFT(cpr.application_status,1) IN ('3', '4') AND cpr.assessment_status LIKE '%Manual Approved%' THEN cpr.application_id END) AS manual_approved_application,
        COUNT(DISTINCT CASE WHEN cpr.application_status = '2.3.Risk Declined' AND cpr.assessment_status LIKE '%Auto Declined%' THEN cpr.application_id END) AS auto_declined_application,
        COUNT(DISTINCT CASE WHEN cpr.application_status = '2.3.Risk Declined' AND cpr.assessment_status LIKE '%Manual Declined%' THEN cpr.application_id END) AS manual_declined_application,
        COUNT(DISTINCT CASE WHEN cpr.application_status = '2.1.Submitted Withdrawn' AND cpr.assessment_status LIKE '%Auto Withdrawn%' THEN cpr.application_id END) AS auto_withdrawn_application,
        COUNT(DISTINCT CASE WHEN cpr.application_status = '2.1.Submitted Withdrawn' AND cpr.assessment_status LIKE '%Manual Withdrawn%' THEN cpr.application_id END) AS manual_withdrawn_application,
    
        SUM(CASE WHEN cpr.application_status NOT IN ('0.Incomplete', '1.In Progress') AND cpr.requested_loan_amount IS NOT NULL THEN cpr.requested_loan_amount ELSE 0 END) AS requested_amt,
        SUM(CASE WHEN cpr.application_status = '4.Funded' AND cpr.requested_loan_amount IS NOT NULL THEN cpr.requested_loan_amount ELSE 0 END) AS requested_amt_of_funded,
        SUM(CASE WHEN LEFT(cpr.application_status,1) IN ('3', '4') THEN cpr.total_amount ELSE 0 END) AS approved_amt,
        
        COUNT(DISTINCT CASE WHEN cpr.application_status NOT IN ('0.Incomplete', '1.In Progress') AND cpr.risk_level = '01.GREEN' THEN cpr.application_id END) AS green_completed_application,
        COUNT(DISTINCT CASE WHEN cpr.application_status NOT IN ('0.Incomplete', '1.In Progress') AND finv_color_code = '01.GREEN' THEN cpr.application_id END) AS finv_green_completed_application,
        SUM(CASE WHEN cpr.age IS NOT NULL THEN age ELSE 0 END) AS age,
        SUM(CASE WHEN cpr.application_status NOT IN ('0.Incomplete', '1.In Progress') AND cpr.total_income IS NOT NULL AND cpr.total_income < 200000 THEN cpr.total_income ELSE 0 END) AS income,
        SUM(CASE WHEN cpr.application_status NOT IN ('0.Incomplete', '1.In Progress') AND cpr.total_expenses IS NOT NULL AND cpr.total_expenses < 200000 THEN cpr.total_expenses ELSE 0 END) AS expenses,
        SUM(CASE WHEN cpr.application_status NOT IN ('0.Incomplete', '1.In Progress') AND cpr.gross_surplus IS NOT NULL AND cpr.total_income < 200000 AND cpr.total_expenses < 200000 THEN cpr.gross_surplus ELSE 0 END) AS gross_surplus,
        
        COUNT(DISTINCT CASE WHEN cpr.application_tag = 'New' THEN cpr.application_id END) AS new_application,
        COUNT(DISTINCT CASE WHEN cpr.application_tag = 'New' AND cpr.application_status NOT IN ('0.Incomplete', '1.In Progress') THEN cpr.application_id END) AS new_completed_application,
        COUNT(DISTINCT CASE WHEN cpr.application_tag = 'New' AND LEFT(cpr.application_status,1) IN ('3', '4') THEN cpr.application_id END) AS new_approved_application,
        COUNT(DISTINCT CASE WHEN cpr.application_tag = 'New' AND cpr.application_status = '4.Funded' THEN cpr.application_id END) AS new_principal_cnt,
        SUM(CASE WHEN cpr.application_tag = 'New' AND cpr.application_status = '4.Funded' AND cpr.total_amount IS NOT NULL THEN cpr.total_amount ELSE 0 END) AS new_principal_amt,
        
        COUNT(DISTINCT CASE WHEN cpr.user_tag = 'New' THEN cpr.application_id END) AS new_user_application,
        COUNT(DISTINCT CASE WHEN cpr.user_tag = 'New' AND cpr.application_status NOT IN ('0.Incomplete', '1.In Progress') THEN cpr.application_id END) AS new_user_completed_application,
        COUNT(DISTINCT CASE WHEN cpr.user_tag = 'New' AND LEFT(cpr.application_status,1) IN ('3', '4') THEN cpr.application_id END) AS new_user_approved_application,
        COUNT(DISTINCT CASE WHEN cpr.user_tag = 'New' AND cpr.application_status = '4.Funded' THEN cpr.application_id END) AS new_user_principal_cnt,
        SUM(CASE WHEN cpr.user_tag = 'New' AND application_status = '4.Funded' AND cpr.total_amount IS NOT NULL THEN cpr.total_amount ELSE 0 END) AS new_user_principal_amt,
        
        COUNT(CASE WHEN cpr.last_step='9.submitted' AND cpr.completed_step_day=0  THEN cpr.application_id END) AS t0_completed,
        COUNT(CASE WHEN cpr.last_step='9.submitted' AND cpr.completed_step_day<=1 THEN cpr.application_id END) AS t1_completed,
        COUNT(CASE WHEN cpr.last_step='9.submitted' AND cpr.completed_step_day<=2 THEN cpr.application_id END) AS t2_completed,
        COUNT(CASE WHEN cpr.last_step='9.submitted' AND cpr.completed_step_day<=7 THEN cpr.application_id END) AS t7_completed,
        
        COUNT(CASE WHEN LEFT(cpr.application_status,1) IN ('3','4') AND cpr.risk_approved_day=0  THEN cpr.application_id END) AS t0_approved,
        COUNT(CASE WHEN LEFT(cpr.application_status,1) IN ('3','4') AND cpr.risk_approved_day<=1 THEN cpr.application_id END) AS t1_approved,
        COUNT(CASE WHEN LEFT(cpr.application_status,1) IN ('3','4') AND cpr.risk_approved_day<=2 THEN cpr.application_id END) AS t2_approved,
        COUNT(CASE WHEN LEFT(cpr.application_status,1) IN ('3','4') AND cpr.risk_approved_day<=7 THEN cpr.application_id END) AS t7_approved,
        
        COUNT(CASE WHEN LEFT(cpr.application_status,1) IN ('3','4') AND cpr.assessment_status LIKE '%Auto Approved%'  AND cpr.risk_approved_day=0  THEN cpr.application_id END) AS t0_auto_approved,
        COUNT(CASE WHEN LEFT(cpr.application_status,1) IN ('3','4') AND cpr.assessment_status LIKE '%Auto Approved%'  AND cpr.risk_approved_day<=1 THEN cpr.application_id END) AS t1_auto_approved,
        COUNT(CASE WHEN LEFT(cpr.application_status,1) IN ('3','4') AND cpr.assessment_status LIKE '%Auto Approved%'  AND cpr.risk_approved_day<=2 THEN cpr.application_id END) AS t2_auto_approved,
        COUNT(CASE WHEN LEFT(cpr.application_status,1) IN ('3','4') AND cpr.assessment_status LIKE '%Auto Approved%'  AND cpr.risk_approved_day<=7 THEN cpr.application_id END) AS t7_auto_approved,
        
        COUNT(CASE WHEN LEFT(cpr.application_status,1) IN ('3','4') AND cpr.assessment_status LIKE '%Manual Approved%' AND cpr.risk_approved_day=0  THEN cpr.application_id END) AS t0_manual_approved,
        COUNT(CASE WHEN LEFT(cpr.application_status,1) IN ('3','4') AND cpr.assessment_status LIKE '%Manual Approved%' AND cpr.risk_approved_day<=1 THEN cpr.application_id END) AS t1_manual_approved,
        COUNT(CASE WHEN LEFT(cpr.application_status,1) IN ('3','4') AND cpr.assessment_status LIKE '%Manual Approved%' AND cpr.risk_approved_day<=2 THEN cpr.application_id END) AS t2_manual_approved,
        COUNT(CASE WHEN LEFT(cpr.application_status,1) IN ('3','4') AND cpr.assessment_status LIKE '%Manual Approved%' AND cpr.risk_approved_day<=7 THEN cpr.application_id END) AS t7_manual_approved,
        
        COUNT(CASE WHEN cpr.application_status='2.3.Risk Declined' AND cpr.assessment_status LIKE '%Auto Declined%'   AND cpr.risk_declined_day=0  THEN cpr.application_id END) AS t0_auto_declined,
        COUNT(CASE WHEN cpr.application_status='2.3.Risk Declined' AND cpr.assessment_status LIKE '%Auto Declined%'   AND cpr.risk_declined_day<=1 THEN cpr.application_id END) AS t1_auto_declined,
        COUNT(CASE WHEN cpr.application_status='2.3.Risk Declined' AND cpr.assessment_status LIKE '%Auto Declined%'   AND cpr.risk_declined_day<=2 THEN cpr.application_id END) AS t2_auto_declined,
        COUNT(CASE WHEN cpr.application_status='2.3.Risk Declined' AND cpr.assessment_status LIKE '%Auto Declined%'   AND cpr.risk_declined_day<=7 THEN cpr.application_id END) AS t7_auto_declined,
        
        COUNT(CASE WHEN cpr.application_status='2.3.Risk Declined' AND cpr.assessment_status LIKE '%Manual Declined%' AND cpr.risk_declined_day=0  THEN cpr.application_id END) AS t0_manual_declined,
        COUNT(CASE WHEN cpr.application_status='2.3.Risk Declined' AND cpr.assessment_status LIKE '%Manual Declined%' AND cpr.risk_declined_day<=1 THEN cpr.application_id END) AS t1_manual_declined,
        COUNT(CASE WHEN cpr.application_status='2.3.Risk Declined' AND cpr.assessment_status LIKE '%Manual Declined%' AND cpr.risk_declined_day<=2 THEN cpr.application_id END) AS t2_manual_declined,
        COUNT(CASE WHEN cpr.application_status='2.3.Risk Declined' AND cpr.assessment_status LIKE '%Manual Declined%' AND cpr.risk_declined_day<=7 THEN cpr.application_id END) AS t7_manual_declined,
        
        COUNT(CASE WHEN cpr.application_status='4.Funded' AND cpr.dispersal_day=0  THEN cpr.application_id END) AS t0_dispersal,
        COUNT(CASE WHEN cpr.application_status='4.Funded' AND cpr.dispersal_day<=1 THEN cpr.application_id END) AS t1_dispersal,
        COUNT(CASE WHEN cpr.application_status='4.Funded' AND cpr.dispersal_day<=2 THEN cpr.application_id END) AS t2_dispersal,
        COUNT(CASE WHEN cpr.application_status='4.Funded' AND cpr.dispersal_day<=7 THEN cpr.application_id END) AS t7_dispersal,
        
        SUM(CASE WHEN cpr.application_status='4.Funded' AND cpr.dispersal_day=0  THEN cpr.total_amount ELSE 0 END) AS t0_dispersal_amount,
        SUM(CASE WHEN cpr.application_status='4.Funded' AND cpr.dispersal_day<=1 THEN cpr.total_amount ELSE 0 END) AS t1_dispersal_amount,
        SUM(CASE WHEN cpr.application_status='4.Funded' AND cpr.dispersal_day<=2 THEN cpr.total_amount ELSE 0 END) AS t2_dispersal_amount,
        SUM(CASE WHEN cpr.application_status='4.Funded' AND cpr.dispersal_day<=7 THEN cpr.total_amount ELSE 0 END) AS t7_dispersal_amount
    FROM 
        (SELECT *,
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
        ) AS cpr
    LEFT JOIN ba.mkt_attribution_fundo AS af
    ON cpr.application_id = af.application_id
    WHERE cpr.application_date>='2025-04-01'
    GROUP BY 1,2,3) b
ON driver.biz_date = b.application_date
AND driver.channel = b.attributed_utm
AND driver.biz_campaign_name = b.attributed_campaign

LEFT JOIN
   (SELECT 
        application_date,
        attributed_utm,
        attributed_campaign,
        SUM(pred_funded) AS pred_funded,
        SUM(pred_funded_amt) AS pred_funded_amt,
        SUM(CASE WHEN user_tag='New' THEN pred_funded ELSE 0 END) AS pred_funded_new,
        SUM(CASE WHEN user_tag='New' THEN pred_funded_amt ELSE 0 END) AS pred_funded_amt_new
    FROM 
        (SELECT *,
            ROW_NUMBER() OVER (PARTITION BY application_date, user_tag, attributed_utm, attributed_campaign, attributed_term ORDER BY observe_date DESC) AS seq_no
        FROM mkt.mkt_t7_cpfl_forecast)
    WHERE seq_no = 1
    GROUP BY 1,2,3
    ) f
ON driver.biz_date = f.application_date 
AND driver.channel = f.attributed_utm
AND driver.biz_campaign_name = f.attributed_campaign
ORDER BY 1,2,3,4,5;