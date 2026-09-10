DROP TABLE IF EXISTS mkt.mkt_customer_profile_fundo;
CREATE TABLE IF NOT EXISTS mkt.mkt_customer_profile_fundo AS
SELECT 
    cpr.application_month,
    cpr.application_week,
    cpr.application_date,
    CASE WHEN cpr.dispersal_month IS NULL THEN 'N/A' ELSE cpr.dispersal_month END AS dispersal_month,
    CASE WHEN cpr.dispersal_week IS NULL THEN 'N/A' ELSE cpr.dispersal_week END AS dispersal_week,
    CASE WHEN dispersal_date IS NULL THEN 'N/A' ELSE dispersal_date END AS dispersal_date,
    cpr.application_tag,
    cpr.requested_loan_tag,
    cpr.loan_tag,
    cpr.user_tag,
    cpr.traffic_source,
    cpr.app_platform,
    cpr.app_side_completed,
    cpr.completed_step,
    cpr.last_step AS dropoff_step,
    CASE WHEN af.attribution_source IS NULL THEN 'Organic' ELSE af.attribution_source END AS attributed_utm,
    CASE WHEN af.attributed_category IS NULL THEN 'Organic' ELSE af.attributed_category END AS attributed_category,
    CASE WHEN af.attribution_medium IS NULL THEN 'Null' ELSE af.attribution_medium END AS attributed_medium,
    CASE WHEN af.attribution_campaign IS NULL THEN 'Null' ELSE af.attribution_campaign END AS attributed_campaign,
    CASE WHEN af.attribution_term IS NULL THEN 'Null' ELSE af.attribution_term END AS attributed_term,
    cpr.application_status, 
    CASE 
            WHEN LEFT(cpr.application_status,1) IN ('3', '4') THEN 
                    CASE 
                            WHEN cpr.assessment_status LIKE '%Auto Approved%' THEN 'Auto Approved' 
                            ELSE 'Manual Approved'
                    END 
            ELSE 'Declined'
    END AS approval_tag,
    cpr.risk_level,
    cpr.finv_color_code,
    COUNT(DISTINCT cpr.application_id) AS application,
    COUNT(DISTINCT CASE WHEN cpr.application_status NOT IN ('0.Incomplete', '1.In Progress') THEN cpr.application_id END) AS completed_application,
    COUNT(DISTINCT CASE WHEN cpr.application_status NOT IN ('0.Incomplete', '1.In Progress') AND cpr.app_side_completed=1 THEN cpr.application_id END) AS app_side_completed_application,
    COUNT(DISTINCT CASE WHEN LEFT(cpr.application_status,1) IN ('3', '4') THEN cpr.application_id END) AS approved_application,
    COUNT(DISTINCT CASE WHEN LEFT(cpr.application_status,1) IN ('3', '4') AND cpr.assessment_status LIKE '%Auto Approved%' THEN cpr.application_id END) AS auto_approved_application,
    COUNT(DISTINCT CASE WHEN LEFT(cpr.application_status,1) IN ('3', '4') AND cpr.assessment_status LIKE '%Manual Approved%' THEN cpr.application_id END) AS manual_approved_application,
    COUNT(DISTINCT CASE WHEN cpr.application_status = '2.3.Risk Declined' THEN cpr.application_id END) AS declined_application,
    COUNT(DISTINCT CASE WHEN cpr.application_status = '2.3.Risk Declined' AND cpr.assessment_status LIKE '%Auto Declined%' THEN cpr.application_id END) AS auto_declined_application,
    COUNT(DISTINCT CASE WHEN cpr.application_status = '2.3.Risk Declined' AND cpr.assessment_status LIKE '%Manual Declined%' THEN cpr.application_id END) AS manual_declined_application,
    COUNT(DISTINCT CASE WHEN cpr.application_status = '2.1.Submitted Withdrawn' THEN cpr.application_id END) AS withdrawn_application,
    COUNT(DISTINCT CASE WHEN cpr.application_status = '2.1.Submitted Withdrawn' AND cpr.assessment_status LIKE '%Auto Withdrawn%' THEN cpr.application_id END) AS auto_withdrawn_application,
    COUNT(DISTINCT CASE WHEN cpr.application_status = '2.1.Submitted Withdrawn' AND cpr.assessment_status LIKE '%Manual Withdrawn%' THEN cpr.application_id END) AS manual_withdrawn_application,
    COUNT(DISTINCT CASE WHEN cpr.application_status = '4.Funded' THEN cpr.application_id END) AS principal_cnt,
    SUM(CASE WHEN cpr.application_status = '4.Funded' AND cpr.total_amount IS NOT NULL THEN cpr.total_amount ELSE 0 END) AS principal_amt,
    SUM(CASE WHEN cpr.application_status NOT IN ('0.Incomplete', '1.In Progress') AND cpr.requested_loan_amount IS NOT NULL THEN cpr.requested_loan_amount ELSE 0 END) AS requested_amt,
    SUM(CASE WHEN cpr.application_status = '4.Funded' THEN cpr.requested_loan_amount ELSE 0 END) AS funded_request_amt,
    SUM(CASE WHEN LEFT(cpr.application_status,1) IN ('3', '4') AND cpr.total_amount IS NOT NULL THEN cpr.total_amount ELSE 0 END) AS approved_amt,
    SUM(CASE WHEN cpr.age IS NOT NULL THEN cpr.age ELSE 0 END) AS age,
    SUM(CASE WHEN cpr.application_status NOT IN ('0.Incomplete', '1.In Progress') AND cpr.total_income IS NOT NULL AND cpr.total_income < 200000 THEN cpr.total_income ELSE 0 END) AS income,
    SUM(CASE WHEN cpr.application_status = '4.Funded' AND cpr.total_income IS NOT NULL AND cpr.total_income < 200000 THEN cpr.total_income ELSE 0 END) AS funded_income,
    SUM(CASE WHEN cpr.application_status NOT IN ('0.Incomplete', '1.In Progress') AND cpr.total_expenses IS NOT NULL AND cpr.total_expenses < 200000 THEN cpr.total_expenses ELSE 0 END) AS expenses,
    
    -- SUM(CASE WHEN cpr.base_probability IS NULL OR cpr.base_probability <= 0 OR cpr.base_probability > 1 THEN 0 ELSE cpr.base_probability END) AS base_probability,
    -- SUM(CASE WHEN cpr.dpd_7_probability IS NULL OR cpr.dpd_7_probability <= 0 OR cpr.dpd_7_probability > 1 THEN 0 ELSE cpr.dpd_7_probability END) AS dpd_7_probability,
    -- SUM(CASE WHEN cpr.dpd_14_probability IS NULL OR cpr.dpd_14_probability <= 0 OR cpr.dpd_14_probability > 1 THEN 0 ELSE cpr.dpd_14_probability END) AS dpd_14_probability,
    -- SUM(CASE WHEN cpr.dpd_21_probability IS NULL OR cpr.dpd_21_probability <= 0 OR cpr.dpd_21_probability > 1 THEN 0 ELSE cpr.dpd_21_probability END) AS dpd_21_probability,
    -- SUM(CASE WHEN cpr.dpd_28_probability IS NULL OR cpr.dpd_28_probability <= 0 OR cpr.dpd_28_probability > 1 THEN 0 ELSE cpr.dpd_28_probability END) AS dpd_28_probability,
    -- SUM(CASE WHEN cpr.dpd_35_probability IS NULL OR cpr.dpd_35_probability <= 0 OR cpr.dpd_35_probability > 1 THEN 0 ELSE cpr.dpd_35_probability END) AS dpd_35_probability,
    -- SUM(CASE WHEN cpr.dpd_42_probability IS NULL OR cpr.dpd_42_probability <= 0 OR cpr.dpd_42_probability > 1 THEN 0 ELSE cpr.dpd_42_probability END) AS dpd_42_probability,
    -- SUM(CASE WHEN cpr.dpd_49_probability IS NULL OR cpr.dpd_49_probability <= 0 OR cpr.dpd_49_probability > 1 THEN 0 ELSE cpr.dpd_49_probability END) AS dpd_49_probability,
    -- SUM(CASE WHEN cpr.final_probability IS NULL OR cpr.final_probability <= 0 OR cpr.final_probability > 1 THEN 0 ELSE cpr.final_probability END) AS final_probability,
    
    ROUND(SUM(CASE WHEN cpr.dpd_days_mob0 >= 5 THEN cpr.estimate_principal_remaining_mob0 ELSE 0 END), 2) AS est_principal_remaining_5_amt_mob0,
    COUNT(DISTINCT CASE WHEN cpr.dpd_days_mob0 >= 5 AND cpr.estimate_principal_remaining_mob0 > 0 THEN cpr.application_id END) AS est_principal_remaining_5_cnt_mob0,
    ROUND(SUM(CASE WHEN cpr.dpd_days_mob1 >= 5 THEN cpr.estimate_principal_remaining_mob1 ELSE 0 END), 2) AS est_principal_remaining_5_amt_mob1,
    COUNT(DISTINCT CASE WHEN cpr.dpd_days_mob1 >= 5 AND cpr.estimate_principal_remaining_mob1 > 0 THEN cpr.application_id END) AS est_principal_remaining_5_cnt_mob1,
    ROUND(SUM(CASE WHEN cpr.dpd_days_mob2 >= 30 THEN cpr.estimate_principal_remaining_mob2 ELSE 0 END), 2) AS est_principal_remaining_30_amt_mob2,
    COUNT(DISTINCT CASE WHEN cpr.dpd_days_mob2 >= 30 AND cpr.estimate_principal_remaining_mob2 > 0 THEN cpr.application_id END) AS est_principal_remaining_30_cnt_mob2,
    ROUND(SUM(CASE WHEN cpr.dpd_days_mob3 >= 30 THEN cpr.estimate_principal_remaining_mob3 ELSE 0 END), 2) AS est_principal_remaining_30_amt_mob3,
    COUNT(DISTINCT CASE WHEN cpr.dpd_days_mob3 >= 30 AND cpr.estimate_principal_remaining_mob3 > 0 THEN cpr.application_id END) AS est_principal_remaining_30_cnt_mob3,
    ROUND(SUM(CASE WHEN cpr.dpd_days_mob4 >= 30 THEN cpr.estimate_principal_remaining_mob4 ELSE 0 END), 2) AS est_principal_remaining_30_amt_mob4,
    COUNT(DISTINCT CASE WHEN cpr.dpd_days_mob4 >= 30 AND cpr.estimate_principal_remaining_mob4 > 0 THEN cpr.application_id END) AS est_principal_remaining_30_cnt_mob4,
    ROUND(SUM(CASE WHEN cpr.dpd_days_mob4 >= 60 THEN cpr.estimate_principal_remaining_mob4 ELSE 0 END), 2) AS est_principal_remaining_60_amt_mob4,
    COUNT(DISTINCT CASE WHEN cpr.dpd_days_mob4 >= 60 AND cpr.estimate_principal_remaining_mob4 > 0 THEN cpr.application_id END) AS est_principal_remaining_60_cnt_mob4
    
    -- ROUND(SUM(CASE WHEN cpr.dpd_days_ever_mob0 >= 5 THEN cpr.estimate_principal_remaining_mob0 ELSE 0 END), 2) AS est_principal_remaining_ever_5_amt_mob0,
    -- COUNT(DISTINCT CASE WHEN cpr.dpd_days_ever_mob0 >= 5 THEN cpr.application_id END) AS est_principal_remaining_ever_5_cnt_mob0,
    -- ROUND(SUM(CASE WHEN cpr.dpd_days_ever_mob1 >= 5 THEN cpr.estimate_principal_remaining_mob1 ELSE 0 END), 2) AS est_principal_remaining_ever_5_amt_mob1,
    -- COUNT(DISTINCT CASE WHEN cpr.dpd_days_ever_mob1 >= 5 THEN cpr.application_id END) AS est_principal_remaining_ever_5_cnt_mob1,
    -- ROUND(SUM(CASE WHEN cpr.dpd_days_ever_mob2 >= 30 THEN cpr.estimate_principal_remaining_mob2 ELSE 0 END), 2) AS est_principal_remaining_ever_30_amt_mob2,
    -- COUNT(DISTINCT CASE WHEN cpr.dpd_days_ever_mob2 >= 30 THEN cpr.application_id END) AS est_principal_remaining_ever_30_cnt_mob2,
    -- ROUND(SUM(CASE WHEN cpr.dpd_days_ever_mob3 >= 30 THEN cpr.estimate_principal_remaining_mob3 ELSE 0 END), 2) AS est_principal_remaining_ever_30_amt_mob3,
    -- COUNT(DISTINCT CASE WHEN cpr.dpd_days_ever_mob3 >= 30 THEN cpr.application_id END) AS est_principal_remaining_ever_30_cnt_mob3

FROM  
    ba.customer_profile_rawdata AS cpr
LEFT JOIN
    ba.mkt_attribution_fundo AS af
ON cpr.application_id = af.application_id
WHERE 
    cpr.application_date >= '2023-10-01'
GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24
ORDER BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24
;