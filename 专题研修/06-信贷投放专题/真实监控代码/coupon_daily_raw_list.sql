-- DROP TABLE IF EXISTS ba.coupon_daily_raw_list;
-- CREATE TABLE ba.coupon_daily_raw_list (
--     user_id BIGINT,
--     segmentation STRING,
--     latest_application_interval STRING,
--     latest_scheduled_cleared_interval STRING,
--     random_num DOUBLE,
--     layer_threshold DOUBLE,
--     test_group STRING
-- )
-- PARTITIONED BY (observe_date DATE)
-- ;



INSERT OVERWRITE TABLE ba.coupon_daily_raw_list PARTITION (observe_date)

WITH user_with_rand AS (
    SELECT user_id,
        segmentation,
        CASE WHEN latest_application_interval IS NULL OR latest_application_interval < 0 THEN '99.N/A'
            WHEN latest_application_interval >= 0 AND latest_application_interval <= 30 THEN '01.0-30 Days'
            WHEN latest_application_interval > 30 AND latest_application_interval <= 60 THEN '02.31-60 Days'
            WHEN latest_application_interval > 60 AND latest_application_interval <= 90 THEN '03.61-90 Days'
            WHEN latest_application_interval > 90 AND latest_application_interval <= 120 THEN '04.91-120 Days'
            WHEN latest_application_interval > 120 AND latest_application_interval <= 150 THEN '05.121-150 Days'
            WHEN latest_application_interval > 150 AND latest_application_interval <= 180 THEN '06.151-180 Days'
            WHEN latest_application_interval > 180 AND latest_application_interval <= 210 THEN '07.181-210 Days'
            WHEN latest_application_interval > 210 AND latest_application_interval <= 240 THEN '08.211-240 Days'
            WHEN latest_application_interval > 240 AND latest_application_interval <= 270 THEN '09.241-270 Days'
            WHEN latest_application_interval > 270 THEN '10.271+ Days'
        END AS latest_application_interval,
        CASE WHEN latest_scheduled_cleared_interval IS NULL OR latest_scheduled_cleared_interval < 0 THEN '99.N/A'
            WHEN latest_scheduled_cleared_interval >= 0 AND latest_scheduled_cleared_interval <= 30 THEN '01.0-30 Days'
            WHEN latest_scheduled_cleared_interval > 30 AND latest_scheduled_cleared_interval <= 60 THEN '02.31-60 Days'
            WHEN latest_scheduled_cleared_interval > 60 AND latest_scheduled_cleared_interval <= 90 THEN '03.61-90 Days'
            WHEN latest_scheduled_cleared_interval > 90 AND latest_scheduled_cleared_interval <= 120 THEN '04.91-120 Days'
            WHEN latest_scheduled_cleared_interval > 120 AND latest_scheduled_cleared_interval <= 150 THEN '05.121-150 Days'
            WHEN latest_scheduled_cleared_interval > 150 AND latest_scheduled_cleared_interval <= 180 THEN '06.151-180 Days'
            WHEN latest_scheduled_cleared_interval > 180 AND latest_scheduled_cleared_interval <= 210 THEN '07.181-210 Days'
            WHEN latest_scheduled_cleared_interval > 210 AND latest_scheduled_cleared_interval <= 240 THEN '08.211-240 Days'
            WHEN latest_scheduled_cleared_interval > 240 AND latest_scheduled_cleared_interval <= 270 THEN '09.241-270 Days'
            WHEN latest_scheduled_cleared_interval > 270 THEN '10.271+ Days'
        END AS latest_scheduled_cleared_interval,
        rand(20260210) AS random_num
    FROM ba.coupon_customer_status_rawdata
    WHERE observe_date = to_date('${yyyy-mm-dd}')
    AND segmentation IN ('Group 1 High-value','Group 2 Potential Growth','Group 3 Inactive','Group 4 Past Due 30+')
    AND is_blacklisted = 0
    AND hardship_status = 0
    AND current_dpd = 0
    AND probation_period_flag = 0
    AND in_process_flag = 0
    AND active_flag = 0
    AND latest_finv_risk_level <> '03.RED'
    AND latest_application_interval > 90 
    AND latest_scheduled_cleared_interval > 90
    AND do_not_market = 0
    AND is_comms_unsubscribed = 0
    AND user_id NOT IN 
        (SELECT DISTINCT user_id 
        FROM ba.operation_global_control_list
        WHERE global_control_group='Global Control')
),

layer_percentile AS (
    SELECT 
        segmentation,
        latest_application_interval,
        latest_scheduled_cleared_interval,
        percentile_approx(random_num, 0.7, 10000) AS layer_threshold
    FROM user_with_rand
    GROUP BY 1,2,3
)

SELECT 
    u.user_id,
    u.segmentation,
    u.latest_application_interval,
    u.latest_scheduled_cleared_interval,
    u.random_num,
    l.layer_threshold,
    CASE 
        WHEN u.random_num < l.layer_threshold THEN 'A'
        ELSE 'B'
    END AS test_group,
     to_date('${yyyy-mm-dd}') AS observe_date 
FROM user_with_rand u
LEFT JOIN layer_percentile l 
ON u.segmentation = l.segmentation
AND u.latest_application_interval = l.latest_application_interval
AND u.latest_scheduled_cleared_interval = l.latest_scheduled_cleared_interval
;