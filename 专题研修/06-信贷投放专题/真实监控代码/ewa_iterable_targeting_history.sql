DROP TABLE IF EXISTS ba.ewa_iterable_targeting_history;
CREATE TABLE IF NOT EXISTS ba.ewa_iterable_targeting_history AS
WITH campaign AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        campaign_name, campaign_state, type, message_medium,
        CAST(send_size AS INT) AS send_size
    FROM ods.dim_mkt_iterable_campaign_config_dtl
    WHERE account_id=31467
    AND isactive=1
),
sms_template AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(template_id AS BIGINT) AS template_id, 
        CASE WHEN message_type_id IN (184218, 189861, 190756) THEN 'Transactional'
            WHEN message_type_id IN (184217, 185421) THEN 'Marketing'
            WHEN message_type_id IN (189860, 190755) THEN 'Collection'
            END AS message_type,
        message AS sms_template,
        NULL AS email_template_subject,
        NULL AS email_template_preheader
    FROM edw.dwd_mkt_iterable_sms_template_report_data
    WHERE account_id=31467
),
email_template AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(template_id AS BIGINT) AS template_id, 
        CASE WHEN message_type_id IN (184218, 189861, 190756) THEN 'Transactional'
            WHEN message_type_id IN (184217, 185421) THEN 'Marketing'
            WHEN message_type_id IN (189860, 190755) THEN 'Collection'
            END AS message_type,
        NULL AS sms_template,
        subject AS email_template_subject,
        preheader_text AS email_template_preheader
    FROM edw.dwd_mkt_iterable_email_template_report_data
    WHERE account_id=31467
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
    WHERE account_id=31467
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
    WHERE account_id=31467
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
    WHERE account_id=31467
),
email_bounce AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(user_id AS BIGINT) AS user_id, 
        from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney') AS bounce_time,
        DATE(from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney')) AS bounce_date
    FROM ods.dwd_mkt_iterable_email_bounce_dtl
    WHERE account_id=31467
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
    WHERE account_id=31467
),
email_click AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(user_id AS BIGINT) AS user_id, 
        from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney') AS click_time,
        DATE(from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney')) AS click_date
    FROM ods.dwd_mkt_iterable_email_click_dtl
    WHERE account_id=31467
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
    WHERE account_id=31467
    AND NOT user_id rlike '[a-zA-Z]'
),
email_unsubscribe AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(user_id AS BIGINT) AS user_id, 
        from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney') AS unsubscribe_time,
        DATE(from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney')) AS unsubscribe_date
    FROM ods.dwd_mkt_iterable_email_unsubscribe_dtl
    WHERE account_id=31467
),
email_complaint AS (
    SELECT 
        CAST(campaign_id AS BIGINT) AS campaign_id, 
        CAST(user_id AS BIGINT) AS user_id, 
        from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney') AS complaint_time,
        DATE(from_utc_timestamp(to_timestamp(LEFT(create_time,19)), 'Australia/Sydney')) AS complaint_date
    FROM ods.dwd_mkt_iterable_email_complaint_dtl
    WHERE account_id=31467
),
previous_sms_send AS (
    SELECT user_id, campaign_id, send_date, 
        COUNT(DISTINCT CASE WHEN previous_send_date<send_date THEN previous_campaign_id END) AS previous_sms_send_cnt,
        COUNT(DISTINCT CASE WHEN previous_send_date<send_date AND previous_send_date>=DATE_SUB(send_date, 14) THEN previous_campaign_id END) AS previous_sms_send_cnt_14,
        COUNT(DISTINCT CASE WHEN previous_send_date<send_date AND previous_send_date>=DATE_SUB(send_date, 30) THEN previous_campaign_id END) AS previous_sms_send_cnt_30,
        COUNT(DISTINCT CASE WHEN previous_send_date<send_date AND previous_send_date>=DATE_SUB(send_date, 90) THEN previous_campaign_id END) AS previous_sms_send_cnt_90,
        COUNT(DISTINCT CASE WHEN previous_send_date<send_date AND previous_send_date>=DATE_SUB(send_date, 180) THEN previous_campaign_id END) AS previous_sms_send_cnt_180,
        MIN(previous_send_date) AS previous_first_sms_send_date,
        MAX(previous_send_date) AS previous_last_sms_send_date
    FROM
        (SELECT a.user_id, a.campaign_id, a.send_date, fa.send_date AS previous_send_date, fa.campaign_id AS previous_campaign_id
        FROM send a
        LEFT JOIN sms_send fa 
        ON a.user_id = fa.user_id
        AND a.send_date>fa.send_date) a 
    GROUP BY 1,2,3
),
previous_email_send AS (
    SELECT user_id, campaign_id, send_date, 
        COUNT(DISTINCT CASE WHEN previous_send_date<send_date THEN previous_campaign_id END) AS previous_email_send_cnt,
        COUNT(DISTINCT CASE WHEN previous_send_date<send_date AND previous_send_date>=DATE_SUB(send_date, 14) THEN previous_campaign_id END) AS previous_email_send_cnt_14,
        COUNT(DISTINCT CASE WHEN previous_send_date<send_date AND previous_send_date>=DATE_SUB(send_date, 30) THEN previous_campaign_id END) AS previous_email_send_cnt_30,
        COUNT(DISTINCT CASE WHEN previous_send_date<send_date AND previous_send_date>=DATE_SUB(send_date, 90) THEN previous_campaign_id END) AS previous_email_send_cnt_90,
        COUNT(DISTINCT CASE WHEN previous_send_date<send_date AND previous_send_date>=DATE_SUB(send_date, 180) THEN previous_campaign_id END) AS previous_email_send_cnt_180,
        MIN(previous_send_date) AS previous_first_email_send_date,
        MAX(previous_send_date) AS previous_last_email_send_date
    FROM
        (SELECT a.user_id, a.campaign_id, a.send_date, fa.send_date AS previous_send_date, fa.campaign_id AS previous_campaign_id
        FROM send a
        LEFT JOIN email_send fa 
        ON a.user_id = fa.user_id
        AND a.send_date>fa.send_date) a 
    GROUP BY 1,2,3
),
previous_sms_click AS (
    SELECT user_id, campaign_id, send_date, 
        COUNT(DISTINCT CASE WHEN click_date<send_date THEN previous_campaign_id END) AS previous_sms_click_cnt,
        COUNT(DISTINCT CASE WHEN click_date<send_date AND click_date>=DATE_SUB(send_date, 14) THEN previous_campaign_id END) AS previous_sms_click_cnt_14,
        COUNT(DISTINCT CASE WHEN click_date<send_date AND click_date>=DATE_SUB(send_date, 30) THEN previous_campaign_id END) AS previous_sms_click_cnt_30,
        COUNT(DISTINCT CASE WHEN click_date<send_date AND click_date>=DATE_SUB(send_date, 90) THEN previous_campaign_id END) AS previous_sms_click_cnt_90,
        COUNT(DISTINCT CASE WHEN click_date<send_date AND click_date>=DATE_SUB(send_date, 180) THEN previous_campaign_id END) AS previous_sms_click_cnt_180,
        MIN(click_date) AS previous_first_sms_click_date,
        MAX(click_date) AS previous_last_sms_click_date
    FROM
        (SELECT a.user_id, a.campaign_id, a.send_date, fa.click_date, fa.campaign_id AS previous_campaign_id
        FROM send a
        LEFT JOIN sms_click fa 
        ON a.user_id = fa.user_id
        AND a.send_date>fa.click_date) a 
    GROUP BY 1,2,3
),
previous_email_click AS (
    SELECT user_id, campaign_id, send_date, 
        COUNT(DISTINCT CASE WHEN click_date<send_date THEN previous_campaign_id END) AS previous_email_click_cnt,
        COUNT(DISTINCT CASE WHEN click_date<send_date AND click_date>=DATE_SUB(send_date, 14) THEN previous_campaign_id END) AS previous_email_click_cnt_14,
        COUNT(DISTINCT CASE WHEN click_date<send_date AND click_date>=DATE_SUB(send_date, 30) THEN previous_campaign_id END) AS previous_email_click_cnt_30,
        COUNT(DISTINCT CASE WHEN click_date<send_date AND click_date>=DATE_SUB(send_date, 90) THEN previous_campaign_id END) AS previous_email_click_cnt_90,
        COUNT(DISTINCT CASE WHEN click_date<send_date AND click_date>=DATE_SUB(send_date, 180) THEN previous_campaign_id END) AS previous_email_click_cnt_180,
        MIN(click_date) AS previous_first_email_click_date,
        MAX(click_date) AS previous_last_email_click_date
    FROM
        (SELECT a.user_id, a.campaign_id, a.send_date, fa.click_date, fa.campaign_id AS previous_campaign_id
        FROM send a
        LEFT JOIN email_click fa 
        ON a.user_id = fa.user_id
        AND a.send_date>fa.click_date) a 
    GROUP BY 1,2,3
),
previous_email_open AS (
    SELECT user_id, campaign_id, send_date, 
        COUNT(DISTINCT CASE WHEN open_date<send_date THEN previous_campaign_id END) AS previous_email_open_cnt,
        COUNT(DISTINCT CASE WHEN open_date<send_date AND open_date>=DATE_SUB(send_date, 14) THEN previous_campaign_id END) AS previous_email_open_cnt_14,
        COUNT(DISTINCT CASE WHEN open_date<send_date AND open_date>=DATE_SUB(send_date, 30) THEN previous_campaign_id END) AS previous_email_open_cnt_30,
        COUNT(DISTINCT CASE WHEN open_date<send_date AND open_date>=DATE_SUB(send_date, 90) THEN previous_campaign_id END) AS previous_email_open_cnt_90,
        COUNT(DISTINCT CASE WHEN open_date<send_date AND open_date>=DATE_SUB(send_date, 180) THEN previous_campaign_id END) AS previous_email_open_cnt_180,
        MIN(open_date) AS previous_first_email_open_date,
        MAX(open_date) AS previous_last_email_open_date
    FROM
        (SELECT a.user_id, a.campaign_id, a.send_date, fa.open_date, fa.campaign_id AS previous_campaign_id
        FROM send a
        LEFT JOIN email_open fa 
        ON a.user_id = fa.user_id
        AND a.send_date>fa.open_date) a 
    GROUP BY 1,2,3
)

