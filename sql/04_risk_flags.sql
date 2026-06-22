-- ============================================================
-- 04_risk_flags.sql
-- Flags high-dependency customers and concentration risks
-- ============================================================

-- A) High-dependency customers (>= 2% of total revenue)
WITH customer_revenue AS (
    SELECT
        s.customer_id,
        c.customer_name,
        c.region,
        c.segment,
        ROUND(SUM(s.revenue), 2)        AS total_revenue,
        COUNT(DISTINCT s.order_id)      AS total_orders
    FROM sales s
    JOIN customers c ON s.customer_id = c.customer_id
    GROUP BY s.customer_id, c.customer_name, c.region, c.segment
),
totals AS (SELECT SUM(total_revenue) AS grand_total FROM customer_revenue)
SELECT
    cr.customer_id,
    cr.customer_name,
    cr.region,
    cr.segment,
    cr.total_revenue,
    cr.total_orders,
    ROUND(100.0 * cr.total_revenue / t.grand_total, 2)  AS revenue_share_pct,
    CASE
        WHEN 100.0 * cr.total_revenue / t.grand_total >= 10 THEN 'CRITICAL  (>=10%)'
        WHEN 100.0 * cr.total_revenue / t.grand_total >= 5  THEN 'HIGH      (>=5%)'
        ELSE                                                     'MODERATE  (>=2%)'
    END AS risk_level
FROM customer_revenue cr
CROSS JOIN totals t
WHERE 100.0 * cr.total_revenue / t.grand_total >= 2
ORDER BY revenue_share_pct DESC;

-- B) Single-customer regional dominance (> 50% of region revenue)
WITH regional_customer AS (
    SELECT
        r.region_name,
        c.customer_name,
        ROUND(SUM(s.revenue), 2)    AS customer_regional_revenue
    FROM sales s
    JOIN customers c ON s.customer_id = c.customer_id
    JOIN regions   r ON s.region_id   = r.region_id
    GROUP BY r.region_name, c.customer_name
),
regional_total AS (
    SELECT region_name, SUM(customer_regional_revenue) AS total_regional_revenue
    FROM regional_customer
    GROUP BY region_name
)
SELECT
    rc.region_name,
    rc.customer_name,
    rc.customer_regional_revenue,
    rt.total_regional_revenue,
    ROUND(100.0 * rc.customer_regional_revenue / rt.total_regional_revenue, 2) AS regional_share_pct,
    'Single customer dominance' AS risk_type
FROM regional_customer rc
JOIN regional_total rt ON rc.region_name = rt.region_name
WHERE 100.0 * rc.customer_regional_revenue / rt.total_regional_revenue > 50
ORDER BY regional_share_pct DESC;

-- C) Category over-reliance (one customer > 40% of category revenue)
WITH cat_customer AS (
    SELECT
        p.category,
        c.customer_name,
        ROUND(SUM(s.revenue), 2)    AS revenue
    FROM sales s
    JOIN products  p ON s.product_id  = p.product_id
    JOIN customers c ON s.customer_id = c.customer_id
    GROUP BY p.category, c.customer_name
),
cat_total AS (
    SELECT category, SUM(revenue) AS total FROM cat_customer GROUP BY category
)
SELECT
    cc.category,
    cc.customer_name,
    cc.revenue                              AS customer_category_revenue,
    ct.total                                AS total_category_revenue,
    ROUND(100.0 * cc.revenue / ct.total, 2) AS category_share_pct,
    'Category over-reliance'                AS risk_type
FROM cat_customer cc
JOIN cat_total ct ON cc.category = ct.category
WHERE 100.0 * cc.revenue / ct.total > 40
ORDER BY category_share_pct DESC;

-- D) Overall concentration scorecard
WITH customer_revenue AS (
    SELECT customer_id, SUM(revenue) AS rev
    FROM sales
    GROUP BY customer_id
),
totals AS (SELECT SUM(rev) AS grand_total FROM customer_revenue),
ranked AS (
    SELECT rev, grand_total,
        SUM(rev) OVER (ORDER BY rev DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_rev
    FROM customer_revenue CROSS JOIN totals
)
SELECT
    (SELECT COUNT(*) FROM customer_revenue)                     AS total_customers,
    (SELECT COUNT(*) FROM ranked WHERE cum_rev <= grand_total * 0.80) AS customers_driving_80pct,
    ROUND(100.0 *
        (SELECT COUNT(*) FROM ranked WHERE cum_rev <= grand_total * 0.80) /
        (SELECT COUNT(*) FROM customer_revenue), 2)            AS pct_of_base_for_80pct,
    (SELECT COUNT(*) FROM ranked
        WHERE 100.0 * rev / grand_total >= 5)                  AS critical_dependency_count,
    ROUND(
        COALESCE((SELECT SUM(rev) FROM ranked
            WHERE 100.0 * rev / grand_total >= 5), 0) /
        (SELECT grand_total FROM totals) * 100, 2)             AS pct_revenue_at_critical_risk;