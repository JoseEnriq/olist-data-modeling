"""Export the dbt marts to Parquet files for the Power BI report.

Run after `dbt build`. Each mart becomes one file in data/marts/, which the
report in powerbi/ reads with Power BI's native Parquet connector. Parquet keeps
the column types (dates, decimals, booleans), so Power Query does not have to
guess them again. Only the tested marts are exported: every business rule stays
in dbt, and the report only adds measures on top.

Usage:
    python scripts/export_marts.py
"""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DATABASE = ROOT / "dbt" / "olist.duckdb"
OUTPUT_DIR = ROOT / "data" / "marts"

# Listed by name rather than discovered, so a mart that disappears from dbt
# breaks the export instead of silently leaving the report without a table.
MARTS = (
    "dim_date",
    "dim_customer",
    "dim_location",
    "dim_product",
    "dim_seller",
    "fct_orders",
    "fct_order_items",
    "fct_payments",
    "fct_reviews",
)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DATABASE), read_only=True)

    for name in MARTS:
        target = OUTPUT_DIR / f"{name}.parquet"
        con.execute(f"copy {name} to '{target.as_posix()}' (format parquet)")
        rows = con.execute(f"select count(*) from '{target.as_posix()}'").fetchone()[0]
        print(f"{name:<16} {rows:>9,} rows -> {target.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
