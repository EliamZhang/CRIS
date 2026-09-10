-- ============================================================================
-- Fundo 营销花费 - 灵活日/周/月拆分
-- ============================================================================

-- 整体思路：
--   STEP 0    ba.marketing_cost_input_raw      —— 手工花费录入表（day/week=可选的形状数据，month=可选的对账口径）
--   STEP 0.5  数据完整性检查
--   STEP 1    ba.cost_category_daily_volume_count       —— 申请量(application_date)+放款量(dispersal_date)合并，
--                                                  并直接算出统一的volume字段(clear score=loans，其他=applications)；
--   STEP 2    ba.marketing_cost_daily_shape    —— day/week原始形状(按volume拆周) + Google后台日花费，校准前
--   STEP 2.5  ba.marketing_cost_daily          —— 有month记录：完全覆盖→整体等比例缩放；有缺口→缺口按残差+volume占比分摊，已覆盖天数原样保留；没有month记录：原样透传
--   STEP 3    ba.marketing_cost_actual_breakdown   —— 将花费分摊到 application_tag / user_tag / traffic_source / app_platform / attributed_category 各维度；
--                                                  默认渠道+clear score合并成一个"按volume拆分"分支(因为volume字段已经统一了口径)，
--                                                  Iterable(周度发送量比例拆user_tag/application_tag + volume占比拆traffic_source/app_platform，两组独立相乘)
--                                                  Google(campaign精确拆分)单独处理
--   STEP 4    ba.marketing_cost_actual_split —— 按(month,cost_category,user_tag)重新聚合，再关联放款实际值/放款预测值，产出粗颗粒度的月度花费+放款汇总表；
--                                               用于财务和市场看板分析


-- ============================================================================
-- STEP 0：手工花费录入表
-- ============================================================================
-- CREATE TABLE IF NOT EXISTS ba.marketing_cost_input_raw (
--     cost_category   STRING,         -- 渠道名，必须跟 customer_profile_rawdata.cost_category 完全一致（区分大小写/空格）
--     period_type     STRING,         -- 'day' | 'week' | 'month'
--     period_key      STRING,         -- day: 具体日期'YYYY-MM-DD'；week: 对应application_week取值(如'2026W31')；month: 对应application_month取值(如'2026-07')
--     cost            DECIMAL(14,2),  -- 该period对应的花费
--     note            STRING          -- 备注，方便你自己回溯
-- )
-- STORED AS ORC
-- TBLPROPERTIES ("orc.compress"="SNAPPY");

-- period_type说明：
--   'month' —— 可选的对账口径。填了就以这个数字为准，把当月的day/week(或Google后台)数据等比例缩放校准；
--               不填就直接用已有的day/week(或Google后台)数据，不做任何缩放——比如月中只攒了前两周的
--               数据，还没等到月度总数，完全没问题，先按周数据用着，等月度总数出来了再补一条month记录。
--   'day' / 'week' —— 形状数据，反映花费在各天/各周怎么分布。同一天不能同时被day和week覆盖。
--                      Google不需要填day/week，它的形状自动来自mkt.mkt_imp_clk_cost后台。
--                      clear score的形状驱动量是放款量(不是申请量)，clear score的形状驱动量是发送量，其他渠道是申请量。
--
-- 日常维护方式：追加/覆盖一批新数据。


-- DROP TABLE IF EXISTS ba.marketing_cost_input_raw_stg;
-- CREATE TABLE ba.marketing_cost_input_raw_stg AS
-- SELECT * FROM ba.marketing_cost_input_raw
-- -- WHERE NOT (cost_category IN ('Google','Meta','Bing','clear score','lead_market','Others') AND period_type = 'week' AND period_key = '2026-07')          -- 先删掉要覆盖的旧记录
-- UNION ALL
-- VALUES
--     ('Meta',              'week',  '2026W31',  8128.89,  NULL),
--     ('Apple Search Ads',  'week',  '2026W31',  10618.18, NULL),
--     ('overflow',          'week',  '2026W31',  1180.00,  NULL),
--     ('lead_market',       'week',  '2026W31',  11465.00, NULL),
--     ('clear score',       'week',  '2026W31',  660.00,   NULL),
--     ('lml',               'week',  '2026W31',  8000.00,  NULL),
--     ('Iterable',          'week',  '2026W31',  4082.36,  NULL),
--     ('Meta',              'week',  '2026W30',  9187.65,  NULL),
--     ('Apple Search Ads',  'week',  '2026W30',  10189.80, NULL),
--     ('overflow',          'week',  '2026W30',  1267.00,  NULL),
--     ('lead_market',       'week',  '2026W30',  8733.78,  NULL),
--     ('clear score',       'week',  '2026W30',  660.00,   NULL),
--     ('lml',               'week',  '2026W30',  6716.00,  NULL),
--     ('Meta',              'week',  '2026W29',  8324.73,  NULL),
--     ('Apple Search Ads',  'week',  '2026W29',  9712.44,  NULL),
--     ('overflow',          'week',  '2026W29',  1315.00,  NULL),
--     ('lead_market',       'week',  '2026W29',  9266.00,  NULL),
--     ('clear score',       'week',  '2026W29',  300.00,   NULL),
--     ('lml',               'week',  '2026W29',  6487.00,  NULL)
-- ;

