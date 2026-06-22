-- ============================================================
-- 01_create_tables.sql
-- Creates core tables for revenue concentration analysis
-- Database: adventureworks.db (SQLite)
-- ============================================================

DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS regions;
DROP TABLE IF EXISTS salespersons;

CREATE TABLE products (
    product_id    TEXT PRIMARY KEY,
    product_name  TEXT,
    category      TEXT,
    subcategory   TEXT,
    unit_cost     REAL,
    color         TEXT
);

CREATE TABLE regions (
    region_id    TEXT PRIMARY KEY,
    region_name  TEXT,
    country      TEXT,
    territory    TEXT
);

CREATE TABLE customers (
    customer_id   TEXT PRIMARY KEY,
    customer_name TEXT,
    segment       TEXT,
    city          TEXT,
    state         TEXT,
    region        TEXT
);

CREATE TABLE salespersons (
    employee_id       TEXT PRIMARY KEY,
    employee_code     TEXT,
    salesperson_name  TEXT,
    title             TEXT,
    email             TEXT
);

CREATE TABLE sales (
    order_id     TEXT,
    order_date   TEXT,
    product_id   TEXT,
    customer_id  TEXT,
    employee_id  TEXT,
    region_id    TEXT,
    quantity     REAL,
    unit_price   REAL,
    revenue      REAL,
    cost         REAL,
    profit       REAL,
    FOREIGN KEY (product_id)  REFERENCES products(product_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (region_id)   REFERENCES regions(region_id),
    FOREIGN KEY (employee_id) REFERENCES salespersons(employee_id)
);

CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_product  ON sales(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_region   ON sales(region_id);
CREATE INDEX IF NOT EXISTS idx_sales_date     ON sales(order_date);

SELECT 'Tables created successfully' AS status;