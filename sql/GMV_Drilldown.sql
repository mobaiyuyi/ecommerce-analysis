-- 品类 / 地区下钻：定位 2026-01 → 2026-04 完成订单GMV 下滑的来源
-- 口径与 GMV_Month.sql 保持一致：按订单ID去重，完成GMV 仅计入「已完成」订单金额
-- 方法：加法分解。各维度 ΔGMV 之和 = 总 ΔGMV，贡献占比 = 该维度 ΔGMV / 总 ΔGMV（合计 100%）
-- 说明：窗口函数 SUM(...) OVER () 用于在明细行上直接算出总 ΔGMV，避免再跑一次汇总查询

-- ========== 查询1：商品分类下钻 ==========
WITH base_order AS (
    SELECT DISTINCT `订单ID`, `订单日期`, `订单金额`, `订单状态`, `商品分类`
    FROM sales_data
    WHERE `订单状态` IN ('已完成', '待发货', '已取消', '退款中')
      AND `订单日期` >= '2026-01-01'
      AND `订单日期` <  '2026-05-01'
),
monthly_dim AS (
    SELECT
        `商品分类`                                                    AS 维度值,
        DATE_FORMAT(`订单日期`, '%Y-%m')                              AS 年月,
        SUM(CASE WHEN `订单状态` = '已完成' THEN `订单金额` ELSE 0 END)  AS 完成GMV,
        COUNT(CASE WHEN `订单状态` = '已完成' THEN 1 END)               AS 完成订单数,
        COUNT(*)                                                     AS 总下单量
    FROM base_order
    GROUP BY `商品分类`, DATE_FORMAT(`订单日期`, '%Y-%m')
),
pivot AS (
    SELECT
        维度值,
        SUM(CASE WHEN 年月 = '2026-01' THEN 完成GMV   ELSE 0 END) AS GMV_01,
        SUM(CASE WHEN 年月 = '2026-04' THEN 完成GMV   ELSE 0 END) AS GMV_04,
        SUM(CASE WHEN 年月 = '2026-01' THEN 总下单量   ELSE 0 END) AS 下单量_01,
        SUM(CASE WHEN 年月 = '2026-04' THEN 总下单量   ELSE 0 END) AS 下单量_04,
        SUM(CASE WHEN 年月 = '2026-01' THEN 完成订单数 ELSE 0 END) AS 完成订单数_01,
        SUM(CASE WHEN 年月 = '2026-04' THEN 完成订单数 ELSE 0 END) AS 完成订单数_04
    FROM monthly_dim
    GROUP BY 维度值
)
SELECT
    维度值                                                              AS `商品分类`,
    ROUND(GMV_01, 2)                                                   AS `完成GMV_202601`,
    ROUND(GMV_04, 2)                                                   AS `完成GMV_202604`,
    ROUND(GMV_04 - GMV_01, 2)                                          AS `GMV变化额`,
    ROUND((GMV_04 / NULLIF(GMV_01, 0) - 1) * 100, 2)                    AS `GMV变化率`,
    ROUND((GMV_04 - GMV_01) / NULLIF(SUM(GMV_04 - GMV_01) OVER (), 0) * 100, 2) AS `GMV贡献占比`,
    下单量_04 - 下单量_01                                                AS `下单量变化`,
    ROUND((GMV_04 / NULLIF(完成订单数_04, 0)) / (GMV_01 / NULLIF(完成订单数_01, 0)) - 1, 4) * 100 AS `客单价变化率`
FROM pivot
ORDER BY `GMV变化额` ASC;

-- ========== 查询2：用户所在地区下钻 ==========
WITH base_order AS (
    SELECT DISTINCT `订单ID`, `订单日期`, `订单金额`, `订单状态`, `用户所在地区`
    FROM sales_data
    WHERE `订单状态` IN ('已完成', '待发货', '已取消', '退款中')
      AND `订单日期` >= '2026-01-01'
      AND `订单日期` <  '2026-05-01'
),
monthly_dim AS (
    SELECT
        `用户所在地区`                                                AS 维度值,
        DATE_FORMAT(`订单日期`, '%Y-%m')                              AS 年月,
        SUM(CASE WHEN `订单状态` = '已完成' THEN `订单金额` ELSE 0 END)  AS 完成GMV,
        COUNT(CASE WHEN `订单状态` = '已完成' THEN 1 END)               AS 完成订单数,
        COUNT(*)                                                     AS 总下单量
    FROM base_order
    GROUP BY `用户所在地区`, DATE_FORMAT(`订单日期`, '%Y-%m')
),
pivot AS (
    SELECT
        维度值,
        SUM(CASE WHEN 年月 = '2026-01' THEN 完成GMV   ELSE 0 END) AS GMV_01,
        SUM(CASE WHEN 年月 = '2026-04' THEN 完成GMV   ELSE 0 END) AS GMV_04,
        SUM(CASE WHEN 年月 = '2026-01' THEN 总下单量   ELSE 0 END) AS 下单量_01,
        SUM(CASE WHEN 年月 = '2026-04' THEN 总下单量   ELSE 0 END) AS 下单量_04,
        SUM(CASE WHEN 年月 = '2026-01' THEN 完成订单数 ELSE 0 END) AS 完成订单数_01,
        SUM(CASE WHEN 年月 = '2026-04' THEN 完成订单数 ELSE 0 END) AS 完成订单数_04
    FROM monthly_dim
    GROUP BY 维度值
)
SELECT
    维度值                                                              AS `用户所在地区`,
    ROUND(GMV_01, 2)                                                   AS `完成GMV_202601`,
    ROUND(GMV_04, 2)                                                   AS `完成GMV_202604`,
    ROUND(GMV_04 - GMV_01, 2)                                          AS `GMV变化额`,
    ROUND((GMV_04 / NULLIF(GMV_01, 0) - 1) * 100, 2)                    AS `GMV变化率`,
    ROUND((GMV_04 - GMV_01) / NULLIF(SUM(GMV_04 - GMV_01) OVER (), 0) * 100, 2) AS `GMV贡献占比`,
    下单量_04 - 下单量_01                                                AS `下单量变化`,
    ROUND((GMV_04 / NULLIF(完成订单数_04, 0)) / (GMV_01 / NULLIF(完成订单数_01, 0)) - 1, 4) * 100 AS `客单价变化率`
FROM pivot
ORDER BY `GMV变化额` ASC;