-- DROP TABLE ba.marketing_cost_input_raw;
-- CREATE TABLE ba.marketing_cost_input_raw AS
-- SELECT * FROM ba.marketing_cost_input_raw_stg;


-- ============================================================================
-- STEP 0.5：数据完整性检查
-- ============================================================================

-- -- 检查1(硬性)：day和week不能互相重叠——同一个渠道同一天只能被其中一种覆盖，两种都覆盖会导致这一天的
-- --        花费在STEP2里被重复计入"形状"。
-- WITH day_week_expanded AS (
--     SELECT cost_category, CONCAT('day:', period_key) AS entry, TO_DATE(period_key) AS date
--     FROM ba.marketing_cost_input_raw WHERE period_type = 'day'
--     UNION ALL
--     SELECT r.cost_category, CONCAT('week:', r.period_key) AS entry, dc.date
--     FROM ba.marketing_cost_input_raw r JOIN ba.date_calendar dc ON dc.week = r.period_key
--     WHERE r.period_type = 'week'
-- )
-- SELECT cost_category, date,
--        COUNT(DISTINCT entry) AS overlapping_entries,
--        COLLECT_LIST(DISTINCT entry) AS entries
-- FROM day_week_expanded
-- GROUP BY cost_category, date
-- HAVING COUNT(DISTINCT entry) > 1
-- ORDER BY cost_category, date;

-- -- 检查2(仅供参考，不是错误)：哪些(渠道,月份)现在有day/week数据(或者Google后台有花费)，但还没有
-- --        month对账口径——这些会直接按已有数据原样使用，不做缩放。等拿到月度总数了补一条month记录即可。
-- WITH day_month AS (
--     SELECT cost_category, DATE_FORMAT(TO_DATE(period_key), 'yyyy-MM') AS month
--     FROM ba.marketing_cost_input_raw WHERE period_type = 'day'
-- ),
-- week_month AS (
--     SELECT DISTINCT r.cost_category, dc.month
--     FROM ba.marketing_cost_input_raw r
--     JOIN ba.date_calendar dc ON dc.week = r.period_key
--     WHERE r.period_type = 'week'
-- ),
-- google_month AS (
--     SELECT DISTINCT 'Google' AS cost_category, DATE_FORMAT(DATE(biz_date), 'yyyy-MM') AS month
--     FROM mkt.mkt_imp_clk_cost
--     WHERE channel = 'google'
--     AND biz_date>='2025-07-01'
-- ),
-- shape_months AS (
--     SELECT cost_category, month FROM day_month
--     UNION SELECT cost_category, month FROM week_month
--     UNION SELECT cost_category, month FROM google_month
-- )
-- SELECT sm.cost_category, sm.month
-- FROM shape_months sm
-- LEFT JOIN ba.marketing_cost_input_raw mt
--   ON mt.cost_category = sm.cost_category AND mt.period_type = 'month' AND mt.period_key = sm.month
-- WHERE mt.period_key IS NULL
-- ORDER BY 1, 2;



-- ============================================================================
-- STEP 1：申请量(application_date)+放款量(dispersal_date)分开统计再合并，并直接产出统一的volume字段
-- ============================================================================
-- volume字段统一了"花费驱动量"的口径：clear score按放款结算，volume=loans；其他渠道按申请量算，volume=applications

