"""Run every dbt analysis and write its result to docs/results.md.

Run after `dbt build`. The analyses in dbt/analyses/ are compiled by dbt (which
replaces {{ ref(...) }} with real table names) and then executed against the
DuckDB database, opened read-only. Every number quoted in the README comes
from this file, so none is typed by hand.

Usage:
    python scripts/export_results.py
"""

import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DBT_DIR = ROOT / "dbt"
ANALYSES_DIR = DBT_DIR / "analyses"
COMPILED_DIR = DBT_DIR / "target" / "compiled" / "olist" / "analyses"
DATABASE = DBT_DIR / "olist.duckdb"
OUTPUT = ROOT / "docs" / "results.md"

# Titles for the report, in the same order as the analysis files.
TITLES = {
    "01_revenue_by_month": "Receita e pedidos por mês",
    "02_revenue_by_category": "Categorias com maior receita",
    "03_average_ticket": "Ticket médio por ano",
    "04_payment_methods": "Formas de pagamento",
    "05_delivery_time_by_state": "Tempo de entrega por estado",
    "06_late_deliveries_by_state": "Entregas atrasadas por estado",
    "07_cancellation_rate": "Pedidos cancelados ou indisponíveis por trimestre",
    "08_seller_ratings": "Vendedores com melhor e pior nota",
    "09_review_score_vs_delay": "Nota da avaliação × atraso na entrega",
    "10_repeat_customers": "Clientes que voltam a comprar",
}


def dbt_executable() -> str:
    # The dbt that lives next to the Python running this script (the project's .venv).
    scripts_dir = Path(sys.executable).parent
    for name in ("dbt.exe", "dbt"):
        if (scripts_dir / name).exists():
            return str(scripts_dir / name)
    return "dbt"


LABEL_COLUMNS = {"year", "quarter", "month", "revenue_rank"}


def fmt(value, column: str) -> str:
    # Brazilian number format: 13.591.643,70. Columns that are labels (year,
    # quarter...) are printed as they are: 2017, not 2.017.
    if value is None:
        return ""
    if column in LABEL_COLUMNS or isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}".replace(",", ".")
    integer, _, decimals = f"{value}".partition(".")
    integer = f"{int(integer):,}".replace(",", ".") if integer not in ("", "-") else integer
    return f"{integer},{decimals}" if decimals else integer


def comments(sql_path: Path) -> list[str]:
    # The header comment of each analysis explains the question and the definitions.
    lines = []
    for line in sql_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("--"):
            break
        lines.append(line[2:].strip())
    return lines


def main() -> None:
    subprocess.run([dbt_executable(), "compile", "--select", "path:analyses", "--quiet"],
                   cwd=DBT_DIR, check=True)
    con = duckdb.connect(str(DATABASE), read_only=True)

    out = [
        "# Resultados das consultas de negócio",
        "",
        "Gerado por `scripts/export_results.py` a partir das consultas em "
        "[dbt/analyses/](../dbt/analyses/). Não edite à mão.",
        "",
        "Definições usadas em todas as consultas (detalhes em [decisions.md](decisions.md)): "
        "**pedido válido** é o que não foi cancelado nem ficou indisponível; **receita** é a soma "
        "dos preços dos itens, sem frete; séries mensais vão de janeiro de 2017 a agosto de 2018.",
        "",
    ]

    for number, (name, title) in enumerate(TITLES.items(), start=1):
        source = ANALYSES_DIR / f"{name}.sql"
        cursor = con.execute((COMPILED_DIR / f"{name}.sql").read_text(encoding="utf-8"))
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        out += [f"## {number}. {title}", "", f"Consulta: [`{source.name}`](../dbt/analyses/{source.name})", ""]
        out += ["> " + " ".join(comments(source)), ""]
        out += ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
        out += ["| " + " | ".join(fmt(v, c) for v, c in zip(row, columns)) + " |" for row in rows]
        out.append("")

    OUTPUT.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(TITLES)} analyses)")


if __name__ == "__main__":
    main()
