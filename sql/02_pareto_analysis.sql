-- ============================================================
-- 02_pareto_analysis.sql
-- 80/20 revenue concentration analysis by customer
-- ============================================================

WITH customer_revenue AS (
    SELECT
        s.customer_id,
        c.customer_name,
        c.region,
        c.segment,
        ROUND(SUM(s.revenue), 2)        AS total_revenue,
        COUNT(DISTINCT s.order_id)      AS total_orders,
        ROUND(AVG(s.revenue), 2)        AS avg_order_value
    FROM sales s
    JOIN customers c ON s.customer_id = c.customer_id
    GROUP BY s.customer_id, c.customer_name, c.region, c.segment
),
ranked AS (
    SELECT *,
        RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank,
        SUM(total_revenue) OVER ()                AS grand_total
    FROM customer_revenue
),
cumulative AS (
    SELECT *,
        SUM(total_revenue) OVER (
            ORDER BY total_revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_revenue,
        ROUND(100.0 * SUM(total_revenue) OVER (
            ORDER BY total_revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) / grand_total, 2) AS cumulative_pct,
        ROUND(100.0 * total_revenue / grand_total, 2) AS revenue_share_pct
    FROM ranked
)
SELECT
    revenue_rank,
    customer_id,
    customer_name,
    region,
    segment,
    total_revenue,
    revenue_share_pct,
    cumulative_revenue,
    cumulative_pct,
    total_orders,
    avg_order_value,
    CASE
        WHEN cumulative_pct <= 80 THEN 'Top 80%'
        ELSE 'Remaining 20%'
    END AS pareto_band
FROM cumulative
ORDER BY revenue_rank;

-- Summary: how many customers make up 80% of revenue?
WITH customer_revenue AS (
    SELECT customer_id, SUM(revenue) AS rev
    FROM sales
    GROUP BY customer_id
),
totals AS (SELECT SUM(rev) AS grand_total FROM customer_revenue),
ranked AS (
    SELECT rev, grand_total,
        ROUND(100.0 * SUM(rev) OVER (
            ORDER BY rev DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) / grand_total, 2) AS cumulative_pct
    FROM customer_revenue CROSS JOIN totals
)
SELECT
    COUNT(*)                                            AS customers_in_top_80pct,
    (SELECT COUNT(*) FROM customer_revenue)             AS total_customers,
    ROUND(100.0 * COUNT(*) /
        (SELECT COUNT(*) FROM customer_revenue), 2)    AS pct_of_customer_base,
    ROUND(SUM(rev), 2)                                 AS revenue_they_generate,
    ROUND(AVG(rev), 2)                                 AS avg_revenue_per_customer
FROM ranked
WHERE cumulative_pct <= 80;