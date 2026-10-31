-- =====================================================
-- Campus Coffee Shop - Step 3: Business Questions
-- Run ONE query at a time: click inside it, press Ctrl + Enter
-- =====================================================

USE coffee_shop;


-- =====================================================
-- SECTION A: SALES PERFORMANCE
-- =====================================================

-- Q1. How is the business doing overall?
--     Total revenue, number of orders, and average order value
SELECT
    COUNT(DISTINCT o.order_id)                              AS total_orders,
    ROUND(SUM(oi.quantity * oi.unit_price), 2)              AS total_revenue,
    ROUND(SUM(oi.quantity * oi.unit_price)
          / COUNT(DISTINCT o.order_id), 2)                  AS avg_order_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id;


-- Q2. What are our top 5 best-selling products by revenue?
SELECT
    p.product_name,
    SUM(oi.quantity)                            AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price), 2)  AS revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_id, p.product_name
ORDER BY revenue DESC
LIMIT 5;


-- Q3. Which product categories make the most profit?
--     (revenue minus what it costs us to make each item)
SELECT
    p.category,
    ROUND(SUM(oi.quantity * oi.unit_price), 2)             AS revenue,
    ROUND(SUM(oi.quantity * p.cost), 2)                    AS cost,
    ROUND(SUM(oi.quantity * (oi.unit_price - p.cost)), 2)  AS profit,
    ROUND(100 * SUM(oi.quantity * (oi.unit_price - p.cost))
              / SUM(oi.quantity * oi.unit_price), 1)       AS profit_margin_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY profit DESC;


-- Q4. How are weekly sales trending?
SELECT
    MIN(DATE(o.order_datetime))                 AS week_starting,
    COUNT(DISTINCT o.order_id)                  AS orders,
    ROUND(SUM(oi.quantity * oi.unit_price), 2)  AS revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY YEARWEEK(o.order_datetime, 1)
ORDER BY week_starting;


-- =====================================================
-- SECTION B: OPERATIONS & STAFFING
-- =====================================================

-- Q5. What are our busiest hours? (helps plan staff shifts)
SELECT
    HOUR(order_datetime)  AS hour_of_day,
    COUNT(*)              AS orders
FROM orders
GROUP BY HOUR(order_datetime)
ORDER BY hour_of_day;


-- Q6. Which days of the week are busiest?
SELECT
    DAYNAME(o.order_datetime)                   AS day_of_week,
    COUNT(DISTINCT o.order_id)                  AS orders,
    ROUND(SUM(oi.quantity * oi.unit_price), 2)  AS revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY DAYOFWEEK(o.order_datetime), DAYNAME(o.order_datetime)
ORDER BY DAYOFWEEK(o.order_datetime);


-- Q7. How is each employee performing?
SELECT
    CONCAT(e.first_name, ' ', e.last_name)      AS employee,
    e.role,
    COUNT(DISTINCT o.order_id)                  AS orders_handled,
    ROUND(SUM(oi.quantity * oi.unit_price), 2)  AS revenue_handled
FROM employees e
JOIN orders o       ON e.employee_id = o.employee_id
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY e.employee_id, e.first_name, e.last_name, e.role
ORDER BY revenue_handled DESC;


-- Q8. Which products are low in stock and need to be reordered?
SELECT
    p.product_name,
    i.quantity_on_hand,
    i.reorder_level,
    i.reorder_level - i.quantity_on_hand  AS units_below_reorder
FROM inventory i
JOIN products p ON i.product_id = p.product_id
WHERE i.quantity_on_hand < i.reorder_level
ORDER BY units_below_reorder DESC;


-- =====================================================
-- SECTION C: CUSTOMERS
-- =====================================================

-- Q9. Do loyalty members spend more per visit than walk-ins?
--     (uses a CTE: first total each order, then compare groups)
WITH order_totals AS (
    SELECT
        o.order_id,
        o.customer_id,
        SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY o.order_id, o.customer_id
)
SELECT
    CASE WHEN customer_id IS NULL THEN 'Walk-in'
         ELSE 'Loyalty member' END   AS customer_type,
    COUNT(*)                         AS orders,
    ROUND(AVG(order_total), 2)       AS avg_order_value
FROM order_totals
GROUP BY customer_type;


-- Q10. Who are our top 5 most valuable loyalty members?
SELECT
    CONCAT(c.first_name, ' ', c.last_name)      AS customer,
    COUNT(DISTINCT o.order_id)                  AS visits,
    ROUND(SUM(oi.quantity * oi.unit_price), 2)  AS total_spent,
    MAX(DATE(o.order_datetime))                 AS last_visit
FROM customers c
JOIN orders o       ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY total_spent DESC
LIMIT 5;


-- Q11. How do customers prefer to pay?
SELECT
    payment_method,
    COUNT(*)                                            AS orders,
    ROUND(100 * COUNT(*) / (SELECT COUNT(*) FROM orders), 1)  AS pct_of_orders
FROM orders
GROUP BY payment_method
ORDER BY orders DESC;


-- Q12. Which products are most often bought together?
--      (useful for combo deals, e.g. "Latte + Muffin")
SELECT
    p1.product_name  AS product_a,
    p2.product_name  AS product_b,
    COUNT(*)         AS times_bought_together
FROM order_items a
JOIN order_items b  ON a.order_id = b.order_id
                   AND a.product_id < b.product_id   -- avoids duplicate pairs
JOIN products p1    ON a.product_id = p1.product_id
JOIN products p2    ON b.product_id = p2.product_id
GROUP BY p1.product_name, p2.product_name
ORDER BY times_bought_together DESC
LIMIT 5;


-- =====================================================
-- SECTION D: REUSABLE VIEW
-- =====================================================

-- Q13. Create a view so daily sales can be pulled with one line.
--      The Python report in Step 4 will use this.
CREATE OR REPLACE VIEW daily_sales AS
SELECT
    DATE(o.order_datetime)                      AS sale_date,
    COUNT(DISTINCT o.order_id)                  AS orders,
    ROUND(SUM(oi.quantity * oi.unit_price), 2)  AS revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY DATE(o.order_datetime);

-- Try it:
SELECT * FROM daily_sales ORDER BY sale_date DESC LIMIT 7;