SELECT 
    a.campaign_id,
    a.campaign_name,
    a.message_medium,
    a.campaign_state, 
    a.type, 
    a.send_size,
    template.template_id, 
    template.message_type,
    template.sms_template, 
    template.email_template_subject, 
    template.email_template_preheader,
    send.user_id,
    send.send_time,
    send.send_date,
    EXTRACT(HOUR FROM send_time) AS send_hour,
    date_format(send_time, 'EEEE') AS send_dow,
    CASE WHEN MONTH(DATE(send_time))=12 AND WEEKOFYEAR(DATE(send_time)) = 1 
              THEN CONCAT(CAST(YEAR(DATE(send_time)) + 1 AS STRING), 'W', LPAD(CAST(WEEKOFYEAR(DATE(send_time)) AS STRING), 2, '0')) 
        WHEN MONTH(DATE(send_time))=1 AND WEEKOFYEAR(DATE(send_time)) IN (52,53) 
              THEN CONCAT(CAST(YEAR(DATE(send_time)) - 1 AS STRING), 'W', LPAD(CAST(WEEKOFYEAR(DATE(send_time)) AS STRING), 2, '0')) 
        ELSE CONCAT(CAST(YEAR(DATE(send_time)) AS STRING), 'W', LPAD(CAST(WEEKOFYEAR(DATE(send_time)) AS STRING), 2, '0')) 
        END AS send_week,
    date_format(TIMESTAMP(send_time),'yyyy-MM') AS send_month,
    CASE WHEN send.send_time < u.fst_apply_limit_time THEN 'New' ELSE 'Returning' END AS ls_application_tag,
    CASE WHEN send.send_time < u.fst_withdraw_time THEN 'new' ELSE 'old' END AS ls_user_tag,
    send.rendered_sms_message, 
    send.sms_send_count,
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
    DATEDIFF(send.send_date, previous_first_sms_send_date) AS previous_first_sms_send_interval,
    DATEDIFF(send.send_date, previous_last_sms_send_date) AS previous_last_sms_send_interval,
    DATEDIFF(send.send_date, previous_first_email_send_date) AS previous_first_email_send_interval,
    DATEDIFF(send.send_date, previous_last_email_send_date) AS previous_last_email_send_interval,
    DATEDIFF(send.send_date, previous_first_sms_click_date) AS previous_first_sms_click_interval,
    DATEDIFF(send.send_date, previous_last_sms_click_date) AS previous_last_sms_click_interval,
    DATEDIFF(send.send_date, previous_first_email_click_date) AS previous_first_email_click_interval,
    DATEDIFF(send.send_date, previous_last_email_click_date) AS previous_last_email_click_interval,
    DATEDIFF(send.send_date, previous_first_email_open_date) AS previous_first_email_open_interval,
    DATEDIFF(send.send_date, previous_last_email_open_date) AS previous_last_email_open_interval,
    CASE WHEN bounce_flag=1 THEN 1 ELSE 0 END AS bounce_flag,
    CASE WHEN open_flag=1 THEN 1 ELSE 0 END AS open_flag,
    CASE WHEN click_flag=1 THEN 1 ELSE 0 END AS click_flag,
    CASE WHEN unsubscribe_flag=1 THEN 1 ELSE 0 END AS unsubscribe_flag,
    CASE WHEN complaint_flag=1 THEN 1 ELSE 0 END AS complaint_flag
