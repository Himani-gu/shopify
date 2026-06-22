-- ============================================================
-- 03_segment_analysis.sql
-- Revenue breakdown by region, category, segment, and time
-- ============================================================

-- A) Revenue by Region
SELECT
    r.region_name,
    r.country,
    ROUND(SUM(s.revenue), 2)                            AS total_revenue,
    ROUND(SUM(s.profit), 2)                             AS total_profit,
    ROUND(100.0 * SUM(s.profit) / SUM(s.revenue), 2)   AS profit_margin_pct,
    COUNT(DISTINCT s.customer_id)                       AS unique_customers,
    COUNT(DISTINCT s.order_id)                          AS total_orders,
    ROUND(100.0 * SUM(s.revenue) /
        SUM(SUM(s.revenue)) OVER (), 2)                AS revenue_share_pct
FROM sales s
JOIN regions r ON s.region_id = r.region_id
GROUP BY r.region_name, r.country
ORDER BY total_revenue DESC;

-- B) Revenue by Product Category
SELECT
    p.category,
    p.subcategory,
    ROUND(SUM(s.revenue), 2)                            AS total_revenue,
    ROUND(SUM(s.profit), 2)                             AS total_profit,
    ROUND(100.0 * SUM(s.profit) / SUM(s.revenue), 2)   AS profit_margin_pct,
    SUM(s.quantity)                                     AS units_sold,
    COUNT(DISTINCT s.customer_id)                       AS unique_customers,
    ROUND(100.0 * SUM(s.revenue) /
        SUM(SUM(s.revenue)) OVER (), 2)                AS revenue_share_pct
FROM sales s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.category, p.subcategory
ORDER BY total_revenue DESC;

-- C) Revenue by Customer Segment
SELECT
    c.segment,
    ROUND(SUM(s.revenue), 2)                            AS total_revenue,
    ROUND(SUM(s.profit), 2)                             AS total_profit,
    COUNT(DISTINCT s.customer_id)                       AS unique_customers,
    COUNT(DISTINCT s.order_id)                          AS total_orders,
    ROUND(AVG(s.revenue), 2)                            AS avg_order_value,
    ROUND(100.0 * SUM(s.revenue) /
        SUM(SUM(s.revenue)) OVER (), 2)                AS revenue_share_pct
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
GROUP BY c.segment
ORDER BY total_revenue DESC;

-- D) Monthly Revenue Trend
SELECT
    STRFTIME('%Y', order_date)      AS year,
    STRFTIME('%m', order_date)      AS month,
    STRFTIME('%Y-%m', order_date)   AS year_month,
    ROUND(SUM(revenue), 2)          AS monthly_revenue,
    ROUND(SUM(profit), 2)           AS monthly_profit,
    COUNT(DISTINCT customer_id)     AS active_customers,
    COUNT(DISTINCT order_id)        AS total_orders
FROM sales
GROUP BY year_month
ORDER BY year_month;

-- E) Region x Category cross-cut
SELECT
    r.region_name,
    p.category,
    ROUND(SUM(s.revenue), 2)        AS revenue
FROM sales s
JOIN regions  r ON s.region_id  = r.region_id
JOIN products p ON s.product_id = p.product_id
GROUP BY r.region_name, p.category
ORDER BY r.region_name, revenue DESC;