DROP TABLE IF EXISTS ba.cost_category_daily_volume_count;
CREATE TABLE ba.cost_category_daily_volume_count AS
WITH app_agg AS (
    SELECT
        TO_DATE(application_date)   AS date,
        application_week   AS week,
        application_month  AS month,
        cost_category,
        attributed_category,
        application_tag,
        user_tag,
        traffic_source,
        app_platform,
        COUNT(application_id) AS applications
    FROM ba.customer_profile_rawdata
    WHERE application_date >= '2025-07-01'
      AND application_date <= to_date('${yyyy-mm-dd}')
    GROUP BY 1,2,3,4,5,6,7,8,9
),
loan_agg AS (
    SELECT
        TO_DATE(dispersal_date)   AS date,
        dispersal_week     AS week,
        dispersal_month    AS month,
        cost_category,
        attributed_category,
        application_tag,
        user_tag,
        traffic_source,
        app_platform,
        COUNT(application_id) AS loans
    FROM ba.customer_profile_rawdata
    WHERE application_status = '4.Funded'
      AND dispersal_date >= '2025-07-01'
      AND dispersal_date <= to_date('${yyyy-mm-dd}')
    GROUP BY 1,2,3,4,5,6,7,8,9
)
SELECT
    COALESCE(a.date, l.date) AS date,
    COALESCE(a.week, l.week) AS week,
    COALESCE(a.month, l.month) AS month,
    COALESCE(a.cost_category, l.cost_category) AS cost_category,
    COALESCE(a.attributed_category, l.attributed_category) AS attributed_category,
    COALESCE(a.application_tag, l.application_tag) AS application_tag,
    COALESCE(a.user_tag, l.user_tag) AS user_tag,
    COALESCE(a.traffic_source, l.traffic_source) AS traffic_source,
    COALESCE(a.app_platform, l.app_platform) AS app_platform,
    COALESCE(a.applications, 0) AS applications,
    COALESCE(l.loans, 0) AS loans,
    CASE WHEN COALESCE(a.cost_category, l.cost_category) = 'clear score'
         THEN COALESCE(l.loans, 0)
         ELSE COALESCE(a.applications, 0)
    END AS volume
FROM app_agg a
FULL OUTER JOIN loan_agg l
  ON a.date = l.date
 AND a.cost_category = l.cost_category
 AND a.attributed_category = l.attributed_category
 AND a.application_tag = l.application_tag
 AND a.user_tag = l.user_tag
 AND a.traffic_source = l.traffic_source
 AND a.app_platform = l.app_platform
;



-- ============================================================================
-- STEP 2：day/week原始形状 + Google后台日花费 -> 校准前的形状
-- ============================================================================
DROP TABLE IF EXISTS ba.marketing_cost_daily_shape;
CREATE TABLE ba.marketing_cost_daily_shape AS
WITH channel_daily_volume AS (
    SELECT date, cost_category, SUM(volume) AS volume
    FROM ba.cost_category_daily_volume_count
    GROUP BY 1, 2
),
day_entries AS (
    SELECT TO_DATE(period_key) AS date, cost_category, CAST(cost AS DOUBLE) AS raw_cost
    FROM ba.marketing_cost_input_raw
    WHERE period_type = 'day'
),
-- week记录：按该渠道当周每天volume占比，把周总数拆成每天；volume全为0时兜底按自然天数均分
week_entries_daily AS (
    SELECT
        dc.date,
        r.cost_category,
        CAST(r.cost AS DOUBLE) *
            CASE WHEN COALESCE(SUM(COALESCE(v.volume,0)) OVER (PARTITION BY r.cost_category, r.period_key), 0) = 0
                 THEN CAST(1.0 AS DOUBLE) / COUNT(*) OVER (PARTITION BY r.cost_category, r.period_key)
                 ELSE CAST(COALESCE(v.volume,0) AS DOUBLE)
                      / CAST(SUM(COALESCE(v.volume,0)) OVER (PARTITION BY r.cost_category, r.period_key) AS DOUBLE)
            END AS raw_cost
    FROM ba.marketing_cost_input_raw r
    JOIN ba.date_calendar dc
      ON dc.week = r.period_key
    LEFT JOIN channel_daily_volume v
      ON v.date = dc.date AND v.cost_category = r.cost_category
    WHERE r.period_type = 'week'
),
-- Google的日度花费直接来自后台campaign数据
google_backend AS (
    SELECT
        DATE(biz_date) AS date,
        'Google' AS cost_category,
        CAST(SUM(cost) AS DOUBLE) AS raw_cost
    FROM mkt.mkt_imp_clk_cost
    WHERE channel = 'google'
    GROUP BY 1
),
-- "本周花费还没录入"的滞后缺口，用该渠道前一周的日均花费临时补齐
channel_last_covered AS (
    SELECT cost_category, MAX(date) AS last_covered_date
    FROM (
        SELECT date, cost_category FROM day_entries
        UNION ALL
        SELECT date, cost_category FROM week_entries_daily
    ) t
    GROUP BY 1
),
channel_prevweek_avg AS (
    SELECT s.cost_category, SUM(s.raw_cost) * 1.0 / COUNT(*) AS avg_daily_cost
    FROM (
        SELECT date, cost_category, raw_cost FROM day_entries
        UNION ALL
        SELECT date, cost_category, raw_cost FROM week_entries_daily
    ) s
    JOIN channel_last_covered c ON c.cost_category = s.cost_category
    JOIN ba.date_calendar dc_last ON dc_last.date = c.last_covered_date
    JOIN ba.date_calendar dc_s ON dc_s.date = s.date AND dc_s.week = dc_last.week
    GROUP BY 1
),
tail_gap_fill AS (
    SELECT dc.date, c.cost_category, CAST(pw.avg_daily_cost AS DOUBLE) AS raw_cost
    FROM channel_last_covered c
    JOIN channel_prevweek_avg pw ON pw.cost_category = c.cost_category
    JOIN ba.date_calendar dc
      ON dc.date > c.last_covered_date AND dc.date <= to_date('${yyyy-mm-dd}')
    WHERE c.last_covered_date IS NOT NULL   -- 排除Google这类本来就没有day/week真实条目的渠道
)
SELECT date, cost_category, ROUND(raw_cost, 2) AS raw_cost FROM day_entries
UNION ALL
SELECT date, cost_category, ROUND(raw_cost, 2) AS raw_cost FROM week_entries_daily
UNION ALL
SELECT date, cost_category, ROUND(raw_cost, 2) AS raw_cost FROM tail_gap_fill
UNION ALL
SELECT date, cost_category, ROUND(raw_cost, 2) AS raw_cost FROM google_backend
;



