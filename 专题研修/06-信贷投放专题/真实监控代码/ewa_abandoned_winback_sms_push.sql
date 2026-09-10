INSERT INTO ba.ewa_abandoned_winback_sms_push
SELECT  
    to_json(
            named_struct('userId',user_id,
                         'marketingCategoryCode','system_common_category',
                         'userTypeCode','ewa_main',
                         'importMethod','HAND_METHOD',
                         'userTypeCategory','ABANDONED_WINBACK',
                         'totalNum',total_num,
                         'attactment',attactment)
    ) as json_output
    ,observe_date as batchNo
FROM
    (SELECT 
        *
        ,COUNT(*) OVER () AS total_num
        ,named_struct('audienceType',audience_type,
                      'reachType',reach_type,
                      'registerTime',register_time,
                      'registerNonApplyLimitTn',register_non_apply_limit_tn,
                      'fstHasLimitTime',fst_has_limit_time,
                      'fstHasLimit',fst_has_limit,
                      'hasLimitNonLoanTn',has_limit_non_loan_tn,
                      'previousLoanApplyTime',previous_loan_apply_time,
                      'previousSettleTime',previous_settle_time,
                      'hasSettledNonReborrowTn',has_settled_non_reborrow_tn,
                      'observeDate',observe_date
            ) AS attactment  -- 千万别写成attachment
    FROM 
        (SELECT 
            user_id  -- 用户id
            ,register_time  -- 注册时间
            ,datediff('${yyyy-mm-dd+1}', register_time) AS register_non_apply_limit_tn  -- 距离注册日的天数
            ,fst_has_limit_time  -- 首次有额时间
            ,fst_has_limit  -- 首次有额额度
            ,NULL AS has_limit_non_loan_tn  -- 距离有额的天数
            ,NULL AS previous_loan_apply_time  -- 上次申请借款时间
            ,NULL AS previous_settle_time  -- 上次结清时间
            ,NULL AS has_settled_non_reborrow_tn  -- 距离结清的天数
            ,'register_non_apply_limit' AS audience_type  -- 注册未戳额
            ,'sms' AS reach_type  -- 触达方式
            ,'${yyyy-mm-dd+1}' AS observe_date
        FROM edw_ewa.dwb_user_fst_conv_dtl
        WHERE fst_apply_limit_time IS NULL
        AND datediff('${yyyy-mm-dd+1}', register_time) IN (1,5,10) -- 限定 T+n
        
        UNION
        
        SELECT 
            user_id  -- 用户id
            ,register_time  -- 注册时间
            ,datediff('${yyyy-mm-dd+1}', register_time) AS register_non_apply_limit_tn  -- 距离注册日的天数
            ,fst_has_limit_time  -- 首次有额时间
            ,fst_has_limit  -- 首次有额额度
            ,datediff('${yyyy-mm-dd+1}', fst_has_limit_time) AS has_limit_non_loan_tn  -- 距离有额的天数
            ,NULL AS previous_loan_apply_time  -- 上次申请借款时间
            ,NULL AS previous_settle_time  -- 上次结清时间
            ,NULL AS has_settled_non_reborrow_tn  -- 距离结清的天数
            ,'has_limit_non_loan' AS audience_type  -- 有额无借款申请
            ,'sms' AS reach_type  -- 触达方式
            ,'${yyyy-mm-dd+1}' AS observe_date
        FROM edw_ewa.dwb_user_fst_conv_dtl
        WHERE fst_has_limit_time IS NOT NULL
        AND fst_apply_loan_time IS NULL
        AND datediff('${yyyy-mm-dd+1}', fst_has_limit_time) IN (1,5,10,53) -- 限定 T+n
        
        UNION 
        
        SELECT 
            a.user_id  -- 用户id
            ,c.register_time  -- 注册时间
            ,datediff('${yyyy-mm-dd+1}', c.register_time) AS register_non_apply_limit_tn  -- 距离注册日的天数
            ,c.fst_has_limit_time  -- 首次有额时间
            ,c.fst_has_limit  -- 首次有额额度
            ,datediff('${yyyy-mm-dd+1}', c.fst_has_limit_time) AS has_limit_non_loan_tn  -- 距离有额的天数
            ,b.previous_loan_apply_time  -- 上次申请借款时间
            ,a.previous_settle_time  -- 上次结清时间
            ,datediff('${yyyy-mm-dd+1}', a.previous_settle_time) AS has_settled_non_reborrow_tn  -- 距离结清的天数
            ,'has_settled_non_reborrow' AS audience_type  -- 结清无复借申请
            ,'sms' AS reach_type  -- 触达方式
            ,'${yyyy-mm-dd+1}' AS observe_date
        FROM 
            (SELECT user_id,
                MAX(repay_time) AS previous_settle_time,
                SUM(owing_principal) AS owing_principal,
                SUM(CASE WHEN debt_status != 2 THEN 1 ELSE 0 END) AS unsettled_debt_cnt
            FROM edw_ewa.dwb_asset_debt_dtl_snp
            WHERE dt='${yyyy-mm-dd+1}'
            GROUP BY user_id
            HAVING MAX(repay_time) IS NOT NULL
             AND SUM(owing_principal) = 0 -- 总未还本金 = 0
             AND SUM(CASE WHEN debt_status != 2 THEN 1 ELSE 0 END) = 0 -- 全部状态为2（没有非结清状态的债务）
            ) a
        LEFT JOIN 
            (SELECT 
                user_id,
                MAX(inserttime) as previous_loan_apply_time
            FROM edw_ewa.dwd_asset_ewa_loan_application
            WHERE isactive=1
            GROUP BY user_id) b
        ON a.user_id=b.user_id
        LEFT JOIN 
            (SELECT 
                user_id  -- 用户id
                ,register_time  -- 注册时间
                ,fst_has_limit_time  -- 首次有额时间
                ,fst_has_limit  -- 首次有额额度
            FROM edw_ewa.dwb_user_fst_conv_dtl) c
        ON a.user_id=c.user_id
        WHERE a.previous_settle_time>b.previous_loan_apply_time -- 结清后未再次申请提款
        AND datediff('${yyyy-mm-dd+1}', a.previous_settle_time) IN (7,21,35) -- 限定 T+n
        )
    WHERE user_id NOT IN 
        (SELECT DISTINCT user_id
        FROM ods.dwd_mkt_iterable_sms_bounce_dtl
        WHERE account_id=31467
        AND error_title='Undeliverable'
        AND user_id IS NOT NULL)
    ) 
;