-- 月度核心指标（2025-06 ~ 2026-05），`订单日期` 已由 etl.py 以 DATETIME 类型入库

WITH base_order AS (
    SELECT
        `订单ID`, `订单日期`, `订单金额`, `订单状态`, `是否促销`
    FROM sales_data
    WHERE `订单状态` IN ('已完成', '待发货', '已取消', '退款中')
      AND `订单日期` >= '2025-06-01'
      AND `订单日期` <  '2026-06-01'
),
distinct_order AS (
    SELECT DISTINCT `订单ID`, `订单日期`, `订单金额`, `订单状态`, `是否促销`
    FROM base_order
),
monthly AS (
    SELECT
        DATE_FORMAT(`订单日期`, '%Y-%m')                                AS 年月,
        SUM(CASE WHEN `订单状态` = '已完成' THEN `订单金额` ELSE 0 END)    AS 完成GMV,
        COUNT(CASE WHEN `订单状态` = '已完成' THEN 1 END)                 AS 完成订单数,
        COUNT(*)                                                        AS 总下单量,
        COUNT(CASE WHEN `订单状态` = '待发货' THEN 1 END)                 AS 待发货订单数,
        COUNT(CASE WHEN `订单状态` = '已取消' THEN 1 END)                 AS 已取消订单数,
        COUNT(CASE WHEN `订单状态` = '退款中' THEN 1 END)                 AS 退款中订单数,
        COUNT(CASE WHEN `订单状态` = '已完成' AND `是否促销` = 1 THEN 1 END) AS 完成促销订单数
    FROM distinct_order
    GROUP BY DATE_FORMAT(`订单日期`, '%Y-%m')
)
SELECT
    年月,
    ROUND(完成GMV, 2)                                        AS `完成订单GMV`,
    总下单量                                                  AS `总下单量`,
    ROUND(完成订单数 / NULLIF(总下单量, 0) * 100, 2)           AS `商品交易成功率`,
    ROUND(完成GMV / NULLIF(完成订单数, 0), 2)                 AS `客单价`,
    ROUND(完成促销订单数 / NULLIF(完成订单数, 0) * 100, 2)     AS `完成订单促销率`
FROM monthly
ORDER BY 年月 ASC;