-- ============================================================================
-- STEP 2.5：市场花费拆分到天
--   对每个"有month记录"的(渠道,月份)，先看day/week数据有没有完全覆盖当月每一天：
--     - 完全覆盖：没有"估算"问题，直接对这个月所有天做统一的等比例缩放(月度总数/已有总数)，对齐发票口径。
--     - 有缺口：已覆盖天数的花费原样保留，不缩放；缺口天数按"残差(月度总数-已覆盖花费) x 缺口天volume占比"分摊。
--     - 边界情况：如果残差<0(已覆盖天数花费已经超过月度总数)，没法只调缺口天来凑总数，退化成对全月统一缩放，这种情况应该去核实day/week是不是填错了。
--   没有month记录的(渠道,月份)：day/week/Google后台数据原样透传，不缩放。
-- ============================================================================
DROP TABLE IF EXISTS ba.marketing_cost_daily;
CREATE TABLE ba.marketing_cost_daily AS
WITH month_targets AS (
    SELECT cost_category, period_key AS month, cost AS month_total
    FROM ba.marketing_cost_input_raw
    WHERE period_type = 'month'
),
channel_daily_volume AS (
    SELECT date, cost_category, SUM(volume) AS volume
    FROM ba.cost_category_daily_volume_count
    GROUP BY 1, 2
),
day_shape_agg AS (
    SELECT date, cost_category, SUM(raw_cost) AS raw_cost
    FROM ba.marketing_cost_daily_shape
    GROUP BY 1, 2
),
full_calendar AS (
    SELECT mt.cost_category, mt.month, dc.date
    FROM month_targets mt
    JOIN ba.date_calendar dc ON dc.month = mt.month
),
-- 每个(渠道,月份)下，当月每一天有没有被day/week/Google后台数据覆盖到
day_coverage AS (
    SELECT f.cost_category, f.month, f.date, s.raw_cost
    FROM full_calendar f
    LEFT JOIN day_shape_agg s ON s.date = f.date AND s.cost_category = f.cost_category
),
month_coverage AS (
    SELECT cost_category, month,
           COUNT(*) AS total_days,
           SUM(CASE WHEN raw_cost IS NOT NULL THEN 1 ELSE 0 END) AS covered_days,
           SUM(COALESCE(raw_cost, 0)) AS covered_total
    FROM day_coverage
    GROUP BY 1, 2
),
month_calc AS (
    SELECT
        mt.cost_category, mt.month, mt.month_total,
        mc.total_days, mc.covered_days, mc.covered_total,
        CASE WHEN mc.covered_days = mc.total_days THEN 1 ELSE 0 END AS is_full_coverage,
        mt.month_total - mc.covered_total AS residual
    FROM month_targets mt
    JOIN month_coverage mc ON mc.cost_category = mt.cost_category AND mc.month = mt.month
),
missing_agg AS (
    -- 每个(渠道,月份)下，"缺口天"(没有被覆盖的天)一共有几天、volume总和是多少——用来把残差摊给缺口天
    SELECT dc.cost_category, dc.month,
           COUNT(*) AS missing_days,
           SUM(COALESCE(v.volume, 0)) AS missing_volume_total
    FROM day_coverage dc
    LEFT JOIN channel_daily_volume v ON v.date = dc.date AND v.cost_category = dc.cost_category
    WHERE dc.raw_cost IS NULL
    GROUP BY 1, 2
),
scaled AS (
    SELECT
        dc.date,
        dc.cost_category,
        CASE
            -- Others特例：从不产生day/week数据，永远是"全月都是缺口"，残差(=月度总数)不管正负都直接按当月天数平均摊给每一天
            WHEN dc.cost_category = 'Others' THEN
                CAST(mcalc.residual AS DOUBLE) / mcalc.total_days
            -- 情况A：全月完全覆盖 —— 统一等比例缩放对齐月度总数
            WHEN mcalc.is_full_coverage = 1 THEN
                CAST(COALESCE(dc.raw_cost, 0) AS DOUBLE) *
                CASE WHEN mcalc.covered_total = 0 THEN CAST(1.0 AS DOUBLE) / mcalc.total_days   -- 全月都填了但金额都是0的极端兜底
                     ELSE CAST(mcalc.month_total AS DOUBLE) / CAST(mcalc.covered_total AS DOUBLE) END
            -- 情况B：有缺口，且残差>=0 —— 已覆盖天数原样保留
            WHEN mcalc.residual >= 0 AND dc.raw_cost IS NOT NULL THEN CAST(dc.raw_cost AS DOUBLE)
            -- 情况B：有缺口，且残差>=0 —— 缺口天按volume占比分残差；缺口天volume全为0则均分
            WHEN mcalc.residual >= 0 AND dc.raw_cost IS NULL THEN
                CAST(mcalc.residual AS DOUBLE) *
                CASE WHEN COALESCE(ma.missing_volume_total, 0) = 0 THEN CAST(1.0 AS DOUBLE) / ma.missing_days
                     ELSE CAST(COALESCE(v.volume, 0) AS DOUBLE) / CAST(ma.missing_volume_total AS DOUBLE) END
            -- 情况C(边界)：残差<0，已覆盖天数已经超过月度总数——退化成对全月统一缩放，建议人工核实；
            -- 缺口天的COALESCE(dc.raw_cost,0)=0，0乘ratio还是0，不会被补成负数
            ELSE
                CAST(COALESCE(dc.raw_cost, 0) AS DOUBLE) *
                CASE WHEN mcalc.covered_total = 0 THEN CAST(1.0 AS DOUBLE) / mcalc.total_days
                     ELSE CAST(mcalc.month_total AS DOUBLE) / CAST(mcalc.covered_total AS DOUBLE) END
        END AS cost
    FROM day_coverage dc
    JOIN month_calc mcalc ON mcalc.cost_category = dc.cost_category AND mcalc.month = dc.month
    LEFT JOIN channel_daily_volume v ON v.date = dc.date AND v.cost_category = dc.cost_category
    LEFT JOIN missing_agg ma ON ma.cost_category = dc.cost_category AND ma.month = dc.month
),
passthrough AS (
    SELECT s.date, s.cost_category, s.raw_cost AS cost
    FROM ba.marketing_cost_daily_shape s
    LEFT JOIN ba.marketing_cost_input_raw mt
      ON mt.cost_category = s.cost_category AND mt.period_type = 'month'
     AND mt.period_key = DATE_FORMAT(s.date, 'yyyy-MM')
    WHERE mt.period_key IS NULL   -- 这个(渠道,月份)还没有month记录，原样透传
)
SELECT date, cost_category, ROUND(cost, 2) AS cost FROM scaled
UNION ALL
SELECT date, cost_category, ROUND(cost, 2) AS cost FROM passthrough
;



