DROP TABLE IF EXISTS ba.mkt_attribution_first_touch_7d;
CREATE TABLE IF NOT EXISTS ba.mkt_attribution_first_touch_7d AS
SELECT 
    a.application_id,
    a.user_id,
    a.application_date,
    a.application_month,
    CASE WHEN b.media_source IN ('googleadwords_int', 'google') THEN 'google'
        WHEN b.media_source='Facebook Ads' THEN 'Facebook Ads'
        WHEN b.media_source='Apple Search Ads' THEN 'Apple Search Ads'
        WHEN b.media_source IN ('iterable_email', 'iterable_sms', 'Iterable', 'SMS', 'Email') THEN 'Iterable'
        WHEN b.media_source='tiktokglobal_int' THEN 'tiktok'
        ELSE a.attributed_utm END AS attributed_utm,
    CASE WHEN b.media_source IN ('googleadwords_int', 'google') THEN 'Google'
        WHEN b.media_source='Facebook Ads' THEN 'Meta'
        WHEN b.media_source='Apple Search Ads' THEN 'Apple Search Ads'
        WHEN b.media_source IN ('iterable_email', 'iterable_sms', 'Iterable', 'SMS', 'Email') THEN 'Owned Channels'
        WHEN b.media_source='tiktokglobal_int' THEN 'Tiktok'
        ELSE a.attributed_category END AS attributed_category,
    CASE WHEN b.media_source IN ('googleadwords_int', 'google', 'Facebook Ads', 'Apple Search Ads', 'tiktokglobal_int') THEN NULL
        WHEN b.media_source IN ('iterable_email', 'Email') THEN 'email'
        WHEN b.media_source IN ('iterable_sms', 'SMS') THEN 'sms'
        ELSE a.attributed_medium END AS attributed_medium,
    CASE WHEN b.media_source IN ('googleadwords_int', 'google', 'Facebook Ads', 'Apple Search Ads', 'iterable_email', 'iterable_sms', 'Iterable', 'SMS', 'Email', 'tiktokglobal_int') THEN b.campaign
        ELSE a.attributed_campaign END AS attributed_campaign,
    a.attributed_term AS attributed_term,
    CASE WHEN b.media_source IN ('googleadwords_int', 'google', 'Facebook Ads', 'Apple Search Ads', 'iterable_email', 'iterable_sms', 'Iterable', 'SMS', 'Email', 'tiktokglobal_int') THEN b.platform END AS platform,
    CASE WHEN b.media_source IN ('googleadwords_int', 'google', 'Facebook Ads', 'Apple Search Ads', 'iterable_email', 'iterable_sms', 'Iterable', 'SMS', 'Email', 'tiktokglobal_int') THEN b.inserttime
        ELSE a.first_touch_time END AS first_touch_time

FROM 
    (SELECT DISTINCT
        la.id AS application_id,
        la.user_id,
        date_format(TIMESTAMP(la.created_at),'yyyy-MM-dd') AS application_date,
        date_format(TIMESTAMP(la.created_at),'yyyy-MM') AS application_month,
        COALESCE(
            CASE 
                WHEN src.attribution_source = 'leadmarket' THEN 'lead_market' 
                WHEN src.attribution_source LIKE '%google%' THEN 'google' 
                ELSE src.attribution_source 
            END, 
            'Organic'
        ) AS attributed_utm,
        CASE
            WHEN src.attribution_source LIKE '%google%' THEN 'Google'
            WHEN src.attribution_source IN ('bing') THEN 'Bing'
            WHEN src.attribution_source IN ('Meta-SiteLink-1', 'Meta-SiteLink-2', 'Meta-SiteLink-3', 'facebook', 'fb', 'fb-SiteLink', 'fb-SiteLink-1', 'fb-SiteLink-2', 'ig') THEN 'Meta'
            WHEN src.attribution_source IN ('tiktok') THEN 'Tiktok'
            WHEN src.attribution_source IN ('ebroker','clear score','tippla','lendela','leadmarket','finder','swift loans','good2goloans',
                                          'wonderloans','ezpzfinance','yesloans','klarna','overflow','EOACLK', 'lml','lead_market') THEN 'Lead Partner'
            WHEN src.attribution_source IN ('Klaviyo', 'trustpilot', 'fundo marketing', 'fundo affiliates', 'Iterable', 'zoho marketing', 'sms', 'email') THEN 'Owned Channels'
            WHEN src.attribution_source IN ('chatgpt.com', 'perplexity', 'copilot.com', 'openai') THEN 'GEO'
            WHEN src.attribution_source IN ('Mailgun', 'mailgun', 'burstsms', 'zalo', 'search') THEN 'Organic'
            ELSE 'Organic'
        END AS attributed_category,
        COALESCE(CASE WHEN src.attribution_medium LIKE '%utm_medium=ppc%' THEN 'ppc' ELSE src.attribution_medium END, 'Null') AS attributed_medium,
        COALESCE(CASE WHEN src.attribution_campaign LIKE '%utm_campaign=brand%' THEN 'brand' 
                      WHEN src.attribution_campaign = 'max' THEN 'max_value' ELSE src.attribution_campaign END, 'Null') AS attributed_campaign,
        COALESCE(CASE WHEN src.attribution_term LIKE '%utm_term=fundo%' THEN 'fundo' ELSE src.attribution_term END, 'Null') AS attributed_term,
        src.first_touch_time
    FROM 
        ods.aus_fundo_loans_loan_applications la
    LEFT JOIN 
        (SELECT 
            user_id,
            application_id,
            attribution_source,
            attribution_medium,
            attribution_campaign,
            attribution_term,
            first_touch_time,
            ROW_NUMBER() OVER (PARTITION BY user_id, application_id ORDER BY first_touch_time ASC, attribution_source ASC, attribution_campaign DESC, attribution_term DESC) AS rn
        FROM 
            (SELECT DISTINCT
                utm.user_id,
                la_ref.id AS application_id,
                 CASE 
                    WHEN utm.utm_source = 'leadmarket' THEN 'lead_market'
                    ELSE utm.utm_source 
                END AS attribution_source,
                utm.utm_medium AS attribution_medium,
                utm.utm_campaign AS attribution_campaign,
                utm.utm_term AS attribution_term,
                utm.created_at AS first_touch_time
            FROM ods.aus_fundo_loans_utm_campaign_history utm
            INNER JOIN ods.aus_fundo_loans_loan_applications la_ref
                ON utm.user_id = la_ref.user_id
                AND date_format(TIMESTAMP(utm.created_at),'yyyy-MM-dd') BETWEEN 
                    date_format(date_sub(TIMESTAMP(la_ref.created_at), 7) ,'yyyy-MM-dd')
                    AND 
                    date_format(TIMESTAMP(la_ref.created_at),'yyyy-MM-dd')
    
            UNION ALL
    
            SELECT DISTINCT 
                provider.user_id,
                provider.application_id,
                provider.provider AS attribution_source,
                NULL AS attribution_medium,
                NULL AS attribution_campaign,
                NULL AS attribution_term,
                provider.created_at AS first_touch_time
            FROM ods.fundo_v2_loan_provider_leads_view provider
            INNER JOIN ods.aus_fundo_loans_loan_applications la_ref
                ON provider.application_id = la_ref.id
                AND date_format( TIMESTAMP(provider.created_at),'yyyy-MM-dd') BETWEEN 
                    date_format(date_sub(TIMESTAMP(la_ref.created_at), 7) ,'yyyy-MM-dd')
                    AND 
                    date_format(TIMESTAMP(la_ref.created_at),'yyyy-MM-dd')
            ) combined_sources
        ) src 
    ON la.id = src.application_id 
    AND src.rn = 1
    WHERE la.created_at >= '2023-10-01') a

