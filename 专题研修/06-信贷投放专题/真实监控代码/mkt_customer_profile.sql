DROP TABLE IF EXISTS mkt.mkt_customer_profile;
CREATE TABLE IF NOT EXISTS mkt.mkt_customer_profile AS
SELECT 
    application_month,
    application_week,
    application_date,
    CASE WHEN dispersal_month IS NULL THEN 'N/A' ELSE dispersal_month END AS dispersal_month,
    CASE WHEN dispersal_week IS NULL THEN 'N/A' ELSE dispersal_week END AS dispersal_week,
    CASE WHEN dispersal_date IS NULL THEN 'N/A' ELSE dispersal_date END AS dispersal_date,
    application_tag,
    requested_loan_tag,
    loan_tag,
    user_tag,
    traffic_source,
    app_platform,
    app_side_completed,
    completed_step,
    last_step AS dropoff_step,
    attributed_utm,
    attributed_category,
    attributed_medium,
    attributed_campaign,
    attributed_term,
    application_status, 
    CASE 
            WHEN LEFT(application_status,1) IN ('3', '4') THEN 
                    CASE 
                            WHEN assessment_status LIKE '%Auto Approved%' THEN 'Auto Approved' 
                            ELSE 'Manual Approved'
                    END 
            ELSE 'Declined'
    END AS approval_tag,
    risk_level,
    finv_color_code,
    COUNT(DISTINCT application_id) AS application,
    COUNT(DISTINCT CASE WHEN application_status NOT IN ('0.Incomplete', '1.In Progress') THEN application_id END) AS completed_application,
    COUNT(DISTINCT CASE WHEN application_status NOT IN ('0.Incomplete', '1.In Progress') AND app_side_completed=1 THEN application_id END) AS app_side_completed_application,
    COUNT(DISTINCT CASE WHEN LEFT(application_status,1) IN ('3', '4') THEN application_id END) AS approved_application,
    COUNT(DISTINCT CASE WHEN LEFT(application_status,1) IN ('3', '4') AND assessment_status LIKE '%Auto Approved%' THEN application_id END) AS auto_approved_application,
    COUNT(DISTINCT CASE WHEN LEFT(application_status,1) IN ('3', '4') AND assessment_status LIKE '%Manual Approved%' THEN application_id END) AS manual_approved_application,
    COUNT(DISTINCT CASE WHEN application_status = '2.3.Risk Declined' THEN application_id END) AS declined_application,
    COUNT(DISTINCT CASE WHEN application_status = '2.3.Risk Declined' AND assessment_status LIKE '%Auto Declined%' THEN application_id END) AS auto_declined_application,
    COUNT(DISTINCT CASE WHEN application_status = '2.3.Risk Declined' AND assessment_status LIKE '%Manual Declined%' THEN application_id END) AS manual_declined_application,
    COUNT(DISTINCT CASE WHEN application_status = '2.1.Submitted Withdrawn' THEN application_id END) AS withdrawn_application,
    COUNT(DISTINCT CASE WHEN application_status = '2.1.Submitted Withdrawn' AND assessment_status LIKE '%Auto Withdrawn%' THEN application_id END) AS auto_withdrawn_application,
    COUNT(DISTINCT CASE WHEN application_status = '2.1.Submitted Withdrawn' AND assessment_status LIKE '%Manual Withdrawn%' THEN application_id END) AS manual_withdrawn_application,
    COUNT(DISTINCT CASE WHEN application_status = '4.Funded' THEN application_id END) AS principal_cnt,
    SUM(CASE WHEN application_status = '4.Funded' AND total_amount IS NOT NULL THEN total_amount ELSE 0 END) AS principal_amt,
    SUM(CASE WHEN application_status NOT IN ('0.Incomplete', '1.In Progress') AND requested_loan_amount IS NOT NULL THEN requested_loan_amount ELSE 0 END) AS requested_amt,
    SUM(CASE WHEN application_status = '4.Funded' THEN requested_loan_amount ELSE 0 END) AS funded_request_amt,
    SUM(CASE WHEN LEFT(application_status,1) IN ('3', '4')AND total_amount IS NOT NULL THEN total_amount ELSE 0 END) AS approved_amt,
    SUM(CASE WHEN age IS NOT NULL THEN age ELSE 0 END) AS age,
    SUM(CASE WHEN application_status NOT IN ('0.Incomplete', '1.In Progress') AND total_income IS NOT NULL AND total_income < 200000 THEN total_income ELSE 0 END) AS income,
    SUM(CASE WHEN application_status = '4.Funded' AND total_income IS NOT NULL AND total_income < 200000 THEN total_income ELSE 0 END) AS funded_income,
    SUM(CASE WHEN application_status NOT IN ('0.Incomplete', '1.In Progress') AND total_expenses IS NOT NULL AND total_expenses < 200000 THEN total_expenses ELSE 0 END) AS expenses,
    -- SUM(CASE WHEN base_probability IS NULL OR base_probability <= 0 OR base_probability > 1 THEN 0 ELSE base_probability END) AS base_probability,
    -- SUM(CASE WHEN dpd_7_probability IS NULL OR dpd_7_probability <= 0 OR dpd_7_probability > 1 THEN 0 ELSE dpd_7_probability END) AS dpd_7_probability,
    -- SUM(CASE WHEN dpd_14_probability IS NULL OR dpd_14_probability <= 0 OR dpd_14_probability > 1 THEN 0 ELSE dpd_14_probability END) AS dpd_14_probability,
    -- SUM(CASE WHEN dpd_21_probability IS NULL OR dpd_21_probability <= 0 OR dpd_21_probability > 1 THEN 0 ELSE dpd_21_probability END) AS dpd_21_probability,
    -- SUM(CASE WHEN dpd_28_probability IS NULL OR dpd_28_probability <= 0 OR dpd_28_probability > 1 THEN 0 ELSE dpd_28_probability END) AS dpd_28_probability,
    -- SUM(CASE WHEN dpd_35_probability IS NULL OR dpd_35_probability <= 0 OR dpd_35_probability > 1 THEN 0 ELSE dpd_35_probability END) AS dpd_35_probability,
    -- SUM(CASE WHEN dpd_42_probability IS NULL OR dpd_42_probability <= 0 OR dpd_42_probability > 1 THEN 0 ELSE dpd_42_probability END) AS dpd_42_probability,
    -- SUM(CASE WHEN dpd_49_probability IS NULL OR dpd_49_probability <= 0 OR dpd_49_probability > 1 THEN 0 ELSE dpd_49_probability END) AS dpd_49_probability,
    -- SUM(CASE WHEN final_probability IS NULL OR final_probability <= 0 OR final_probability > 1 THEN 0 ELSE final_probability END) AS final_probability,
    
    ROUND(SUM(CASE WHEN dpd_days_mob0 >= 5 THEN estimate_principal_remaining_mob0 ELSE 0 END), 2) AS est_principal_remaining_5_amt_mob0,
    COUNT(DISTINCT CASE WHEN dpd_days_mob0 >= 5 AND estimate_principal_remaining_mob0 > 0 THEN application_id END) AS est_principal_remaining_5_cnt_mob0,
    ROUND(SUM(CASE WHEN dpd_days_mob1 >= 5 THEN estimate_principal_remaining_mob1 ELSE 0 END), 2) AS est_principal_remaining_5_amt_mob1,
    COUNT(DISTINCT CASE WHEN dpd_days_mob1 >= 5 AND estimate_principal_remaining_mob1 > 0 THEN application_id END) AS est_principal_remaining_5_cnt_mob1,
    ROUND(SUM(CASE WHEN dpd_days_mob2 >= 30 THEN estimate_principal_remaining_mob2 ELSE 0 END), 2) AS est_principal_remaining_30_amt_mob2,
    COUNT(DISTINCT CASE WHEN dpd_days_mob2 >= 30 AND estimate_principal_remaining_mob2 > 0 THEN application_id END) AS est_principal_remaining_30_cnt_mob2,
    ROUND(SUM(CASE WHEN dpd_days_mob3 >= 30 THEN estimate_principal_remaining_mob3 ELSE 0 END), 2) AS est_principal_remaining_30_amt_mob3,
    COUNT(DISTINCT CASE WHEN dpd_days_mob3 >= 30 AND estimate_principal_remaining_mob3 > 0 THEN application_id END) AS est_principal_remaining_30_cnt_mob3,
    ROUND(SUM(CASE WHEN dpd_days_mob4 >= 30 THEN estimate_principal_remaining_mob4 ELSE 0 END), 2) AS est_principal_remaining_30_amt_mob4,
    COUNT(DISTINCT CASE WHEN dpd_days_mob4 >= 30 AND estimate_principal_remaining_mob4 > 0 THEN application_id END) AS est_principal_remaining_30_cnt_mob4,
    ROUND(SUM(CASE WHEN dpd_days_mob4 >= 60 THEN estimate_principal_remaining_mob4 ELSE 0 END), 2) AS est_principal_remaining_60_amt_mob4,
    COUNT(DISTINCT CASE WHEN dpd_days_mob4 >= 60 AND estimate_principal_remaining_mob4 > 0 THEN application_id END) AS est_principal_remaining_60_cnt_mob4
    
    -- ROUND(SUM(CASE WHEN dpd_days_ever_mob0 >= 5 THEN estimate_principal_remaining_mob0 ELSE 0 END), 2) AS est_principal_remaining_ever_5_amt_mob0,
    -- COUNT(DISTINCT CASE WHEN dpd_days_ever_mob0 >= 5 THEN application_id END) AS est_principal_remaining_ever_5_cnt_mob0,
    -- ROUND(SUM(CASE WHEN dpd_days_ever_mob1 >= 5 THEN estimate_principal_remaining_mob1 ELSE 0 END), 2) AS est_principal_remaining_ever_5_amt_mob1,
    -- COUNT(DISTINCT CASE WHEN dpd_days_ever_mob1 >= 5 THEN application_id END) AS est_principal_remaining_ever_5_cnt_mob1,
    -- ROUND(SUM(CASE WHEN dpd_days_ever_mob2 >= 30 THEN estimate_principal_remaining_mob2 ELSE 0 END), 2) AS est_principal_remaining_ever_30_amt_mob2,
    -- COUNT(DISTINCT CASE WHEN dpd_days_ever_mob2 >= 30 THEN application_id END) AS est_principal_remaining_ever_30_cnt_mob2,
    -- ROUND(SUM(CASE WHEN dpd_days_ever_mob3 >= 30 THEN estimate_principal_remaining_mob3 ELSE 0 END), 2) AS est_principal_remaining_ever_30_amt_mob3,
    -- COUNT(DISTINCT CASE WHEN dpd_days_ever_mob3 >= 30 THEN application_id END) AS est_principal_remaining_ever_30_cnt_mob3

FROM  
    ba.customer_profile_rawdata
WHERE 
    application_date >= '2023-10-01'
GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24
ORDER BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24
;