-- ============================================================================
-- STEP 3：将花费分摊到 application_tag / user_tag / traffic_source / app_platform / attributed_category 各维度
--     Google：沿用已有campaign级的精确拆分
--     Iterable：user_tag和application_tag用发送量拆，其他维度用volume(applications)拆
--     其他渠道：按volume拆
-- ============================================================================
DROP TABLE IF EXISTS ba.marketing_cost_actual_breakdown;
CREATE TABLE ba.marketing_cost_actual_breakdown AS
WITH 
-- 3.1 默认渠道：traffic_source/app_platform 按渠道固定指定，application_tag/user_tag依然按volume的联合分布拆
volume_by_dim AS (
    SELECT date, cost_category, attributed_category, application_tag, user_tag,
           SUM(volume) AS volume
    FROM ba.cost_category_daily_volume_count
    WHERE cost_category NOT IN ('Google', 'Iterable')
    GROUP BY 1,2,3,4,5
),
volume_by_channel_day AS (
    SELECT date, cost_category, SUM(volume) AS volume
    FROM ba.cost_category_daily_volume_count
    WHERE cost_category NOT IN ('Google', 'Iterable')
    GROUP BY 1,2
),
volume_split AS (
    SELECT
        j.date, d.cost_category, j.attributed_category, j.application_tag, j.user_tag,
        CASE WHEN d.cost_category IN ('Meta', 'Apple Search Ads', 'Tiktok') THEN 'App' ELSE 'Web' END AS traffic_source,
        CASE WHEN d.cost_category IN ('Meta', 'Apple Search Ads') THEN 'iOS'
            WHEN d.cost_category IN ('Tiktok') THEN 'Android' ELSE 'Web' END AS app_platform,
        CAST(d.cost AS DOUBLE) * (CAST(j.volume AS DOUBLE) / CAST(NULLIF(t.volume, 0) AS DOUBLE)) AS split_cost
    FROM ba.marketing_cost_daily d
    LEFT JOIN volume_by_channel_day t
      ON t.date = d.date AND t.cost_category = d.cost_category
    LEFT JOIN volume_by_dim j
      ON t.date = j.date AND t.cost_category = j.cost_category
    WHERE d.cost_category NOT IN ('Google', 'Iterable')
      AND COALESCE(t.volume, 0) > 0
    UNION ALL
    SELECT
        d.date,
        d.cost_category,
        CASE WHEN d.cost_category IN ('clear score', 'lead_market', 'lml', 'overflow', 'wonderloans') THEN 'Lead Partner'
             WHEN d.cost_category = 'Others' THEN 'Organic'
             ELSE d.cost_category
        END AS attributed_category,
        'New' AS application_tag, 'New' AS user_tag,
        CASE WHEN d.cost_category IN ('Meta', 'Apple Search Ads', 'Tiktok') THEN 'App' ELSE 'Web' END AS traffic_source,
        CASE WHEN d.cost_category IN ('Meta', 'Apple Search Ads') THEN 'iOS'
            WHEN d.cost_category IN ('Tiktok') THEN 'Android' ELSE 'Web' END AS app_platform,
        CAST(d.cost AS DOUBLE) AS split_cost
    FROM ba.marketing_cost_daily d
    LEFT JOIN volume_by_channel_day t
      ON t.date = d.date AND t.cost_category = d.cost_category
    WHERE d.cost_category NOT IN ('Google', 'Iterable')
      AND COALESCE(t.volume, 0) = 0
),

