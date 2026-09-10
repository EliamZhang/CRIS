DROP TABLE IF EXISTS ba.iterable_dashboard;
CREATE TABLE IF NOT EXISTS ba.iterable_dashboard AS
SELECT
    ir.campaign_id,
    ir.campaign_name,
    ir.message_medium,
    ir.audience,
    ir.email_type,
    ir.launch_time,
    ir.launch_hour,
    ir.launch_date,
    ir.launch_dow,
    ir.launch_week,
    ir.launch_month,
    ir.ls_application_tag,
    ir.ls_user_tag,

    CASE WHEN ir.application_date  IS NOT NULL THEN CAST(ir.application_date  AS STRING) ELSE 'N/A' END AS application_date,
    CASE WHEN ir.application_week  IS NOT NULL THEN CAST(ir.application_week  AS STRING) ELSE 'N/A' END AS application_week,
    CASE WHEN ir.application_month IS NOT NULL THEN CAST(ir.application_month AS STRING) ELSE 'N/A' END AS application_month,
    CASE WHEN ir.dispersal_date  IS NOT NULL THEN CAST(ir.dispersal_date  AS STRING) ELSE 'N/A' END AS dispersal_date,
    CASE WHEN ir.dispersal_week  IS NOT NULL THEN CAST(ir.dispersal_week  AS STRING) ELSE 'N/A' END AS dispersal_week,
    CASE WHEN ir.dispersal_month IS NOT NULL THEN CAST(ir.dispersal_month AS STRING) ELSE 'N/A' END AS dispersal_month,

    ir.traffic_source,
    ir.app_platform,
    ir.app_side_completed,
    ir.completed_step,
    ir.last_step AS dropoff_step,
    ir.application_status,

    ir.application_tag,
    ir.user_tag,
    ir.loan_tag,
    ir.requested_loan_tag,
    CASE
        WHEN ir.gross_surplus <= 0 OR ir.gross_surplus IS NULL OR ir.total_income > 200000 OR ir.total_expenses > 200000 THEN '99.N/A'
        WHEN ir.gross_surplus > 0 AND ir.gross_surplus < 200 THEN '04.(0;200)'
        WHEN ir.gross_surplus >= 200 AND ir.gross_surplus < 500 THEN '03.[200;500)'
        WHEN ir.gross_surplus >= 500 AND ir.gross_surplus < 1000 THEN '02.[500;1000)'
        WHEN ir.gross_surplus >= 1000 THEN '01.[1000;+)'
    END AS gross_surplus_bucket,

    ir.risk_level,
    ir.finv_color_code,

    CASE
      WHEN ir.previous_application_interval IS NULL OR ir.previous_application_interval <= 0 THEN '99.N/A'
      WHEN ir.previous_application_interval <= 30   THEN '01.(0;30]'
      WHEN ir.previous_application_interval <= 90   THEN '02.(30;90]'
      WHEN ir.previous_application_interval <= 180  THEN '03.(90;180]'
      WHEN ir.previous_application_interval <= 360  THEN '04.(180;360]'
      WHEN ir.previous_application_interval <= 540  THEN '05.(360;540]'
      ELSE '06.(540;+)'
    END AS previous_application_interval_bucket,

    
    CASE 
      WHEN ir.age IS NULL OR ir.age <= 0 THEN '99.N/A' 
      WHEN ir.age >= 55 THEN '06.[55;+)' 
      WHEN ir.age >= 48 AND ir.age < 55 THEN '05.[48;55)' 
      WHEN ir.age >= 40 AND ir.age < 48 THEN '04.[40;48)' 
      WHEN ir.age >= 30 AND ir.age < 40 THEN '03.[30;40)' 
      WHEN ir.age >= 24 AND ir.age < 30 THEN '02.[24;30)' 
      WHEN ir.age >= 18 AND ir.age < 24 THEN '01.[18;24)' 
      WHEN ir.age < 18 THEN '00.(-;18)' 
    END AS age_bucket,

    -- =========================
    -- 指标字段（聚合）
    -- =========================
    COUNT(DISTINCT ir.user_id) AS send_cnt,

    SUM(CASE WHEN ir.bounce_flag = 1 THEN 1 ELSE 0 END) AS bounced_cnt,
    SUM(CASE WHEN ir.open_flag = 1 THEN 1 ELSE 0 END) AS opened_cnt,
    SUM(CASE WHEN ir.click_flag = 1 THEN 1 ELSE 0 END) AS clicked_cnt,
    SUM(CASE WHEN ir.unsubscribe_flag = 1 THEN 1 ELSE 0 END) AS unsubscribed_cnt,
    SUM(CASE WHEN ir.complaint_flag = 1 THEN 1 ELSE 0 END) AS complained_cnt,

    COUNT(ir.application_id) AS application,

    COUNT(DISTINCT CASE WHEN ir.application_status NOT IN ('0.Incomplete', '1.In Progress') THEN ir.application_id END) AS completed_application,
    COUNT(DISTINCT CASE WHEN ir.application_status NOT IN ('0.Incomplete', '1.In Progress') AND ir.app_side_completed=1 THEN ir.application_id END) AS app_side_completed_application,

    COUNT(DISTINCT CASE WHEN LEFT(ir.application_status,1) IN ('3', '4') THEN ir.application_id END) AS approved_application,
    COUNT(DISTINCT CASE WHEN LEFT(ir.application_status,1) IN ('3', '4') AND ir.assessment_status LIKE '%Auto Approved%' THEN ir.application_id END) AS auto_approved_application,
    COUNT(DISTINCT CASE WHEN LEFT(ir.application_status,1) IN ('3', '4') AND ir.assessment_status LIKE '%Manual Approved%' THEN ir.application_id END) AS manual_approved_application,

    COUNT(DISTINCT CASE WHEN ir.application_status = '2.3.Risk Declined' THEN ir.application_id END) AS declined_application,
    COUNT(DISTINCT CASE WHEN ir.application_status = '2.3.Risk Declined' AND ir.assessment_status LIKE '%Auto Declined%' THEN ir.application_id END) AS auto_declined_application,
    COUNT(DISTINCT CASE WHEN ir.application_status = '2.3.Risk Declined' AND ir.assessment_status LIKE '%Manual Declined%' THEN ir.application_id END) AS manual_declined_application,

    COUNT(DISTINCT CASE WHEN ir.application_status = '2.1.Submitted Withdrawn' THEN ir.application_id END) AS withdrawn_application,
    COUNT(DISTINCT CASE WHEN ir.application_status = '2.1.Submitted Withdrawn' AND ir.assessment_status LIKE '%Auto Withdrawn%' THEN ir.application_id END) AS auto_withdrawn_application,
    COUNT(DISTINCT CASE WHEN ir.application_status = '2.1.Submitted Withdrawn' AND ir.assessment_status LIKE '%Manual Withdrawn%' THEN ir.application_id END) AS manual_withdrawn_application,

    COUNT(DISTINCT CASE WHEN ir.application_status = '4.Funded' THEN ir.application_id END) AS principal_cnt,
    SUM(CASE WHEN ir.application_status = '4.Funded' AND ir.loan_amount IS NOT NULL THEN ir.loan_amount ELSE 0 END) AS principal_amt,

    SUM(CASE WHEN ir.requested_loan_amount IS NOT NULL THEN ir.requested_loan_amount ELSE 0 END) AS requested_amt,
    SUM(CASE WHEN ir.application_status = '4.Funded' THEN ir.requested_loan_amount ELSE 0 END) AS funded_request_amt,

    SUM(CASE WHEN LEFT(ir.application_status,1) IN ('3', '4') AND ir.loan_amount IS NOT NULL
         THEN COALESCE(ir.total_loan_amount, 0) ELSE 0 END) AS approved_amt,


    SUM(CASE WHEN ir.original_term_avg > 0 THEN ir.original_term_avg ELSE 0 END) AS original_term_length,
    SUM(CASE WHEN ir.actual_term_avg > 0 THEN ir.actual_term_avg ELSE 0 END) AS actual_term_length,

    SUM(CASE WHEN ir.age IS NOT NULL THEN ir.age ELSE 0 END) AS age,
    SUM(CASE WHEN ir.final_probability IS NOT NULL THEN ir.final_probability ELSE 0 END) AS risk_score,

    SUM(CASE WHEN ir.total_income IS NOT NULL AND ir.total_income < 200000 THEN ir.total_income ELSE 0 END) AS income,
    SUM(CASE WHEN ir.application_status = '4.Funded' AND ir.total_income IS NOT NULL AND ir.total_income < 200000 THEN ir.total_income ELSE 0 END) AS funded_income,

    SUM(CASE WHEN ir.total_expenses IS NOT NULL AND ir.total_expenses < 200000 THEN ir.total_expenses ELSE 0 END) AS expenses,
    SUM(CASE WHEN ir.gross_surplus IS NOT NULL AND ir.total_income < 200000 AND ir.total_expenses < 200000 THEN ir.gross_surplus ELSE 0 END) AS gross_surplus,
    SUM(CASE WHEN ir.net_surplus IS NOT NULL AND ir.total_income < 200000 AND ir.total_expenses < 200000 THEN ir.net_surplus ELSE 0 END) AS net_surplus,

    SUM(CASE WHEN ir.default_income IS NOT NULL AND ir.default_income < 200000 THEN ir.default_income ELSE 0 END) AS default_income,
    SUM(CASE WHEN ir.default_expenses IS NOT NULL AND ir.default_expenses < 200000 THEN ir.default_expenses ELSE 0 END) AS default_expenses,
    SUM(CASE WHEN ir.default_gross_surplus IS NOT NULL AND ir.default_income < 200000 AND ir.default_expenses < 200000 THEN ir.default_gross_surplus ELSE 0 END) AS default_gross_surplus,

    COUNT(CASE WHEN ir.application_flag=1 AND ir.response_day=0  THEN ir.application_id END) AS t0_application,
    COUNT(CASE WHEN ir.application_flag=1 AND ir.response_day<=1 THEN ir.application_id END) AS t1_application,
    COUNT(CASE WHEN ir.application_flag=1 AND ir.response_day<=2 THEN ir.application_id END) AS t2_application,
    COUNT(CASE WHEN ir.application_flag=1 AND ir.response_day<=7 THEN ir.application_id END) AS t7_application,

    COUNT(CASE WHEN ir.dispersal_flag=1 AND ir.conversion_day=0  THEN ir.application_id END) AS t0_dispersal,
    COUNT(CASE WHEN ir.dispersal_flag=1 AND ir.conversion_day<=1 THEN ir.application_id END) AS t1_dispersal,
    COUNT(CASE WHEN ir.dispersal_flag=1 AND ir.conversion_day<=2 THEN ir.application_id END) AS t2_dispersal,
    COUNT(CASE WHEN ir.dispersal_flag=1 AND ir.conversion_day<=7 THEN ir.application_id END) AS t7_dispersal,

    SUM(CASE WHEN ir.dispersal_flag=1 AND ir.conversion_day=0  THEN ir.loan_amount ELSE 0 END) AS t0_dispersal_amount,
    SUM(CASE WHEN ir.dispersal_flag=1 AND ir.conversion_day<=1 THEN ir.loan_amount ELSE 0 END) AS t1_dispersal_amount,
    SUM(CASE WHEN ir.dispersal_flag=1 AND ir.conversion_day<=2 THEN ir.loan_amount ELSE 0 END) AS t2_dispersal_amount,
    SUM(CASE WHEN ir.dispersal_flag=1 AND ir.conversion_day<=7 THEN ir.loan_amount ELSE 0 END) AS t7_dispersal_amount

FROM ba.iterable_responses ir

GROUP BY
    1,2,3,4,5,
    6,7,8,9,10,
    11,12,13,14,
    15,16,17,18,19,20,
    21,22,23,24,
    25,26,27,28,29,30,
    31,32,33,34
ORDER BY
    1,2,3,4,5,
    6,7,8,9,10,
    11,12,13,14,
    15,16,17,18,19,20,
    21,22,23,24,
    25,26,27,28,29,30,
    31,32,33,34
;