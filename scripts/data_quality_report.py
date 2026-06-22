"""
data_quality_report.py
----------------------
Generates a data quality summary report
and saves it to outputs/data_quality_report.md

Usage:
    python scripts/data_quality_report.py
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "adventureworks.db"
OUT     = ROOT / "outputs" / "data_quality_report.md"

conn = sqlite3.connect(DB_PATH)

print("Running data quality checks...")

checks = {}

# ── Null checks ───────────────────────────────────────────────
null_checks = [
    ("sales",        "revenue"),
    ("sales",        "customer_id"),
    ("sales",        "product_id"),
    ("sales",        "order_date"),
    ("customers",    "customer_name"),
    ("customers",    "segment"),
    ("products",     "category"),
    ("products",     "unit_cost"),
    ("regions",      "region_name"),
    ("salespersons", "salesperson_name"),
]

for table, col in null_checks:
    result = pd.read_sql(
        f"SELECT COUNT(*) as nulls FROM {table} WHERE {col} IS NULL", conn
    )
    checks[f"{table}.{col} nulls"] = {
        "value":  result["nulls"][0],
        "type":   "null"
    }

# ── Duplicate checks ──────────────────────────────────────────
dup_sales = pd.read_sql("""
    SELECT COUNT(*) - COUNT(DISTINCT order_id || '-' || customer_id || '-' || product_id) 
    AS dupes FROM sales
""", conn)
checks["sales logical duplicates"] = {
    "value": dup_sales["dupes"][0],
    "type":  "duplicate"
}

dup_customers = pd.read_sql("""
    SELECT COUNT(*) - COUNT(DISTINCT customer_id) AS dupes FROM customers
""", conn)
checks["customers duplicate IDs"] = {
    "value": dup_customers["dupes"][0],
    "type":  "duplicate"
}

dup_products = pd.read_sql("""
    SELECT COUNT(*) - COUNT(DISTINCT product_id) AS dupes FROM products
""", conn)
checks["products duplicate IDs"] = {
    "value": dup_products["dupes"][0],
    "type":  "duplicate"
}

# ── Sanity checks ─────────────────────────────────────────────
neg_revenue = pd.read_sql(
    "SELECT COUNT(*) as n FROM sales WHERE revenue < 0", conn
)
checks["negative revenue rows"] = {
    "value": neg_revenue["n"][0],
    "type":  "sanity"
}

neg_profit = pd.read_sql(
    "SELECT COUNT(*) as n FROM sales WHERE profit < 0", conn
)
checks["negative profit rows"] = {
    "value": neg_profit["n"][0],
    "type":  "sanity"
}

zero_quantity = pd.read_sql(
    "SELECT COUNT(*) as n FROM sales WHERE quantity <= 0", conn
)
checks["zero or negative quantity"] = {
    "value": zero_quantity["n"][0],
    "type":  "sanity"
}

orphan_sales = pd.read_sql("""
    SELECT COUNT(*) as n FROM sales s
    LEFT JOIN customers c ON s.customer_id = c.customer_id
    WHERE c.customer_id IS NULL
""", conn)
checks["sales with no matching customer"] = {
    "value": orphan_sales["n"][0],
    "type":  "referential"
}

orphan_products = pd.read_sql("""
    SELECT COUNT(*) as n FROM sales s
    LEFT JOIN products p ON s.product_id = p.product_id
    WHERE p.product_id IS NULL
""", conn)
checks["sales with no matching product"] = {
    "value": orphan_products["n"][0],
    "type":  "referential"
}

# ── Row counts ────────────────────────────────────────────────
row_counts = {}
for table in ["sales", "customers", "products", "regions", "salespersons"]:
    count = pd.read_sql(f"SELECT COUNT(*) as n FROM {table}", conn)
    row_counts[table] = count["n"][0]

# ── Date range ────────────────────────────────────────────────
date_range = pd.read_sql("""
    SELECT MIN(order_date) as min_date, MAX(order_date) as max_date FROM sales
""", conn)

# ── Revenue stats ─────────────────────────────────────────────
rev_stats = pd.read_sql("""
    SELECT 
        ROUND(SUM(revenue), 2)  as total_revenue,
        ROUND(AVG(revenue), 2)  as avg_revenue,
        ROUND(MIN(revenue), 2)  as min_revenue,
        ROUND(MAX(revenue), 2)  as max_revenue
    FROM sales
""", conn)

conn.close()

# ── Build report ──────────────────────────────────────────────
lines = []
lines.append(f"# Data Quality Report")
lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

lines.append("---\n")
lines.append("## Row Counts\n")
lines.append("| Table | Rows |")
lines.append("|-------|------|")
for table, count in row_counts.items():
    lines.append(f"| {table} | {count:,} |")

lines.append("\n---\n")
lines.append("## Date Range\n")
lines.append("| Metric | Value |")
lines.append("|--------|-------|")
lines.append(f"| Earliest order | {date_range['min_date'][0]} |")
lines.append(f"| Latest order   | {date_range['max_date'][0]} |")

lines.append("\n---\n")
lines.append("## Revenue Statistics\n")
lines.append("| Metric | Value |")
lines.append("|--------|-------|")
lines.append(f"| Total Revenue | ${rev_stats['total_revenue'][0]:,.2f} |")
lines.append(f"| Avg Revenue per row | ${rev_stats['avg_revenue'][0]:,.2f} |")
lines.append(f"| Min Revenue | ${rev_stats['min_revenue'][0]:,.2f} |")
lines.append(f"| Max Revenue | ${rev_stats['max_revenue'][0]:,.2f} |")

lines.append("\n---\n")
lines.append("## Quality Checks\n")
lines.append("| Check | Type | Result | Status |")
lines.append("|-------|------|--------|--------|")

all_pass = True
for check, info in checks.items():
    val  = info["value"]
    ctype = info["type"].upper()
    if info["type"] in ("null", "duplicate", "referential"):
        status = "✅ PASS" if val == 0 else "❌ FAIL"
        if val != 0:
            all_pass = False
    else:
        status = "⚠️ INFO"
    lines.append(f"| {check} | {ctype} | {val:,} | {status} |")

lines.append("\n---\n")
overall = "✅ ALL CHECKS PASSED" if all_pass else "⚠️ SOME CHECKS FAILED — review above"
lines.append(f"## Overall Status: {overall}\n")

lines.append("---\n")
lines.append("*Generated by data_quality_report.py*")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"✅ Report saved to outputs/data_quality_report.md")
print(f"   Overall: {overall}")