-- 3.2 Iterable：user_tag和application_tag用发送量拆，其他维度用volume(applications)拆
iterable_cost_days AS (
    SELECT date, cost FROM ba.marketing_cost_daily WHERE cost_category = 'Iterable'
),
iterable_send_dim AS (
    SELECT launch_week AS week, ls_user_tag AS user_tag, ls_application_tag AS application_tag,
           COUNT(*) AS sends
    FROM ba.iterable_targeting_history
    GROUP BY launch_week, ls_user_tag, ls_application_tag
),
iterable_send_week_total AS (
    SELECT launch_week AS week, COUNT(*) AS sends
    FROM ba.iterable_targeting_history
    GROUP BY launch_week
),
iterable_usertag_apptag_share AS (
    SELECT
        cd.date,
        COALESCE(sd.user_tag, 'New') AS user_tag,
        COALESCE(sd.application_tag, 'New') AS application_tag,
        CAST(cd.cost AS DOUBLE) * (CASE WHEN COALESCE(wt.sends, 0) = 0 THEN CAST(1.0 AS DOUBLE) ELSE CAST(sd.sends AS DOUBLE) / CAST(wt.sends AS DOUBLE) END) AS split_cost
    FROM iterable_cost_days cd
    JOIN ba.date_calendar dc ON dc.date = cd.date
    LEFT JOIN iterable_send_week_total wt ON wt.week = dc.week
    LEFT JOIN iterable_send_dim sd ON sd.week = dc.week
),
iterable_traffic_platform_dim AS (
    SELECT date, user_tag, application_tag, traffic_source, app_platform, SUM(volume) AS volume
    FROM ba.cost_category_daily_volume_count
    WHERE cost_category = 'Iterable'
    GROUP BY 1,2,3,4,5
),
iterable_usertag_apptag_volume_total AS (
    SELECT date, user_tag, application_tag, SUM(volume) AS volume
    FROM ba.cost_category_daily_volume_count
    WHERE cost_category = 'Iterable'
    GROUP BY 1,2,3
),
iterable_split AS (
    SELECT n.date,
        'Iterable' AS cost_category,
        'Owned Channels' AS attributed_category,
        n.user_tag, n.application_tag,
        j.traffic_source, j.app_platform,
        n.split_cost * CAST(j.volume AS DOUBLE) / CAST(t.volume AS DOUBLE) AS split_cost
    FROM iterable_usertag_apptag_share n
    LEFT JOIN iterable_usertag_apptag_volume_total t
      ON t.date = n.date AND t.user_tag = n.user_tag AND t.application_tag = n.application_tag
    LEFT JOIN iterable_traffic_platform_dim j
      ON j.date = n.date AND j.user_tag = n.user_tag AND j.application_tag = n.application_tag
    WHERE COALESCE(t.volume, 0) > 0
    UNION ALL
    SELECT n.date,
        'Iterable' AS cost_category,
        'Owned Channels' AS attributed_category,
        n.user_tag, n.application_tag,
        'Web' AS traffic_source, 'Web' AS app_platform,
        n.split_cost AS split_cost
    FROM iterable_usertag_apptag_share n
    LEFT JOIN iterable_usertag_apptag_volume_total t
      ON t.date = n.date AND t.user_tag = n.user_tag AND t.application_tag = n.application_tag
    WHERE COALESCE(t.volume, 0) = 0
),

