"""
load_data.py
------------
Reads AdventureWorks CSVs from data/raw/, cleans them,
saves processed versions to data/processed/,
and loads everything into database/adventureworks.db.

Usage:
    python scripts/load_data.py
"""

import sqlite3
import pandas as pd
from pathlib import Path
import logging

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parents[1]
RAW_DIR    = ROOT / "data" / "raw"
PROC_DIR   = ROOT / "data" / "processed"
DB_PATH    = ROOT / "database" / "adventureworks.db"

PROC_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────
def parse_money(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(r"[\$,]", "", regex=True)
        .str.strip()
        .pipe(pd.to_numeric, errors="coerce")
    )


# ─────────────────────────────────────────────────────────────
# CLEANING FUNCTIONS
# ─────────────────────────────────────────────────────────────

def clean_product(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "ProductKey":    "product_id",
        "Product":       "product_name",
        "Standard Cost": "unit_cost",
        "Color":         "color",
        "Subcategory":   "subcategory",
        "Category":      "category",
    })
    df["product_id"]   = df["product_id"].astype(str).str.strip()
    df["product_name"] = df["product_name"].str.strip()
    df["category"]     = df["category"].str.strip().str.title()
    df["subcategory"]  = df["subcategory"].str.strip().str.title()
    df["unit_cost"]    = parse_money(df["unit_cost"])
    df = df[["product_id", "product_name", "category", "subcategory", "unit_cost", "color"]]
    df = df.drop_duplicates(subset=["product_id"]).dropna(subset=["product_id"])
    log.info(f"  Product:          {len(df):,} rows")
    return df


def clean_region(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "SalesTerritoryKey": "region_id",
        "Region":            "region_name",
        "Country":           "country",
        "Group":             "territory",
    })
    df["region_id"]   = df["region_id"].astype(str).str.strip()
    df["region_name"] = df["region_name"].str.strip().str.title()
    df["country"]     = df["country"].str.strip().str.title()
    df["territory"]   = df["territory"].str.strip().str.title()
    df = df[["region_id", "region_name", "country", "territory"]]
    df = df.drop_duplicates(subset=["region_id"]).dropna(subset=["region_id"])
    log.info(f"  Region:           {len(df):,} rows")
    return df


def clean_reseller(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "ResellerKey":    "customer_id",
        "Reseller":       "customer_name",
        "Business Type":  "segment",
        "City":           "city",
        "State-Province": "state",
        "Country-Region": "region",
    })
    df["customer_id"]   = df["customer_id"].astype(str).str.strip()
    df["customer_name"] = df["customer_name"].str.strip().str.title()
    df["segment"]       = df["segment"].str.strip().str.title()
    df["city"]          = df["city"].str.strip().str.title()
    df["region"]        = df["region"].str.strip().str.title()
    df = df[["customer_id", "customer_name", "segment", "city", "state", "region"]]
    df = df.drop_duplicates(subset=["customer_id"]).dropna(subset=["customer_id"])
    log.info(f"  Reseller:         {len(df):,} rows  (customers)")
    return df


def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "SalesOrderNumber":  "order_id",
        "OrderDate":         "order_date",
        "ProductKey":        "product_id",
        "ResellerKey":       "customer_id",
        "EmployeeKey":       "employee_id",
        "SalesTerritoryKey": "region_id",
        "Quantity":          "quantity",
        "Unit Price":        "unit_price",
        "Sales":             "revenue",
        "Cost":              "cost",
    })
    for col in ["unit_price", "revenue", "cost"]:
        df[col] = parse_money(df[col])
    df["order_date"] = pd.to_datetime(
        df["order_date"], format="%A, %B %d, %Y", errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    df["quantity"]    = pd.to_numeric(df["quantity"], errors="coerce")
    df["product_id"]  = df["product_id"].astype(str).str.strip()
    df["customer_id"] = df["customer_id"].astype(str).str.strip()
    df["region_id"]   = df["region_id"].astype(str).str.strip()
    df["employee_id"] = df["employee_id"].astype(str).str.strip()
    df["profit"]      = (df["revenue"] - df["cost"]).round(2)
    df["revenue"]     = df["revenue"].round(2)
    df["cost"]        = df["cost"].round(2)
    before = len(df)
    df = df.dropna(subset=["order_id", "customer_id", "product_id", "revenue"])
    dropped = before - len(df)
    if dropped:
        log.warning(f"  Sales: dropped {dropped:,} rows with nulls")
    df = df[[
        "order_id", "order_date", "product_id", "customer_id",
        "employee_id", "region_id", "quantity", "unit_price",
        "revenue", "cost", "profit"
    ]]
    log.info(f"  Sales:            {len(df):,} rows")
    return df


def clean_salesperson(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "EmployeeKey": "employee_id",
        "EmployeeID":  "employee_code",
        "Salesperson": "salesperson_name",
        "Title":       "title",
        "UPN":         "email",
    })
    df["employee_id"]   = df["employee_id"].astype(str).str.strip()
    df["employee_code"] = df["employee_code"].astype(str).str.strip()
    df = df.drop_duplicates(subset=["employee_id"]).dropna(subset=["employee_id"])
    log.info(f"  Salesperson:      {len(df):,} rows")
    return df


