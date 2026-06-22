"""
run_queries.py
--------------
Executes SQL analysis files against adventureworks.db,
saves each result as a CSV in outputs/,
and generates charts in outputs/charts/.

Usage:
    python scripts/run_queries.py
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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
ROOT        = Path(__file__).resolve().parents[1]
DB_PATH     = ROOT / "database" / "adventureworks.db"
SQL_DIR     = ROOT / "sql"
OUTPUTS_DIR = ROOT / "outputs"
CHARTS_DIR  = OUTPUTS_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Plot style ────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor":  "white",
    "axes.facecolor":    "white",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.3,
    "font.size":         11,
})

COLORS = {
    "primary":   "#378ADD",
    "secondary": "#1D9E75",
    "warning":   "#EF9F27",
    "danger":    "#E24B4A",
}


# ─────────────────────────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────────────────────────

def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}\n"
            "Run load_data.py first."
        )
    return sqlite3.connect(DB_PATH)


def run_sql_file(conn: sqlite3.Connection, sql_file: Path) -> list[pd.DataFrame]:
    """Split a .sql file on semicolons, run each SELECT, return DataFrames."""
    text       = sql_file.read_text(encoding="utf-8")
    statements = [s.strip() for s in text.split(";") if s.strip()]
    results    = []
    for i, stmt in enumerate(statements, 1):
        if not any(kw in stmt.upper() for kw in ("SELECT", "WITH")):
            continue
        try:
            df = pd.read_sql_query(stmt, conn)
            log.info(f"  [{sql_file.name}] query {i}: {len(df):,} rows")
            results.append(df)
        except Exception as e:
            log.warning(f"  [{sql_file.name}] query {i} failed: {e}")
    return results


# ─────────────────────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────────────────────

def chart_pareto(df: pd.DataFrame) -> None:
    if df.empty or "cumulative_pct" not in df.columns:
        return
    top = df.head(30).copy()
    fig, ax1 = plt.subplots(figsize=(14, 6))

    ax1.bar(range(len(top)), top["revenue_share_pct"],
            color=COLORS["primary"], alpha=0.75, label="Revenue share %")
    ax1.set_ylabel("Individual revenue share (%)", color=COLORS["primary"])
    ax1.set_xticks(range(len(top)))
    ax1.set_xticklabels(
        top.get("customer_name", top["customer_id"]),
        rotation=45, ha="right", fontsize=8)

    ax2 = ax1.twinx()
    ax2.plot(range(len(top)), top["cumulative_pct"],
             color=COLORS["danger"], marker="o", markersize=3,
             linewidth=2, label="Cumulative %")
    ax2.axhline(80, color=COLORS["warning"], linestyle="--",
                linewidth=1.2, label="80% threshold")
    ax2.set_ylabel("Cumulative revenue (%)", color=COLORS["danger"])
    ax2.set_ylim(0, 105)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)
    fig.suptitle("Pareto Analysis — Top 30 Customers by Revenue", fontsize=13)

    plt.tight_layout()
    path = CHARTS_DIR / "pareto_curve.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info(f"  Saved → {path.name}")


def chart_bar(df: pd.DataFrame, group_col: str, value_col: str,
              title: str, filename: str) -> None:
    if df.empty or group_col not in df.columns:
        return
    df = df.sort_values(value_col, ascending=True).tail(15)
    fig, ax = plt.subplots(figsize=(10, max(4, len(df) * 0.45)))
    ax.barh(df[group_col], df[value_col],
            color=COLORS["secondary"], alpha=0.8)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"${x/1e6:.1f}M" if x >= 1e6 else f"${x/1e3:.0f}K"))
    ax.set_title(title, fontsize=12)
    plt.tight_layout()
    path = CHARTS_DIR / filename
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info(f"  Saved → {path.name}")


def chart_risk_matrix(df: pd.DataFrame) -> None:
    if df.empty or "revenue_share_pct" not in df.columns:
        return
    risk_colors = {
        "CRITICAL  (>=10%)": COLORS["danger"],
        "HIGH      (>=5%)":  COLORS["warning"],
        "MODERATE  (>=2%)":  COLORS["primary"],
    }
    fig, ax = plt.subplots(figsize=(10, 6))
    for risk, group in df.groupby("risk_level"):
        ax.scatter(group["total_orders"], group["revenue_share_pct"],
                   c=risk_colors.get(risk, "#aaa"),
                   label=risk.strip(), s=80, alpha=0.85,
                   edgecolors="white", linewidths=0.5)
    for _, row in df.iterrows():
        ax.annotate(row.get("customer_name", row["customer_id"]),
                    (row["total_orders"], row["revenue_share_pct"]),
                    fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.axhline(5,  color=COLORS["warning"], linestyle="--", linewidth=1, alpha=0.6)
    ax.axhline(10, color=COLORS["danger"],  linestyle="--", linewidth=1, alpha=0.6)
    ax.set_xlabel("Total orders")
    ax.set_ylabel("Revenue share (%)")
    ax.set_title("Concentration Risk Matrix", fontsize=12)
    ax.legend(fontsize=9)
    plt.tight_layout()
    path = CHARTS_DIR / "risk_matrix.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info(f"  Saved → {path.name}")


def chart_monthly_trend(df: pd.DataFrame) -> None:
    if df.empty or "monthly_revenue" not in df.columns:
        return
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(range(len(df)), df["monthly_revenue"],
            color=COLORS["primary"], linewidth=2, marker="o", markersize=4)
    ax.fill_between(range(len(df)), df["monthly_revenue"],
                    alpha=0.08, color=COLORS["primary"])
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df["year_month"], rotation=45, ha="right", fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"${x/1e6:.1f}M" if x >= 1e6 else f"${x/1e3:.0f}K"))
    ax.set_title("Monthly Revenue Trend", fontsize=12)
    plt.tight_layout()
    path = CHARTS_DIR / "monthly_trend.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info(f"  Saved → {path.name}")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main() -> None:
    log.info("=== run_queries.py starting ===")
    conn = connect()

    # ── 02: Pareto ───────────────────────────────────────────
    log.info("Running 02_pareto_analysis.sql...")
    pareto = run_sql_file(conn, SQL_DIR / "02_pareto_analysis.sql")
    if pareto:
        pareto[0].to_csv(OUTPUTS_DIR / "pareto_analysis.csv", index=False)
        chart_pareto(pareto[0])
    if len(pareto) > 1:
        pareto[1].to_csv(OUTPUTS_DIR / "pareto_summary.csv", index=False)

    # ── 03: Segments ─────────────────────────────────────────
    log.info("Running 03_segment_analysis.sql...")
    segs = run_sql_file(conn, SQL_DIR / "03_segment_analysis.sql")
    names = ["region", "category", "segment", "monthly_trend", "region_x_category"]
    for i, df in enumerate(segs):
        label = names[i] if i < len(names) else f"segment_{i+1}"
        df.to_csv(OUTPUTS_DIR / f"segment_{label}.csv", index=False)
    if len(segs) > 0:
        chart_bar(segs[0], "region_name", "total_revenue",
                  "Revenue by Region", "segment_region.png")
    if len(segs) > 1:
        chart_bar(segs[1], "category", "total_revenue",
                  "Revenue by Product Category", "segment_category.png")
    if len(segs) > 3:
        chart_monthly_trend(segs[3])

    # ── 04: Risk flags ───────────────────────────────────────
    log.info("Running 04_risk_flags.sql...")
    risks = run_sql_file(conn, SQL_DIR / "04_risk_flags.sql")
    rlabels = ["high_dependency", "regional_risk", "category_risk", "scorecard"]
    for i, df in enumerate(risks):
        label = rlabels[i] if i < len(rlabels) else f"risk_{i+1}"
        df.to_csv(OUTPUTS_DIR / f"risk_{label}.csv", index=False)
    if risks:
        chart_risk_matrix(risks[0])

    conn.close()
    log.info("=== Done! Check outputs/ and outputs/charts/ ===")


if __name__ == "__main__":
    main()