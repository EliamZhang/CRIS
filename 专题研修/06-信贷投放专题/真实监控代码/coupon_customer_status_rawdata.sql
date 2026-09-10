INSERT OVERWRITE TABLE ba.coupon_customer_status_rawdata PARTITION (observe_date)

WITH application_history AS (
     SELECT
          la.user_id,
          la.application_id,
          la.application_time,
          DATE(la.application_date) AS application_date,
          la.application_month,
          DATE(la.dispersal_date) AS dispersal_date,
          DATE(la.scheduled_cleared_date) AS scheduled_cleared_date,
          la.user_tag,
          la.completed_step,
          DATE(la.completed_step_time) AS completed_step_date,
          la.last_status,
          DATE(la.last_status_time) AS last_status_date,
          la.application_status,
          la.status,
          la.total_amount,
          la.risk_level,
          la.finv_risk_level,
          la.finv_color_code,
          CASE WHEN dpd.dpd_days_ever IS NULL THEN 0 ELSE dpd.dpd_days_ever END AS dpd_days_ever,
          CASE WHEN dpd.dpd_days IS NULL THEN 0 ELSE dpd.dpd_days END AS dpd_days,
          CASE WHEN dpd.total_balance IS NULL THEN 0 ELSE dpd.total_balance END AS total_balance,
          CASE WHEN dpd.repaid_amount IS NULL THEN 0 ELSE dpd.repaid_amount END AS repaid_amount,
          CASE WHEN dpd.repaid_percentage IS NULL THEN 0 ELSE dpd.repaid_percentage END AS repaid_percentage,
          ROW_NUMBER() OVER(PARTITION BY la.user_id ORDER BY la.application_time DESC) AS sep_no_desc
     FROM ba.customer_profile_rawdata la
     LEFT JOIN 
          (SELECT
               la.user_id,
               la.id AS application_id,
               la.created_at AS application_date,
               DATE(la.dispersal_date) AS dispersal_date,
               t.actual_trx_date,
               IFNULL(dpds.days_past_due, 0) AS dpd_days,
               IFNULL(dpds.days_past_due_ever, 0) AS dpd_days_ever,
               osr.total_balance,
               osr.repaid_amount,
               osr.repaid_amount/osr.total_balance AS repaid_percentage
          FROM ods.aus_fundo_loans_loan_applications la
          LEFT JOIN 
               (SELECT application_id, 
                    MIN(actual_trx_date) AS actual_trx_date
               FROM 
                    (SELECT 
                         trx.*, 
                         CASE WHEN DATE(TIMESTAMP(trx.transaction_date)) >= DATE('2019-07-02') 
                              AND DATE(TIMESTAMP(trx.created_at)) > DATE(TIMESTAMP(trx.transaction_date)) 
                              THEN DATE(TIMESTAMP(trx.created_at))
                              ELSE DATE(TIMESTAMP(trx.transaction_date))
                         END AS actual_trx_date
                    FROM ods.aus_fundo_loans_transactions trx)
               WHERE actual_trx_date <= to_date('${yyyy-mm-dd}')
               GROUP BY application_id
               ) t 
          ON la.id = t.application_id 
          LEFT JOIN 
               (SELECT tpd.application_id,
                    MAX(tpd.days_past_due) AS days_past_due,
                    MAX(tpd.days_past_due_ever) AS days_past_due_ever
               FROM
                    (SELECT 
                         application_id, 
                         scheduled_amount,
                         DATE(scheduled_date) AS scheduled_date,
                         DATE(schedule_cleared_date) AS schedule_cleared_date,
                         CASE WHEN DATEDIFF(to_date('${yyyy-mm-dd}'), DATE(scheduled_date)) <= dpd_days 
                              THEN DATEDIFF(to_date('${yyyy-mm-dd}'), DATE(scheduled_date)) 
                              ELSE dpd_days 
                              END AS days_past_due_ever,
                         CASE WHEN DATEDIFF(to_date('${yyyy-mm-dd}'), DATE(scheduled_date)) <= dpd_days 
                              THEN DATEDIFF(to_date('${yyyy-mm-dd}'), DATE(scheduled_date)) 
                              ELSE 0 
                              END AS days_past_due
                    FROM ods.vintage_analysis_original_schedule_recoveries_v2
                    WHERE DATE(scheduled_date) < to_date('${yyyy-mm-dd}')
                    ORDER BY application_id, scheduled_date
                    ) tpd
               GROUP BY tpd.application_id
               ) dpds 
          ON la.id  = dpds.application_id
          LEFT JOIN 
              (SELECT 
                   application_id, 
                   SUM(scheduled_amount) AS total_balance,
                   SUM(CASE WHEN schedule_cleared_date IS NOT NULL AND DATE(schedule_cleared_date) < to_date('${yyyy-mm-dd}') THEN scheduled_amount ELSE 0 END) AS repaid_amount
              FROM ods.vintage_analysis_original_schedule_recoveries_v2
              GROUP BY 1) osr
          ON la.id=osr.application_id
          WHERE DATE(la.dispersal_date) <= to_date('${yyyy-mm-dd}') 
          AND t.actual_trx_date IS NOT NULL
          ) dpd
     ON la.application_id = dpd.application_id
     WHERE DATE(la.application_date) <= to_date('${yyyy-mm-dd}')
     ORDER BY la.user_id, la.application_id
),
user_history AS (
     SELECT 
          u.user_id,
          u.is_blacklisted, 
          u.do_not_market, 
          u.is_comms_unsubscribed, 
          u.invalid_email,
          u.mobile_verified, 
          u.email_verified, 
          u.precise_age AS age,
          CASE WHEN la.hardship_status = 1 THEN 1 ELSE 0 END AS hardship_status,
          CASE WHEN to_date(la.reapplication_activation_date, 'yyyy-MM-dd')>=to_date('${yyyy-mm-dd}') THEN 1 ELSE 0 END AS probation_period_flag,
          COALESCE(app.in_complete_process_flag, 0) AS in_complete_process_flag,
          COALESCE(app.in_process_flag, 0) AS in_process_flag,
          COALESCE(app.active_flag, 0) AS active_flag,
          COALESCE(app.repaid_percentage, 1) AS repaid_percentage,
          app.latest_application_date,
          app.latest_dispersal_date,
          app.latest_scheduled_cleared_date,
          COALESCE(app.latest_completed_step, 'N/A') AS latest_completed_step,
          app.latest_completed_step_date,
          COALESCE(app.latest_last_status, 'N/A') AS latest_last_status,
          app.latest_last_status_date, 
          COALESCE(app.latest_application_status, 'N/A') AS latest_application_status,
          COALESCE(app.latest_status, 'N/A') AS latest_status,
          COALESCE(app.ever_red_risk_level, 0) AS ever_red_risk_level,
          COALESCE(app.latest_risk_level, 'N/A') AS latest_risk_level,
          COALESCE(app.ever_red_finv_risk_level, 0) AS ever_red_finv_risk_level,
          COALESCE(app.latest_finv_risk_level, 'N/A') AS latest_finv_risk_level,
          COALESCE(app.pre_funded_loans, 0) AS pre_funded_loans,
          COALESCE(app.pre_funded_amount, 0) AS pre_funded_amount,
          COALESCE(app.pre_max_dpd_days_ever, 0) AS pre_max_dpd_days_ever,
          COALESCE(app.current_dpd, 0) AS current_dpd,
          COALESCE(app.pre_funded_loans_180, 0) AS pre_funded_loans_180
     FROM 
          (SELECT
               id AS user_id,
               is_blacklisted, 
               do_not_market, 
               is_comms_unsubscribed, 
               invalid_email,
               CASE WHEN mobile_verified_at IS NOT NULL THEN 1 ELSE 0 END AS mobile_verified, 
               CASE WHEN email_verified_at IS NOT NULL THEN 1 ELSE 0 END AS email_verified, 
                YEAR(to_date('${yyyy-mm-dd}')) - YEAR(TO_DATE(birthday, 'yyyy-MM-dd')) 
                  - (CASE WHEN MONTH(to_date('${yyyy-mm-dd}')) < MONTH(TO_DATE(birthday, 'yyyy-MM-dd')) THEN 1 
                        WHEN MONTH(to_date('${yyyy-mm-dd}')) = MONTH(TO_DATE(birthday, 'yyyy-MM-dd')) 
                            AND DAY(to_date('${yyyy-mm-dd}')) < DAY(TO_DATE(birthday, 'yyyy-MM-dd')) THEN 1 
                        ELSE 0 
                    END) AS precise_age
          FROM ods.fundo_v2_users_metadata_view) u
     LEFT JOIN 
          (SELECT user_id, 
               MAX(reapplication_activation_date) AS reapplication_activation_date,
               MAX(hardship_status) AS hardship_status
          FROM ods.aus_fundo_loans_loan_applications
          GROUP BY 1) la
     ON u.user_id=la.user_id
     LEFT JOIN
          (SELECT user_id,
               MAX(CASE WHEN sep_no_desc = 1 THEN application_date END) AS latest_application_date,
               MAX(CASE WHEN sep_no_desc = 1 THEN application_status END) AS latest_application_status,
               MAX(CASE WHEN sep_no_desc = 1 THEN status END) AS latest_status,
               MAX(dispersal_date) AS latest_dispersal_date,
               MAX(scheduled_cleared_date) AS latest_scheduled_cleared_date,
               MAX(CASE WHEN sep_no_desc = 1 THEN completed_step END) AS latest_completed_step,
               MAX(CASE WHEN sep_no_desc = 1 THEN completed_step_date END) AS latest_completed_step_date,
               MAX(CASE WHEN sep_no_desc = 1 THEN last_status END) AS latest_last_status,
               MAX(CASE WHEN sep_no_desc = 1 THEN last_status_date END) AS latest_last_status_date,
               MAX(CASE WHEN sep_no_desc = 1 THEN risk_level END) AS latest_risk_level,
               MAX(CASE WHEN risk_level = '03.RED' THEN 1 ELSE 0 END) AS ever_red_risk_level,
               MAX(CASE WHEN sep_no_desc = 1 THEN finv_color_code END) AS latest_finv_risk_level,
               MAX(CASE WHEN application_status NOT IN ('0.Incomplete', '1.In Progress') AND finv_color_code = '03.RED' THEN 1 ELSE 0 END) AS ever_red_finv_risk_level,
               MAX(CASE WHEN application_status IN ('1.In Progress') THEN 1 ELSE 0 END) AS in_complete_process_flag,
               MAX(CASE WHEN application_status IN ('1.In Progress', '2.0.Submitted','2.2.Assessment Submitted','3.2.Conversion Submitted') THEN 1 ELSE 0 END) AS in_process_flag,
               MAX(CASE WHEN status = 'Active_Account' THEN 1 ELSE 0 END) AS active_flag,
               MIN(CASE WHEN status = 'Active_Account' THEN repaid_percentage ELSE 1 END) AS repaid_percentage,
               COUNT(CASE WHEN dispersal_date <= to_date('${yyyy-mm-dd}') AND application_status = '4.Funded' THEN application_id END) AS pre_funded_loans,
               SUM(CASE WHEN dispersal_date <= to_date('${yyyy-mm-dd}') AND application_status = '4.Funded' THEN total_amount ELSE 0 END) AS pre_funded_amount,
               MAX(CASE WHEN dispersal_date <= to_date('${yyyy-mm-dd}') AND application_status = '4.Funded' THEN dpd_days_ever ELSE 0 END) AS pre_max_dpd_days_ever,
               MAX(CASE WHEN dispersal_date <= to_date('${yyyy-mm-dd}') AND application_status = '4.Funded' AND dpd_days>0 THEN 1 ELSE 0 END) AS current_dpd,
               COUNT(CASE WHEN dispersal_date > DATE_SUB(to_date('${yyyy-mm-dd}'), 180) AND dispersal_date <= to_date('${yyyy-mm-dd}') AND application_status = '4.Funded' THEN application_id END) AS pre_funded_loans_180
          FROM application_history
          GROUP BY 1) app
     ON u.user_id=app.user_id
)
SELECT
     user_id,
     CASE WHEN (pre_funded_loans>=4 OR (pre_funded_loans>=2 AND pre_funded_amount/pre_funded_loans > 1000))
               AND pre_funded_loans_180>=1 
               AND (pre_max_dpd_days_ever IS NULL OR pre_max_dpd_days_ever<=30)
               THEN 'Group 1 High-value'
          WHEN (pre_funded_loans=1 OR (pre_funded_loans IN (2,3) AND pre_funded_amount/pre_funded_loans <= 1000))
               AND pre_funded_loans_180>=1 
               AND (pre_max_dpd_days_ever IS NULL OR pre_max_dpd_days_ever<=30)
               THEN 'Group 2 Potential Growth' 
          WHEN pre_funded_loans>=1
               AND (pre_funded_loans_180=0 OR pre_funded_loans_180 IS NULL)
               AND (pre_max_dpd_days_ever IS NULL OR pre_max_dpd_days_ever<=30)
               THEN 'Group 3 Inactive' 
          WHEN pre_funded_loans>=1
               AND pre_max_dpd_days_ever>30
               THEN 'Group 4 Past Due 30+' 
          WHEN (pre_funded_loans=0 OR pre_funded_loans IS NULL)
               AND LEFT(latest_application_status,1) IN ('3', '4')
               THEN 'Group 5-1 No Dispersal & Approved'
          WHEN (pre_funded_loans=0 OR pre_funded_loans IS NULL)
               AND LEFT(latest_application_status,1) IN ('2')
               THEN 'Group 5-2 No Dispersal & Completed'
          WHEN (pre_funded_loans=0 OR pre_funded_loans IS NULL)
               AND (latest_application_status IN ('0.Incomplete', '1.In Progress')
                    OR latest_application_status = 'N/A'
                    OR latest_application_status IS NULL)
               THEN 'Group 5-3 No Dispersal & Incompleted'
          END AS segmentation,
     pre_funded_loans,
     pre_funded_amount,
     pre_max_dpd_days_ever,
     pre_funded_loans_180,
     is_blacklisted, 
     hardship_status,
     current_dpd,
     probation_period_flag,
     in_complete_process_flag,
     in_process_flag,
     active_flag,
     latest_completed_step,
     latest_application_status,
     latest_status,
     latest_last_status,
     ever_red_risk_level,
     latest_risk_level,
     ever_red_finv_risk_level,
     latest_finv_risk_level,
     DATEDIFF('${yyyy-mm-dd}', latest_application_date) AS latest_application_interval,
     DATEDIFF('${yyyy-mm-dd}', latest_dispersal_date) AS latest_dispersal_interval,
     DATEDIFF('${yyyy-mm-dd}', latest_scheduled_cleared_date) AS latest_scheduled_cleared_interval,
     DATEDIFF('${yyyy-mm-dd}', latest_completed_step_date) AS latest_completed_step_interval,
     DATEDIFF('${yyyy-mm-dd}', latest_last_status_date) AS latest_last_status_interval,
     do_not_market, 
     is_comms_unsubscribed, 
     invalid_email,
     mobile_verified, 
     email_verified,
     age,
     repaid_percentage,
     to_date('${yyyy-mm-dd}') AS observe_date
FROM user_history
;