FROM campaign a

LEFT JOIN 
    (SELECT DISTINCT campaign_id, template_id, message_type, sms_template, email_template_subject, email_template_preheader FROM template) template
ON a.campaign_id=template.campaign_id

LEFT JOIN 
    (SELECT DISTINCT campaign_id, user_id, send_time, send_date, rendered_sms_message, sms_send_count FROM send) send
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
AND send.send_date=pss.send_date

LEFT JOIN previous_email_send AS pes
ON a.campaign_id=pes.campaign_id
AND send.user_id=pes.user_id
AND send.send_date=pes.send_date

LEFT JOIN previous_sms_click AS psc
ON a.campaign_id=psc.campaign_id
AND send.user_id=psc.user_id
AND send.send_date=psc.send_date

LEFT JOIN previous_email_click AS pec
ON a.campaign_id=pec.campaign_id
AND send.user_id=pec.user_id
AND send.send_date=pec.send_date

LEFT JOIN previous_email_open AS peo
ON a.campaign_id=peo.campaign_id
AND send.user_id=peo.user_id
AND send.send_date=peo.send_date

LEFT JOIN edw_ewa.dwb_user_fst_conv_dtl AS u
ON send.user_id=u.user_id

WHERE send.user_id IS NOT NULL 
AND send.send_time IS NOT NULL
ORDER BY a.campaign_name, send.send_date, send.user_id
;