-- 3.3 Google：campaign级精确拆分逻辑
google_app_ratio AS (
    SELECT 
        a.date,
        a.attributed_campaign,
        b.application_tag,
        b.user_tag,
        CAST(b.applications AS DOUBLE) / CAST(a.applications AS DOUBLE) AS app_ratio
    FROM 
        (SELECT
            TO_DATE(application_date) AS date,
            attributed_campaign,
            COUNT(application_id) AS applications
        FROM ba.customer_profile_rawdata
        WHERE DATEDIFF(to_date('${yyyy-mm-dd}'), DATE(application_date)) >= 0
        AND attributed_category='Google'
        GROUP BY 1,2) a
    LEFT JOIN
        (SELECT
            TO_DATE(application_date) AS date,
            application_tag,
            user_tag,
            attributed_campaign,
            COUNT(application_id) AS applications
        FROM ba.customer_profile_rawdata
        WHERE DATEDIFF(to_date('${yyyy-mm-dd}'), DATE(application_date)) >= 0
        AND attributed_category='Google'
        GROUP BY 1,2,3,4) b 
    ON a.date=b.date 
    AND a.attributed_campaign=b.attributed_campaign
    
    UNION
    
    SELECT 
        date,
        biz_campaign_name AS attributed_campaign,
        'New' AS application_tag,
        'New' AS user_tag,
        1 AS app_ratio
    FROM 
        (SELECT
            DATE(biz_date) AS date,
            biz_campaign_name,
            SUM(cost) AS cost,
            SUM(application) AS application
        FROM mkt.mkt_imp_clk_cost
        WHERE DATEDIFF(to_date('${yyyy-mm-dd}'), DATE(biz_date)) >= 0
        AND channel = 'google'
        GROUP BY 1,2)
    WHERE cost>0 
    AND application=0
),
-- 每一天Google后台原始花费总数 vs STEP2.5校准后的最终花费总数之间的比例，用这个比例去调整每个campaign的原始花费
google_day_ratio AS (
    SELECT
        s.date,
        CASE WHEN COALESCE(s.raw_day_cost, 0) = 0 THEN NULL ELSE CAST(d.cost AS DOUBLE) / CAST(s.raw_day_cost AS DOUBLE) END AS day_ratio
    FROM ba.marketing_cost_daily d 
    LEFT JOIN 
        (SELECT 
            DATE(biz_date) AS date, 
            SUM(cost) AS raw_day_cost
        FROM mkt.mkt_imp_clk_cost
        WHERE channel = 'google'
        GROUP BY 1) s
      ON d.date = s.date 
    WHERE d.cost_category = 'Google'
),
google_split AS (
    SELECT
        a.date,
        'Google' AS cost_category,
        'Google' AS attributed_category,
        b.application_tag,
        b.user_tag,
        CASE WHEN LOWER(biz_campaign_name) LIKE '%ios%' THEN 'App'
             WHEN LOWER(biz_campaign_name) LIKE '%android%' THEN 'App'
             ELSE 'Web' END AS traffic_source,
        CASE WHEN LOWER(biz_campaign_name) LIKE '%ios%' THEN 'iOS'
             WHEN LOWER(biz_campaign_name) LIKE '%android%' THEN 'Android'
             ELSE 'Web' END AS app_platform,
        SUM(CAST(a.cost AS DOUBLE) * COALESCE(gr.day_ratio, CAST(1.0 AS DOUBLE)) * b.app_ratio) AS split_cost
    FROM
        (SELECT
            DATE(biz_date) AS date,
            biz_campaign_name,
            SUM(cost) AS cost
        FROM mkt.mkt_imp_clk_cost
        WHERE channel = 'google'
        GROUP BY 1,2) a
    LEFT JOIN google_app_ratio b
      ON a.date = b.date
     AND a.biz_campaign_name = b.attributed_campaign
    LEFT JOIN google_day_ratio gr
      ON gr.date = a.date
    GROUP BY 1,2,3,4,5,6,7
)

SELECT date, cost_category, attributed_category, application_tag, user_tag, traffic_source, app_platform,
       ROUND(split_cost, 2) AS split_cost
FROM volume_split
UNION ALL
SELECT date, cost_category, attributed_category, application_tag, user_tag, traffic_source, app_platform,
       ROUND(split_cost, 2) AS split_cost
