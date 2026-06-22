-- ============================================================
-- 05_customer_cohort.sql
-- Repeat vs one-time buyer analysis
-- Identifies loyal customers vs single-purchase customers
-- ============================================================

-- A) Customer purchase frequency segmentation
WITH customer_orders AS (
    SELECT
        s.customer_id,
        c.customer_name,
        c.segment,
        c.region,
        COUNT(DISTINCT s.order_id)      AS total_orders,
        ROUND(SUM(s.revenue), 2)        AS total_revenue,
        ROUND(AVG(s.revenue), 2)        AS avg_order_value,
        MIN(s.order_date)               AS first_order_date,
        MAX(s.order_date)               AS last_order_date
    FROM sales s
    JOIN customers c ON s.customer_id = c.customer_id
    GROUP BY s.customer_id, c.customer_name, c.segment, c.region
)
SELECT
    customer_id,
    customer_name,
    segment,
    region,
    total_orders,
    total_revenue,
    avg_order_value,
    first_order_date,
    last_order_date,
    CASE
        WHEN total_orders = 1  THEN 'One-Time Buyer'
        WHEN total_orders <= 3 THEN 'Occasional Buyer'
        WHEN total_orders <= 7 THEN 'Regular Buyer'
        ELSE                        'Loyal Buyer'
    END AS buyer_type,
    CASE
        WHEN total_revenue >= 500000 THEN 'Platinum'
        WHEN total_revenue >= 200000 THEN 'Gold'
        WHEN total_revenue >= 50000  THEN 'Silver'
        ELSE                              'Bronze'
    END AS revenue_tier
FROM customer_orders
ORDER BY total_revenue DESC;


-- B) Cohort summary — how many in each buyer type?
WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(revenue)             AS total_revenue
    FROM sales
    GROUP BY customer_id
),
segmented AS (
    SELECT *,
        CASE
            WHEN total_orders = 1  THEN 'One-Time Buyer'
            WHEN total_orders <= 3 THEN 'Occasional Buyer'
            WHEN total_orders <= 7 THEN 'Regular Buyer'
            ELSE                        'Loyal Buyer'
        END AS buyer_type
    FROM customer_orders
)
SELECT
    buyer_type,
    COUNT(*)                                            AS customer_count,
    ROUND(100.0 * COUNT(*) /
        SUM(COUNT(*)) OVER (), 2)                      AS pct_of_customers,
    ROUND(SUM(total_revenue), 2)                       AS total_revenue,
    ROUND(100.0 * SUM(total_revenue) /
        SUM(SUM(total_revenue)) OVER (), 2)            AS pct_of_revenue,
    ROUND(AVG(total_revenue), 2)                       AS avg_revenue_per_customer,
    ROUND(AVG(total_orders), 1)                        AS avg_orders
FROM segmented
GROUP BY buyer_type
ORDER BY avg_orders DESC;


-- C) Revenue tier summary
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(revenue) AS total_revenue
    FROM sales
    GROUP BY customer_id
),
tiered AS (
    SELECT *,
        CASE
            WHEN total_revenue >= 500000 THEN 'Platinum'
            WHEN total_revenue >= 200000 THEN 'Gold'
            WHEN total_revenue >= 50000  THEN 'Silver'
            ELSE                              'Bronze'
        END AS revenue_tier
    FROM customer_revenue
)
SELECT
    revenue_tier,
    COUNT(*)                                            AS customer_count,
    ROUND(SUM(total_revenue), 2)                       AS total_revenue,
    ROUND(100.0 * SUM(total_revenue) /
        SUM(SUM(total_revenue)) OVER (), 2)            AS pct_of_revenue,
    ROUND(AVG(total_revenue), 2)                       AS avg_revenue
FROM tiered
GROUP BY revenue_tier
ORDER BY avg_revenue DESC;


-- D) First purchase year cohort — retention by year
WITH customer_first_year AS (
    SELECT
        customer_id,
        STRFTIME('%Y', MIN(order_date)) AS first_year
    FROM sales
    GROUP BY customer_id
),
customer_yearly AS (
    SELECT
        s.customer_id,
        STRFTIME('%Y', s.order_date)    AS order_year,
        ROUND(SUM(s.revenue), 2)        AS yearly_revenue
    FROM sales s
    GROUP BY s.customer_id, order_year
)
SELECT
    cf.first_year                       AS cohort_year,
    cy.order_year                       AS active_year,
    COUNT(DISTINCT cy.customer_id)      AS active_customers,
    ROUND(SUM(cy.yearly_revenue), 2)    AS cohort_revenue
FROM customer_first_year cf
JOIN customer_yearly cy ON cf.customer_id = cy.customer_id
GROUP BY cf.first_year, cy.order_year
ORDER BY cf.first_year, cy.order_year;