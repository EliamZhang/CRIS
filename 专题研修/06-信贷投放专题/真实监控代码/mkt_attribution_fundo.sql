DROP TABLE IF EXISTS ba.mkt_attribution_fundo;
CREATE TABLE IF NOT EXISTS ba.mkt_attribution_fundo AS
SELECT DISTINCT
    application_id,
    user_id,
    application_date,
    application_month,
    attribution_source,
    CASE
        WHEN attribution_source LIKE '%google%' THEN 'Google'
        WHEN attribution_source IN ('bing') THEN 'Bing'
        WHEN attribution_source IN ('Meta-SiteLink-1', 'Meta-SiteLink-2', 'Meta-SiteLink-3', 'facebook', 'fb', 'fb-SiteLink', 'fb-SiteLink-1', 'fb-SiteLink-2', 'ig') THEN 'Meta'
        WHEN attribution_source IN ('tiktok') THEN 'Tiktok'
        WHEN attribution_source IN ('ebroker','clear score','tippla','lendela','leadmarket','finder','swift loans','good2goloans',
                                      'wonderloans','ezpzfinance','yesloans','klarna','overflow','EOACLK', 'lml','lead_market') THEN 'Lead Partner'
        WHEN attribution_source IN ('Klaviyo', 'trustpilot', 'fundo marketing', 'fundo affiliates', 'Iterable', 'zoho marketing', 'sms', 'email') THEN 'Owned Channels'
        WHEN attribution_source IN ('chatgpt.com', 'perplexity', 'copilot.com', 'openai') THEN 'GEO'
        WHEN attribution_source IN ('Mailgun', 'mailgun', 'burstsms', 'zalo', 'search') THEN 'Organic'
        ELSE 'Organic'
    END AS attributed_category,
    attribution_medium,
    attribution_campaign,
    attribution_term
    
FROM 
    (
    -- ads tracking
    SELECT DISTINCT
        application_id,
        user_id,
        application_date,
        application_month,
        -- CASE WHEN REGEXP_CONTAINS(ads_tokens, '.*gclid.*') THEN 'google_ads'
        --     WHEN REGEXP_CONTAINS(ads_tokens, '.*fbclid.*') THEN 'facebook_ads'
        --     WHEN REGEXP_CONTAINS(ads_tokens, '.*ttclid.*') THEN 'tiktok_ads'
        --     WHEN REGEXP_CONTAINS(ads_tokens, '.*msclkid.*') THEN 'bing_ads'
        --     ELSE 'unknown_source'
        --     END AS attribution_source,
        CASE WHEN ads_tokens rlike '.*gclid.*' THEN 'google_ads'  -- 修复：用rlike替换REGEXP_CONTAINS
            WHEN ads_tokens rlike '.*fbclid.*' THEN 'facebook_ads'
            WHEN ads_tokens rlike '.*ttclid.*' THEN 'tiktok_ads'
            WHEN ads_tokens rlike '.*msclkid.*' THEN 'bing_ads'
            ELSE 'unknown_source'
            END AS attribution_source,
        'Null' AS attribution_medium,
        'Null' AS attribution_campaign,
        'Null' AS attribution_term
    FROM 
        (SELECT DISTINCT
            la.id AS application_id,
            la.user_id,
            date_format( TIMESTAMP(la.created_at),'yyyy-MM-dd') AS application_date,
            date_format( TIMESTAMP(la.created_at),'yyyy-MM') AS application_month,
            -- STRING_AGG(ua.value ORDER BY ua.created_at ASC) AS ads_tokens
            concat_ws(
                    '',  -- 无分隔符拼接（与原STRING_AGG默认行为一致）
                    transform(
                    sort_array(  -- 直接排序，默认按结构体第一个字段（created_at）升序
                      collect_list(struct(ua.created_at, ua.value))  -- 收集(时间,值)结构体数组
                    ),
                    x -> x.value  -- 提取排序后的value
                    )
                ) AS ads_tokens
        FROM ods.fundo_v2_trg_ads_tracking_ids ua  
        INNER JOIN ods.aus_fundo_loans_loan_applications la 
        ON ua.application_id = la.id 
        WHERE ua.attr = 'ADS_TRACKING'
        GROUP BY 1,2,3,4) t1

    UNION ALL
    -- utm campaign
    SELECT DISTINCT
        la.id as application_id, 
        la.user_id,
        date_format(TIMESTAMP(la.created_at),'yyyy-MM-dd') AS application_date,
        date_format(TIMESTAMP(la.created_at),'yyyy-MM') AS application_month,
        attribution_source,
        attribution_medium,
        attribution_campaign,
        attribution_term
    FROM 
        (SELECT 
            application_id,
            user_id,
            created_at,
            CASE 
                WHEN utm_source = 'leadmarket' THEN 'lead_market' 
                WHEN utm_source LIKE '%google%' THEN 'google' 
                ELSE utm_source 
                END AS attribution_source,
            CASE WHEN utm_medium LIKE '%utm_medium=ppc%' THEN 'ppc' ELSE utm_medium END AS attribution_medium,
            CASE WHEN utm_campaign LIKE '%utm_campaign=brand%' THEN 'brand' 
                WHEN utm_campaign = 'max' THEN 'max_value' 
                ELSE utm_campaign END AS attribution_campaign,
            CASE WHEN utm_term LIKE '%utm_term=fundo%' THEN 'fundo' ELSE utm_term END AS attribution_term,
            ROW_NUMBER() OVER (PARTITION BY application_id ORDER BY created_at DESC, utm_source ASC, utm_campaign DESC, utm_term DESC) as rn
        FROM ods.aus_fundo_loans_utm_campaign_history
        WHERE application_id IS NOT NULL AND utm_source IS NOT NULL
        ) attr
    LEFT JOIN ods.aus_fundo_loans_loan_applications la
    ON la.id = attr.application_id
    WHERE attr.rn = 1

    UNION ALL
    -- lead partner
    SELECT DISTINCT
        la.id as application_id, 
        la.user_id,
        date_format(TIMESTAMP(la.created_at),'yyyy-MM-dd') AS application_date,
        date_format(TIMESTAMP(la.created_at),'yyyy-MM') AS application_month,
        provider AS attribution_source,
        'Null' AS attribution_medium,
        'Null' AS attribution_campaign,
        'Null' AS attribution_term
    FROM ods.fundo_v2_loan_provider_leads_view lpl
    INNER JOIN ods.aus_fundo_loans_loan_applications la
    ON la.id = lpl.application_id 
    WHERE provider IN ('lml', 'overflow')
    )
WHERE application_date >= '2023-10-01'
;