LEFT JOIN 
    (SELECT user_id, 
        media_source, 
        CASE WHEN media_source='googleadwords_int' THEN 
              CASE WHEN campaign IN ('BRA - Search - Brand - All', 'BRA - Search - Brand - New', '12763149996') THEN 'brand'
                  WHEN campaign = 'BRA - Search - Brand - Returning' THEN 'brand-rlsa'
                  WHEN campaign IN ('DG - Demand Gen - New | Value', 'DG - Demand Gen - New | Volume') THEN 'demand-gen'
                  WHEN campaign = 'DG - Demand Gen - Returning' THEN 'demand-gen-return'
                  WHEN campaign = 'NBR - Search - Cash Loans | By Type | Volume' THEN 'nbr-by-type'
                  WHEN campaign = 'NBR - Search - Cash Loans | Value' THEN 'nbr-cash-loans'
                  WHEN campaign IN ('NBR - Search - Competitors | Value', 'NBR - Search - Competitors | Volume', '20284299338') THEN 'nbr-competitors'
                  WHEN campaign = 'NBR - Search - Credit | Value' THEN 'nbr-credit'
                  WHEN campaign = 'NBR - Search - Payday Loans | Value' THEN 'nbr-payday-loans'
                  WHEN campaign IN ('NBR - Search - Master - New | Volume', 'NBR - Search - Master - Value', 'NBR - Search - Master | Volume', 'NBR - Search - Master - Volume', '22731729789') THEN 'nbr_master_volume'
                  WHEN campaign IN ('PMAX - Performance Max | Value', 'PMAX - Value', 'PMAX - Value | All', '22376839354') THEN 'max_value'
                  WHEN campaign IN ('PMAX - Value | New', 'PMAX - Value | New Customers') THEN 'max_value_new'
                  WHEN campaign IN ('PMAX - Performance Max | Volume', 'PMAX - Volume', 'zPMAX - Performance Max | Volume') THEN 'max_volume'
                  WHEN campaign IN ('PMAX - Volume (new)') THEN 'max_volume_new'
                  WHEN campaign IN ('NBR - Search - Instant Loans | Volume', 'zNBR - Search - Instant Loans | Volume') THEN 'nbr-instant-loans'
                  WHEN campaign = 'zNBR - Search - Fast Cash | Volume' THEN 'nbr-fast-cash'
                  WHEN campaign LIKE 'APP%' OR campaign LIKE 'Android%' THEN campaign
                  ELSE campaign END
            ELSE campaign
        END AS campaign,
        platform, 
        inserttime
    FROM ods.aus_market_tb_appsflyer_signup_log
    WHERE attribute_node='applicationGenerated'
    AND media_source<>'organic'
    AND isactive=1) b
ON a.user_id = b.user_id
AND DATE(a.application_date) = DATE(b.inserttime)
;