FROM iterable_split
UNION ALL
SELECT date, cost_category, attributed_category, application_tag, user_tag, traffic_source, app_platform,
       ROUND(split_cost, 2) AS split_cost
FROM google_split
;



-- ============================================================================
-- STEP 4：月度花费 x 放款(含预测)汇总，只保留cost_category/user_tag
-- ============================================================================
DROP TABLE IF EXISTS ba.marketing_cost_actual_split;
CREATE TABLE IF NOT EXISTS ba.marketing_cost_actual_split AS
WITH driver AS (
    SELECT DISTINCT month, cost_category, user_tag
    FROM 
        (SELECT DISTINCT month
        FROM ba.date_calendar
        WHERE date>='2025-07-01')
    FULL JOIN 
        (SELECT DISTINCT cost_category
        FROM ba.marketing_cost_actual_breakdown)
    ON 1=1
    FULL JOIN 
        (SELECT DISTINCT user_tag
        FROM ba.marketing_cost_actual_breakdown)
    ON 1=1
),
cost_split AS (
    SELECT dc.month, b.cost_category, b.user_tag, SUM(b.split_cost) AS split_cost
    FROM ba.marketing_cost_actual_breakdown b
    JOIN ba.date_calendar dc ON dc.date = b.date
    WHERE b.date>='2025-07-01'
    GROUP BY 1,2,3
),
loan_originations AS (
    SELECT
        a.application_date,
        a.month,
        a.cost_category,
        a.user_tag,
        COALESCE(a.applications, 0) AS applications,
        COALESCE(a.loans, 0) AS loans,
        COALESCE(a.originations, 0) AS originations,
        COALESCE(f.pred_funded, 0) AS pred_funded,
        COALESCE(f.pred_funded_amt, 0) AS pred_funded_amt,
        CASE WHEN a.application_date <= date_sub(current_date(), 1) AND a.application_date >= date_sub(current_date(), 14)
                THEN GREATEST(COALESCE(f.pred_funded, 0), COALESCE(a.loans, 0))
            WHEN a.application_date < date_sub(current_date(), 14)
                THEN COALESCE(a.loans, 0)
            END AS funded_final,
        CASE WHEN a.application_date <= date_sub(current_date(), 1) AND a.application_date >= date_sub(current_date(), 14)
                THEN GREATEST(COALESCE(f.pred_funded_amt, 0), COALESCE(a.originations, 0))
            WHEN a.application_date < date_sub(current_date(), 14)
                THEN COALESCE(a.originations, 0)
            END AS funded_amt_final
    FROM
        (SELECT DISTINCT
            application_date,
            application_month AS month,
            cost_category,
            user_tag,
            COUNT(application_id) AS applications,
            COUNT(CASE WHEN application_status = '4.Funded' THEN application_id END) AS loans,
            SUM(CASE WHEN application_status = '4.Funded' THEN total_amount END) AS originations
        FROM ba.customer_profile_rawdata
        WHERE application_date >= '2025-07-01'
        AND application_date <= to_date('${yyyy-mm-dd}')
        GROUP BY 1,2,3,4) a
    LEFT JOIN
        (SELECT
            application_date,
            cost_category,
            user_tag,
            SUM(pred_funded) AS pred_funded,
            SUM(pred_funded_amt) AS pred_funded_amt
        FROM mkt.mkt_t7_cpfl_forecast
        WHERE observe_date = to_date('${yyyy-mm-dd}')
        GROUP BY 1,2,3) f
    ON a.application_date = f.application_date
    AND a.cost_category = f.cost_category
    AND a.user_tag = f.user_tag
)
SELECT d.month,
    d.cost_category,
    d.user_tag,
    a.split_cost,
    b.applications,
    b.loans,
    b.originations,
    b.pred_funded,
    b.pred_funded_amt,
    b.funded_final,
    b.funded_amt_final
FROM driver d
LEFT JOIN cost_split a
ON a.month = d.month
AND a.cost_category = d.cost_category
AND a.user_tag = d.user_tag
LEFT JOIN
    (SELECT
        month,
        cost_category,
        user_tag,
        SUM(applications) AS applications,
        SUM(loans) AS loans,
        SUM(originations) AS originations,
        SUM(pred_funded) AS pred_funded,
        SUM(pred_funded_amt) AS pred_funded_amt,
        SUM(funded_final) AS funded_final,
        SUM(funded_amt_final) AS funded_amt_final
    FROM loan_originations
    GROUP BY 1,2,3) b
ON d.month = b.month
AND d.cost_category = b.cost_category
AND d.user_tag = b.user_tag
WHERE (a.split_cost IS NOT NULL AND a.split_cost > 0)
OR (b.applications IS NOT NULL AND b.applications > 0)
;