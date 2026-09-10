DROP TABLE IF EXISTS ba.iterable_targeting_history;
CREATE TABLE IF NOT EXISTS ba.iterable_targeting_history AS
WITH campaign AS (
    SELECT *,
        EXTRACT(HOUR FROM launch_time) AS launch_hour,
        DATE(launch_time) AS launch_date,
        date_format(launch_time, 'EEEE') AS launch_dow,
        CASE WHEN MONTH(DATE(launch_time))=12 AND WEEKOFYEAR(DATE(launch_time)) = 1 
                  THEN CONCAT(CAST(YEAR(DATE(launch_time)) + 1 AS STRING), 'W', LPAD(CAST(WEEKOFYEAR(DATE(launch_time)) AS STRING), 2, '0')) 
            WHEN MONTH(DATE(launch_time))=1 AND WEEKOFYEAR(DATE(launch_time)) IN (52,53) 
                  THEN CONCAT(CAST(YEAR(DATE(launch_time)) - 1 AS STRING), 'W', LPAD(CAST(WEEKOFYEAR(DATE(launch_time)) AS STRING), 2, '0')) 
            ELSE CONCAT(CAST(YEAR(DATE(launch_time)) AS STRING), 'W', LPAD(CAST(WEEKOFYEAR(DATE(launch_time)) AS STRING), 2, '0')) 
            END AS launch_week,
        date_format(TIMESTAMP(launch_time),'yyyy-MM') AS launch_month
    FROM
        (SELECT 
            CAST(campaign_id AS BIGINT) AS campaign_id, 
            campaign_name, campaign_state, type, message_medium,
            CASE WHEN campaign_name LIKE '%Coupon%' THEN 'Coupon'
                WHEN campaign_name LIKE '%AllCustomers%' THEN 'All Customers'
                WHEN campaign_name LIKE '%AbandonedApp%' THEN 'Abandoned App'
                WHEN campaign_name LIKE '%Applied%' THEN 'Applied'
                WHEN campaign_name LIKE '%Cancelled%' THEN 'Cancelled'
                WHEN campaign_name LIKE '%Closed%' THEN 'Closed'
                WHEN campaign_name LIKE '%Declined%' THEN 'Declined'
                WHEN campaign_name LIKE '%Trashed%' THEN 'Trashed'
                WHEN campaign_name LIKE '%DTC%' THEN 'DTC'
                WHEN campaign_name LIKE '%Gmail%' THEN 'Gmail'
                WHEN campaign_name LIKE '%OHL%' THEN 'OHL'
                END AS audience,
            CASE WHEN message_medium='Email' THEN
                CASE WHEN campaign_name LIKE '%Gmail%' THEN 'Gmail'
                    WHEN campaign_name LIKE '%OHL%' THEN 'OHL'
                    END
                END AS email_type,
            start_time,
            CASE WHEN TIMESTAMP(LEFT(start_time,19))>='2025-10-05 10:00:00' AND TIMESTAMP(LEFT(start_time,19))<='2026-04-05 11:00:00' 
                      THEN TIMESTAMP(LEFT(start_time,19)) - INTERVAL 7 HOURS
                ELSE TIMESTAMP(LEFT(start_time,19)) - INTERVAL 8 HOURS
                END AS launch_time,
            CAST(send_size AS INT) AS send_size
        FROM ods.dim_mkt_iterable_campaign_config_dtl
        WHERE account_id=24894
        AND send_size IS NOT NULL
        )
    WHERE DATE(launch_time)>='2025-08-01'
    ORDER BY campaign_name, launch_date
),
sms_template AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(template_id AS BIGINT) AS template_id, 
        message AS sms_template,
        NULL AS email_template_subject,
        NULL AS email_template_preheader
    FROM edw.dwd_mkt_iterable_sms_template_report_data
    WHERE account_id=24894
),
email_template AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(template_id AS BIGINT) AS template_id, 
        NULL AS sms_template,
        subject AS email_template_subject,
        preheader_text AS email_template_preheader
    FROM edw.dwd_mkt_iterable_email_template_report_data
    WHERE account_id=24894
),
template AS (
    SELECT *
    FROM sms_template
    UNION ALL 
    SELECT *
    FROM email_template
),
sms_send AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(user_id AS BIGINT) AS user_id, 
        from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney') AS send_time,
        DATE(from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney')) AS send_date,
        rendered_sms_message AS rendered_sms_message,
        sms_send_count AS sms_send_count
    FROM ods.dwd_mkt_iterable_sms_send_dtl
    WHERE account_id=24894
),
email_send AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(user_id AS BIGINT) AS user_id, 
        from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney') AS send_time,
        DATE(from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney')) AS send_date,
        NULL AS rendered_sms_message,
        NULL AS sms_send_count
    FROM ods.dwd_mkt_iterable_email_send_dtl
    WHERE account_id=24894
),
send AS (
    SELECT *
    FROM sms_send
    UNION ALL 
    SELECT *
    FROM email_send
),
sms_bounce AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(user_id AS BIGINT) AS user_id, 
        from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney') AS bounce_time,
        DATE(from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney')) AS bounce_date
    FROM ods.dwd_mkt_iterable_sms_bounce_dtl
    WHERE account_id=24894
),
email_bounce AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(user_id AS BIGINT) AS user_id, 
        from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney') AS bounce_time,
        DATE(from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney')) AS bounce_date
    FROM ods.dwd_mkt_iterable_email_bounce_dtl
    WHERE account_id=24894
),
bounce AS (
    SELECT *
    FROM sms_bounce
    UNION ALL 
    SELECT *
    FROM email_bounce
),
sms_click AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(user_id AS BIGINT) AS user_id, 
        from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney') AS click_time,
        DATE(from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney')) AS click_date
    FROM ods.dwd_mkt_iterable_sms_click_dtl
    WHERE account_id=24894
),
email_click AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(user_id AS BIGINT) AS user_id, 
        from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney') AS click_time,
        DATE(from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney')) AS click_date
    FROM ods.dwd_mkt_iterable_email_click_dtl
    WHERE account_id=24894
),
click AS (
    SELECT *
    FROM sms_click
    UNION ALL 
    SELECT *
    FROM email_click
),
email_open AS (
    SELECT
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(user_id AS BIGINT) AS user_id, 
        from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney') AS open_time,
        DATE(from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney')) AS open_date
    FROM ods.dwd_mkt_iterable_email_open_dtl
    WHERE account_id=24894
    AND NOT user_id rlike '[a-zA-Z]'
),
email_unsubscribe AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(user_id AS BIGINT) AS user_id, 
        from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney') AS unsubscribe_time,
        DATE(from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney')) AS unsubscribe_date
    FROM ods.dwd_mkt_iterable_email_unsubscribe_dtl
    WHERE account_id=24894
),
email_complaint AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(user_id AS BIGINT) AS user_id, 
        from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney') AS complaint_time,
        DATE(from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney')) AS complaint_date
    FROM ods.dwd_mkt_iterable_email_complaint_dtl
    WHERE account_id=24894
),
previous_sms_send AS (
    SELECT user_id, campaign_id, launch_date, 
        COUNT(DISTINCT CASE WHEN send_date<launch_date THEN previous_campaign_id END) AS previous_sms_send_cnt,
        COUNT(DISTINCT CASE WHEN send_date<launch_date AND send_date>=DATE_SUB(launch_date, 14) THEN previous_campaign_id END) AS previous_sms_send_cnt_14,
        COUNT(DISTINCT CASE WHEN send_date<launch_date AND send_date>=DATE_SUB(launch_date, 30) THEN previous_campaign_id END) AS previous_sms_send_cnt_30,
        COUNT(DISTINCT CASE WHEN send_date<launch_date AND send_date>=DATE_SUB(launch_date, 90) THEN previous_campaign_id END) AS previous_sms_send_cnt_90,
        COUNT(DISTINCT CASE WHEN send_date<launch_date AND send_date>=DATE_SUB(launch_date, 180) THEN previous_campaign_id END) AS previous_sms_send_cnt_180,
        MIN(send_date) AS previous_first_sms_send_date,
        MAX(send_date) AS previous_last_sms_send_date
    FROM
        (SELECT a.user_id, a.campaign_id, c.launch_date, fa.send_date, fa.campaign_id AS previous_campaign_id
        FROM send a
        LEFT JOIN campaign c
        ON a.campaign_id = c.campaign_id
        LEFT JOIN sms_send fa 
        ON a.user_id = fa.user_id
        AND c.launch_date>fa.send_date) a 
    GROUP BY 1,2,3
),
previous_email_send AS (
    SELECT user_id, campaign_id, launch_date, 
        COUNT(DISTINCT CASE WHEN send_date<launch_date THEN previous_campaign_id END) AS previous_email_send_cnt,
        COUNT(DISTINCT CASE WHEN send_date<launch_date AND send_date>=DATE_SUB(launch_date, 14) THEN previous_campaign_id END) AS previous_email_send_cnt_14,
        COUNT(DISTINCT CASE WHEN send_date<launch_date AND send_date>=DATE_SUB(launch_date, 30) THEN previous_campaign_id END) AS previous_email_send_cnt_30,
        COUNT(DISTINCT CASE WHEN send_date<launch_date AND send_date>=DATE_SUB(launch_date, 90) THEN previous_campaign_id END) AS previous_email_send_cnt_90,
        COUNT(DISTINCT CASE WHEN send_date<launch_date AND send_date>=DATE_SUB(launch_date, 180) THEN previous_campaign_id END) AS previous_email_send_cnt_180,
        MIN(send_date) AS previous_first_email_send_date,
        MAX(send_date) AS previous_last_email_send_date
    FROM
        (SELECT a.user_id, a.campaign_id, c.launch_date, fa.send_date, fa.campaign_id AS previous_campaign_id
        FROM send a
        LEFT JOIN campaign c
        ON a.campaign_id = c.campaign_id
        LEFT JOIN email_send fa 
        ON a.user_id = fa.user_id
        AND c.launch_date>fa.send_date) a 
    GROUP BY 1,2,3
),
previous_sms_click AS (
    SELECT user_id, campaign_id, launch_date, 
        COUNT(DISTINCT CASE WHEN click_date<launch_date THEN previous_campaign_id END) AS previous_sms_click_cnt,
        COUNT(DISTINCT CASE WHEN click_date<launch_date AND click_date>=DATE_SUB(launch_date, 14) THEN previous_campaign_id END) AS previous_sms_click_cnt_14,
        COUNT(DISTINCT CASE WHEN click_date<launch_date AND click_date>=DATE_SUB(launch_date, 30) THEN previous_campaign_id END) AS previous_sms_click_cnt_30,
        COUNT(DISTINCT CASE WHEN click_date<launch_date AND click_date>=DATE_SUB(launch_date, 90) THEN previous_campaign_id END) AS previous_sms_click_cnt_90,
        COUNT(DISTINCT CASE WHEN click_date<launch_date AND click_date>=DATE_SUB(launch_date, 180) THEN previous_campaign_id END) AS previous_sms_click_cnt_180,
        MIN(click_date) AS previous_first_sms_click_date,
        MAX(click_date) AS previous_last_sms_click_date
    FROM
        (SELECT a.user_id, a.campaign_id, c.launch_date, fa.click_date, fa.campaign_id AS previous_campaign_id
        FROM send a
        LEFT JOIN campaign c
        ON a.campaign_id = c.campaign_id
        LEFT JOIN sms_click fa 
        ON a.user_id = fa.user_id
        AND c.launch_date>fa.click_date) a 
    GROUP BY 1,2,3
),
previous_email_click AS (
    SELECT user_id, campaign_id, launch_date, 
        COUNT(DISTINCT CASE WHEN click_date<launch_date THEN previous_campaign_id END) AS previous_email_click_cnt,
        COUNT(DISTINCT CASE WHEN click_date<launch_date AND click_date>=DATE_SUB(launch_date, 14) THEN previous_campaign_id END) AS previous_email_click_cnt_14,
        COUNT(DISTINCT CASE WHEN click_date<launch_date AND click_date>=DATE_SUB(launch_date, 30) THEN previous_campaign_id END) AS previous_email_click_cnt_30,
        COUNT(DISTINCT CASE WHEN click_date<launch_date AND click_date>=DATE_SUB(launch_date, 90) THEN previous_campaign_id END) AS previous_email_click_cnt_90,
        COUNT(DISTINCT CASE WHEN click_date<launch_date AND click_date>=DATE_SUB(launch_date, 180) THEN previous_campaign_id END) AS previous_email_click_cnt_180,
        MIN(click_date) AS previous_first_email_click_date,
        MAX(click_date) AS previous_last_email_click_date
    FROM
        (SELECT a.user_id, a.campaign_id, c.launch_date, fa.click_date, fa.campaign_id AS previous_campaign_id
        FROM send a
        LEFT JOIN campaign c
        ON a.campaign_id = c.campaign_id
        LEFT JOIN email_click fa 
        ON a.user_id = fa.user_id
        AND c.launch_date>fa.click_date) a 
    GROUP BY 1,2,3
),
previous_email_open AS (
    SELECT user_id, campaign_id, launch_date, 
        COUNT(DISTINCT CASE WHEN open_date<launch_date THEN previous_campaign_id END) AS previous_email_open_cnt,
        COUNT(DISTINCT CASE WHEN open_date<launch_date AND open_date>=DATE_SUB(launch_date, 14) THEN previous_campaign_id END) AS previous_email_open_cnt_14,
        COUNT(DISTINCT CASE WHEN open_date<launch_date AND open_date>=DATE_SUB(launch_date, 30) THEN previous_campaign_id END) AS previous_email_open_cnt_30,
        COUNT(DISTINCT CASE WHEN open_date<launch_date AND open_date>=DATE_SUB(launch_date, 90) THEN previous_campaign_id END) AS previous_email_open_cnt_90,
        COUNT(DISTINCT CASE WHEN open_date<launch_date AND open_date>=DATE_SUB(launch_date, 180) THEN previous_campaign_id END) AS previous_email_open_cnt_180,
        MIN(open_date) AS previous_first_email_open_date,
        MAX(open_date) AS previous_last_email_open_date
    FROM
        (SELECT a.user_id, a.campaign_id, c.launch_date, fa.open_date, fa.campaign_id AS previous_campaign_id
        FROM send a
        LEFT JOIN campaign c
        ON a.campaign_id = c.campaign_id
        LEFT JOIN email_open fa 
        ON a.user_id = fa.user_id
        AND c.launch_date>fa.open_date) a 
    GROUP BY 1,2,3
),
previous_application AS (
    SELECT user_id, campaign_id, launch_date, DATE(application_date) AS previous_application_date, application_status AS previous_application_status, assessment_status AS previous_assessment_status
    FROM
        (SELECT a.user_id, a.campaign_id, c.launch_date, fa.application_date, fa.application_status, fa.assessment_status,
             ROW_NUMBER() OVER(PARTITION BY a.user_id, a.campaign_id ORDER BY fa.application_date DESC) AS seq_no
        FROM send a
        LEFT JOIN campaign c
        ON a.campaign_id = c.campaign_id
        LEFT JOIN ba.application_rawdata fa 
        ON a.user_id = fa.user_id
        AND c.launch_date>DATE(fa.application_date)) a 
    WHERE seq_no=1
),
previous_dispersal AS (
    SELECT user_id, campaign_id, launch_date, DATE(dispersal_date) AS previous_dispersal_date
    FROM
        (SELECT a.user_id, a.campaign_id, c.launch_date, fa.dispersal_date,
             ROW_NUMBER() OVER(PARTITION BY a.user_id, a.campaign_id ORDER BY fa.dispersal_date DESC) AS seq_no
        FROM send a
        LEFT JOIN campaign c
        ON a.campaign_id = c.campaign_id
        LEFT JOIN ba.application_rawdata fa 
        ON a.user_id = fa.user_id
        AND c.launch_date>DATE(fa.dispersal_date)) a 
    WHERE seq_no=1
),
previous_settled AS (
    SELECT user_id, campaign_id, launch_date, DATE(scheduled_cleared_date) AS previous_settled_date
    FROM
        (SELECT a.user_id, a.campaign_id, c.launch_date, fa.scheduled_cleared_date,
             ROW_NUMBER() OVER(PARTITION BY a.user_id, a.campaign_id ORDER BY fa.scheduled_cleared_date DESC) AS seq_no
        FROM send a
        LEFT JOIN campaign c
        ON a.campaign_id = c.campaign_id
        LEFT JOIN ba.application_rawdata fa 
        ON a.user_id = fa.user_id
        AND c.launch_date>DATE(fa.scheduled_cleared_date)) a 
    WHERE seq_no=1
),
age AS (
    SELECT 
        a.user_id, a.campaign_id, c.launch_date, 
        YEAR(c.launch_date) - YEAR(TO_DATE(birthday, 'yyyy-MM-dd')) 
          - (CASE WHEN MONTH(c.launch_date) < MONTH(TO_DATE(birthday, 'yyyy-MM-dd')) THEN 1 
                WHEN MONTH(c.launch_date) = MONTH(TO_DATE(birthday, 'yyyy-MM-dd')) 
                    AND DAY(c.launch_date) < DAY(TO_DATE(birthday, 'yyyy-MM-dd')) THEN 1 
                ELSE 0 
            END) AS precise_age
    FROM send a
    LEFT JOIN campaign c
    ON a.campaign_id = c.campaign_id
    LEFT JOIN ods.fundo_v2_users_metadata_view u
    ON a.user_id=TRY_CAST(id AS BIGINT)
)

SELECT 
    a.campaign_id,
    a.campaign_name,
    a.message_medium,
    a.audience,
    a.email_type,
    a.launch_time,
    a.launch_hour,
    a.launch_date,
    a.launch_dow,
    a.launch_week,
    a.launch_month,
    a.send_size,
    template.template_id, 
    template.sms_template, 
    template.email_template_subject, 
    template.email_template_preheader,
    send.user_id,
    send.rendered_sms_message, 
    send.sms_send_count,
    CASE WHEN fa.first_application_date IS NOT NULL AND DATE(fa.first_application_date)<a.launch_date THEN 'Returning' ELSE 'New' END AS ls_application_tag,
    CASE WHEN fa.first_dispersal_date IS NOT NULL AND DATE(fa.first_dispersal_date)<a.launch_date THEN 'Existing' ELSE 'New' END AS ls_user_tag,
    previous_sms_send_cnt,
    previous_sms_send_cnt_14,
    previous_sms_send_cnt_30,
    previous_sms_send_cnt_90,
    previous_sms_send_cnt_180,
    previous_first_sms_send_date,
    previous_last_sms_send_date,
    previous_email_send_cnt,
    previous_email_send_cnt_14,
    previous_email_send_cnt_30,
    previous_email_send_cnt_90,
    previous_email_send_cnt_180,
    previous_first_email_send_date,
    previous_last_email_send_date,
    previous_sms_click_cnt,
    previous_sms_click_cnt_14,
    previous_sms_click_cnt_30,
    previous_sms_click_cnt_90,
    previous_sms_click_cnt_180,
    previous_first_sms_click_date,
    previous_last_sms_click_date,
    previous_email_click_cnt,
    previous_email_click_cnt_14,
    previous_email_click_cnt_30,
    previous_email_click_cnt_90,
    previous_email_click_cnt_180,
    previous_first_email_click_date,
    previous_last_email_click_date,
    previous_email_open_cnt,
    previous_email_open_cnt_14,
    previous_email_open_cnt_30,
    previous_email_open_cnt_90,
    previous_email_open_cnt_180,
    previous_first_email_open_date,
    previous_last_email_open_date,
    previous_application_date,
    previous_application_status,
    previous_assessment_status,
    previous_dispersal_date,
    previous_settled_date,
    DATEDIFF(a.launch_date, previous_first_sms_send_date) AS previous_first_sms_send_interval,
    DATEDIFF(a.launch_date, previous_last_sms_send_date) AS previous_last_sms_send_interval,
    DATEDIFF(a.launch_date, previous_first_email_send_date) AS previous_first_email_send_interval,
    DATEDIFF(a.launch_date, previous_last_email_send_date) AS previous_last_email_send_interval,
    DATEDIFF(a.launch_date, previous_first_sms_click_date) AS previous_first_sms_click_interval,
    DATEDIFF(a.launch_date, previous_last_sms_click_date) AS previous_last_sms_click_interval,
    DATEDIFF(a.launch_date, previous_first_email_click_date) AS previous_first_email_click_interval,
    DATEDIFF(a.launch_date, previous_last_email_click_date) AS previous_last_email_click_interval,
    DATEDIFF(a.launch_date, previous_first_email_open_date) AS previous_first_email_open_interval,
    DATEDIFF(a.launch_date, previous_last_email_open_date) AS previous_last_email_open_interval,
    DATEDIFF(a.launch_date, previous_application_date) AS previous_application_interval,
    DATEDIFF(a.launch_date, previous_dispersal_date) AS previous_dispersal_interval,
    DATEDIFF(a.launch_date, previous_settled_date) AS previous_settlement_interval,
    age.precise_age AS age,
    CASE WHEN bounce_flag=1 THEN 1 ELSE 0 END AS bounce_flag,
    CASE WHEN open_flag=1 THEN 1 ELSE 0 END AS open_flag,
    CASE WHEN click_flag=1 THEN 1 ELSE 0 END AS click_flag,
    CASE WHEN unsubscribe_flag=1 THEN 1 ELSE 0 END AS unsubscribe_flag,
    CASE WHEN complaint_flag=1 THEN 1 ELSE 0 END AS complaint_flag
FROM campaign a
LEFT JOIN 
    (SELECT DISTINCT campaign_id, template_id, sms_template, email_template_subject, email_template_preheader FROM template) template
ON a.campaign_id=template.campaign_id
LEFT JOIN 
    (SELECT DISTINCT campaign_id, user_id, rendered_sms_message, sms_send_count FROM send) send
ON a.campaign_id=send.campaign_id
LEFT JOIN 
    (SELECT DISTINCT campaign_id, user_id, 1 AS bounce_flag FROM bounce) bounce
ON a.campaign_id=bounce.campaign_id
AND send.user_id=bounce.user_id
LEFT JOIN 
    (SELECT DISTINCT campaign_id, user_id, 1 AS click_flag FROM click) click
ON a.campaign_id=click.campaign_id
AND send.user_id=click.user_id
LEFT JOIN 
    (SELECT DISTINCT campaign_id, user_id, 1 AS open_flag FROM email_open) open
ON a.campaign_id=open.campaign_id
AND send.user_id=open.user_id
LEFT JOIN 
    (SELECT DISTINCT campaign_id, user_id, 1 AS unsubscribe_flag FROM email_unsubscribe) unsubscribe
ON a.campaign_id=unsubscribe.campaign_id
AND send.user_id=unsubscribe.user_id
LEFT JOIN 
    (SELECT DISTINCT campaign_id, user_id, 1 AS complaint_flag FROM email_complaint) complaint
ON a.campaign_id=complaint.campaign_id
AND send.user_id=complaint.user_id
LEFT JOIN previous_sms_send AS pss
ON a.campaign_id=pss.campaign_id
AND send.user_id=pss.user_id
LEFT JOIN previous_email_send AS pes
ON a.campaign_id=pes.campaign_id
AND send.user_id=pes.user_id
LEFT JOIN previous_sms_click AS psc
ON a.campaign_id=psc.campaign_id
AND send.user_id=psc.user_id
LEFT JOIN previous_email_click AS pec
ON a.campaign_id=pec.campaign_id
AND send.user_id=pec.user_id
LEFT JOIN previous_email_open AS peo
ON a.campaign_id=peo.campaign_id
AND send.user_id=peo.user_id
LEFT JOIN previous_application AS pa
ON a.campaign_id=pa.campaign_id
AND send.user_id=pa.user_id
LEFT JOIN previous_dispersal AS pd
ON a.campaign_id=pd.campaign_id
AND send.user_id=pd.user_id
LEFT JOIN previous_settled AS ps
ON a.campaign_id=ps.campaign_id
AND send.user_id=ps.user_id
LEFT JOIN age AS age
ON a.campaign_id=age.campaign_id
AND send.user_id=age.user_id
LEFT JOIN 
    (SELECT
         user_id,
         MIN(application_date) as first_application_date,
         MIN(dispersal_date) as first_dispersal_date
    FROM ba.application_rawdata
    GROUP BY user_id
    ) fa 
ON send.user_id = fa.user_id
ORDER BY a.launch_date, a.campaign_name, send.user_id
;