-- ============================================================
-- 06_product_performance.sql
-- Best and worst performing products analysis
-- ============================================================

-- A) Full product performance scorecard
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.subcategory,
    p.color,
    ROUND(SUM(s.revenue), 2)                            AS total_revenue,
    ROUND(SUM(s.profit), 2)                             AS total_profit,
    ROUND(SUM(s.cost), 2)                               AS total_cost,
    SUM(s.quantity)                                     AS units_sold,
    COUNT(DISTINCT s.order_id)                          AS total_orders,
    COUNT(DISTINCT s.customer_id)                       AS unique_customers,
    ROUND(AVG(s.unit_price), 2)                         AS avg_selling_price,
    ROUND(p.unit_cost, 2)                               AS unit_cost,
    ROUND(100.0 * SUM(s.profit) / SUM(s.revenue), 2)   AS profit_margin_pct,
    ROUND(100.0 * SUM(s.revenue) /
        SUM(SUM(s.revenue)) OVER (), 2)                AS revenue_share_pct,
    CASE
        WHEN 100.0 * SUM(s.profit) / SUM(s.revenue) >= 20 THEN 'High Margin'
        WHEN 100.0 * SUM(s.profit) / SUM(s.revenue) >= 5  THEN 'Medium Margin'
        WHEN 100.0 * SUM(s.profit) / SUM(s.revenue) >= 0  THEN 'Low Margin'
        ELSE                                                    'Loss Making'
    END AS margin_category
FROM sales s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category,
         p.subcategory, p.color, p.unit_cost
ORDER BY total_revenue DESC;


-- B) Top 10 best performing products
SELECT
    p.product_name,
    p.category,
    p.subcategory,
    ROUND(SUM(s.revenue), 2)                            AS total_revenue,
    ROUND(SUM(s.profit), 2)                             AS total_profit,
    ROUND(100.0 * SUM(s.profit) / SUM(s.revenue), 2)   AS profit_margin_pct,
    SUM(s.quantity)                                     AS units_sold,
    COUNT(DISTINCT s.customer_id)                       AS unique_customers
FROM sales s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.product_name, p.category, p.subcategory
ORDER BY total_revenue DESC
LIMIT 10;


-- C) Bottom 10 worst performing products
SELECT
    p.product_name,
    p.category,
    p.subcategory,
    ROUND(SUM(s.revenue), 2)                            AS total_revenue,
    ROUND(SUM(s.profit), 2)                             AS total_profit,
    ROUND(100.0 * SUM(s.profit) / SUM(s.revenue), 2)   AS profit_margin_pct,
    SUM(s.quantity)                                     AS units_sold,
    COUNT(DISTINCT s.customer_id)                       AS unique_customers
FROM sales s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.product_name, p.category, p.subcategory
ORDER BY total_revenue ASC
LIMIT 10;


-- D) Loss making products (negative profit margin)
SELECT
    p.product_name,
    p.category,
    p.subcategory,
    ROUND(SUM(s.revenue), 2)                            AS total_revenue,
    ROUND(SUM(s.profit), 2)                             AS total_profit,
    ROUND(100.0 * SUM(s.profit) / SUM(s.revenue), 2)   AS profit_margin_pct,
    SUM(s.quantity)                                     AS units_sold,
    'REVIEW PRICING'                                    AS recommendation
FROM sales s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.product_name, p.category, p.subcategory
HAVING profit_margin_pct < 0
ORDER BY profit_margin_pct ASC;


-- E) Revenue by category and subcategory with rankings
WITH cat_revenue AS (
    SELECT
        p.category,
        p.subcategory,
        ROUND(SUM(s.revenue), 2)    AS revenue,
        ROUND(SUM(s.profit), 2)     AS profit,
        SUM(s.quantity)             AS units
    FROM sales s
    JOIN products p ON s.product_id = p.product_id
    GROUP BY p.category, p.subcategory
)
SELECT
    category,
    subcategory,
    revenue,
    profit,
    units,
    ROUND(100.0 * profit / revenue, 2)              AS margin_pct,
    RANK() OVER (
        PARTITION BY category ORDER BY revenue DESC
    )                                               AS rank_in_category,
    ROUND(100.0 * revenue /
        SUM(revenue) OVER (PARTITION BY category), 2) AS pct_of_category
FROM cat_revenue
ORDER BY category, revenue DESC;