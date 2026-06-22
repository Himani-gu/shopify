-- ============================================================
-- 07_salesperson_targets.sql
-- Salesperson actual vs target performance analysis
-- ============================================================

-- A) Full salesperson performance scorecard
SELECT
    sp.employee_id,
    sp.salesperson_name,
    sp.title,
    ROUND(SUM(s.revenue), 2)                            AS actual_revenue,
    ROUND(SUM(s.profit), 2)                             AS actual_profit,
    ROUND(100.0 * SUM(s.profit) / SUM(s.revenue), 2)   AS profit_margin_pct,
    COUNT(DISTINCT s.order_id)                          AS total_orders,
    COUNT(DISTINCT s.customer_id)                       AS unique_customers,
    ROUND(AVG(s.revenue), 2)                            AS avg_order_value,
    ROUND(100.0 * SUM(s.revenue) /
        SUM(SUM(s.revenue)) OVER (), 2)                AS revenue_share_pct,
    CASE
        WHEN 100.0 * SUM(s.profit) / SUM(s.revenue) >= 5  THEN 'Top Performer'
        WHEN 100.0 * SUM(s.profit) / SUM(s.revenue) >= 0  THEN 'On Track'
        ELSE                                                    'Needs Review'
    END AS performance_status
FROM sales s
JOIN salespersons sp ON s.employee_id = sp.employee_id
GROUP BY sp.employee_id, sp.salesperson_name, sp.title
ORDER BY actual_revenue DESC;


-- B) Salesperson vs company average benchmark
WITH sp_performance AS (
    SELECT
        sp.salesperson_name,
        ROUND(SUM(s.revenue), 2)    AS actual_revenue,
        ROUND(AVG(s.revenue), 2)    AS avg_order_value,
        COUNT(DISTINCT s.order_id)  AS total_orders
    FROM sales s
    JOIN salespersons sp ON s.employee_id = sp.employee_id
    GROUP BY sp.salesperson_name
),
company_avg AS (
    SELECT
        ROUND(AVG(actual_revenue), 2)   AS avg_revenue,
        ROUND(AVG(avg_order_value), 2)  AS avg_order_val,
        ROUND(AVG(total_orders), 1)     AS avg_orders
    FROM sp_performance
)
SELECT
    sp.salesperson_name,
    sp.actual_revenue,
    ca.avg_revenue                                      AS company_avg_revenue,
    ROUND(sp.actual_revenue - ca.avg_revenue, 2)        AS vs_avg_revenue,
    ROUND(100.0 * (sp.actual_revenue - ca.avg_revenue)
        / ca.avg_revenue, 2)                            AS pct_above_avg,
    sp.total_orders,
    ca.avg_orders                                       AS company_avg_orders,
    CASE
        WHEN sp.actual_revenue > ca.avg_revenue THEN 'Above Average'
        ELSE                                           'Below Average'
    END AS vs_benchmark
FROM sp_performance sp
CROSS JOIN company_avg ca
ORDER BY sp.actual_revenue DESC;


-- C) Salesperson performance by region
SELECT
    sp.salesperson_name,
    r.region_name,
    r.country,
    ROUND(SUM(s.revenue), 2)                            AS revenue,
    ROUND(SUM(s.profit), 2)                             AS profit,
    COUNT(DISTINCT s.order_id)                          AS orders,
    COUNT(DISTINCT s.customer_id)                       AS customers
FROM sales s
JOIN salespersons sp ON s.employee_id = sp.employee_id
JOIN regions r       ON s.region_id   = r.region_id
GROUP BY sp.salesperson_name, r.region_name, r.country
ORDER BY sp.salesperson_name, revenue DESC;


-- D) Actual vs Target (using Targets table)
SELECT
    sp.salesperson_name,
    ROUND(SUM(s.revenue), 2)        AS actual_revenue,
    ROUND(SUM(t.TargetAmount), 2)   AS target_revenue,
    ROUND(SUM(s.revenue) -
        SUM(t.TargetAmount), 2)     AS variance,
    ROUND(100.0 * SUM(s.revenue) /
        NULLIF(SUM(t.TargetAmount), 0), 2) AS achievement_pct,
    CASE
        WHEN 100.0 * SUM(s.revenue) /
            NULLIF(SUM(t.TargetAmount), 0) >= 100 THEN 'Target Met'
        WHEN 100.0 * SUM(s.revenue) /
            NULLIF(SUM(t.TargetAmount), 0) >= 80  THEN 'Near Target'
        ELSE                                           'Below Target'
    END AS target_status
FROM sales s
JOIN salespersons sp ON s.employee_id  = sp.employee_id
LEFT JOIN Targets t  ON sp.employee_id = t.EmployeeID
GROUP BY sp.salesperson_name
ORDER BY achievement_pct DESC;


-- E) Monthly performance trend per salesperson
SELECT
    sp.salesperson_name,
    STRFTIME('%Y', s.order_date)    AS year,
    STRFTIME('%m', s.order_date)    AS month,
    STRFTIME('%Y-%m', s.order_date) AS year_month,
    ROUND(SUM(s.revenue), 2)        AS monthly_revenue,
    COUNT(DISTINCT s.order_id)      AS monthly_orders
FROM sales s
JOIN salespersons sp ON s.employee_id = sp.employee_id
GROUP BY sp.salesperson_name, year_month
ORDER BY sp.salesperson_name, year_month;