def clean_targets(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "EmployeeID":  "employee_code",
        "Target":      "target_amount",
        "TargetMonth": "target_month",
    })
    df["target_amount"] = parse_money(df["target_amount"])
    df["target_month"]  = pd.to_datetime(
        df["target_month"], format="%A, %B %d, %Y", errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    df["employee_code"] = df["employee_code"].astype(str).str.strip()
    df = df.dropna(subset=["employee_code", "target_amount"])
    log.info(f"  Targets:          {len(df):,} rows")
    return df


def clean_salesperson_region(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "EmployeeKey":       "employee_id",
        "SalesTerritoryKey": "region_id",
    })
    df["employee_id"] = df["employee_id"].astype(str).str.strip()
    df["region_id"]   = df["region_id"].astype(str).str.strip()
    df = df.drop_duplicates()
    log.info(f"  SalespersonRegion:{len(df):,} rows")
    return df


# ─────────────────────────────────────────────────────────────
# DATABASE SCHEMA
# ─────────────────────────────────────────────────────────────

SCHEMA_SQL = """
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS targets;
DROP TABLE IF EXISTS salesperson_region;
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

CREATE TABLE targets (
    employee_code  TEXT,
    target_amount  REAL,
    target_month   TEXT
);

CREATE TABLE salesperson_region (
    employee_id  TEXT,
    region_id    TEXT
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

CREATE INDEX IF NOT EXISTS idx_sales_customer  ON sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_product   ON sales(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_region    ON sales(region_id);
CREATE INDEX IF NOT EXISTS idx_sales_date      ON sales(order_date);
CREATE INDEX IF NOT EXISTS idx_targets_emp     ON targets(employee_code);
CREATE INDEX IF NOT EXISTS idx_sp_region_emp   ON salesperson_region(employee_id);
"""


def setup_database(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    log.info("Database schema created")


def load_table(conn: sqlite3.Connection, df: pd.DataFrame, table: str) -> None:
    df.to_sql(table, conn, if_exists="append", index=False)
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    log.info(f"  Loaded {count:,} rows -> {table}")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main() -> None:
    log.info("=== load_data.py starting ===")

    required = [
        "Sales.csv", "Product.csv", "Region.csv",
        "Reseller.csv", "Salesperson.csv",
        "Targets.csv", "SalespersonRegion.csv"
    ]
    for f in required:
        path = RAW_DIR / f
        if not path.exists():
            raise FileNotFoundError(
                f"\nMissing file: {path}\n"
                f"Make sure all CSV files are inside: {RAW_DIR}"
            )

    log.info("Reading raw files...")
    raw = {
        "product":            pd.read_csv(RAW_DIR / "Product.csv",           sep="\t", encoding="utf-8-sig"),
        "region":             pd.read_csv(RAW_DIR / "Region.csv",            sep="\t", encoding="utf-8-sig"),
        "reseller":           pd.read_csv(RAW_DIR / "Reseller.csv",          sep="\t", encoding="utf-8-sig"),
        "sales":              pd.read_csv(RAW_DIR / "Sales.csv",             sep="\t", encoding="utf-8-sig"),
        "salesperson":        pd.read_csv(RAW_DIR / "Salesperson.csv",       sep="\t", encoding="utf-8-sig"),
        "targets":            pd.read_csv(RAW_DIR / "Targets.csv",           sep="\t", encoding="utf-8-sig"),
        "salesperson_region": pd.read_csv(RAW_DIR / "SalespersonRegion.csv", sep="\t", encoding="utf-8-sig"),
    }
    for name, df in raw.items():
        log.info(f"  Read {len(df):,} rows from {name}")

    log.info("Cleaning data...")
    cleaned = {
        "products":           clean_product(raw["product"]),
        "regions":            clean_region(raw["region"]),
        "customers":          clean_reseller(raw["reseller"]),
        "sales":              clean_sales(raw["sales"]),
        "salespersons":       clean_salesperson(raw["salesperson"]),
        "targets":            clean_targets(raw["targets"]),
        "salesperson_region": clean_salesperson_region(raw["salesperson_region"]),
    }

    log.info("Saving processed CSVs...")
    for name, df in cleaned.items():
        out = PROC_DIR / f"{name}_cleaned.csv"
        df.to_csv(out, index=False)
        log.info(f"  Saved -> {out.name}")

    log.info(f"Loading into {DB_PATH.name}...")
    with sqlite3.connect(DB_PATH) as conn:
        setup_database(conn)
        for table in [
            "products", "regions", "customers",
            "salespersons", "targets", "salesperson_region", "sales"
        ]:
            load_table(conn, cleaned[table], table)

    log.info("=== Done! Run: python scripts/run_queries.py ===")


if __name__ == "__main__":
    main()