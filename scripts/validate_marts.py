"""Compare the dbt marts with the raw files and write docs/validation.md.

Run after `dbt build` (from the dbt/ folder). The database is opened read-only.
The dbt tests already fail the build if something breaks; this report records
the actual numbers behind those checks.

Usage:
    python scripts/validate_marts.py
"""

from pathlib import Path

import duckdb
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATABASE = ROOT / "dbt" / "olist.duckdb"
RAW_DIR = ROOT / "data" / "raw"
OUTPUT = ROOT / "docs" / "validation.md"

# Same bounding box the dbt models use, read from dbt_project.yml.
BRAZIL = yaml.safe_load((ROOT / "dbt" / "dbt_project.yml").read_text(encoding="utf-8"))["vars"]


def raw(name: str) -> str:
    path = (RAW_DIR / f"{name}.csv").as_posix()
    return f"read_csv('{path}', header = true, all_varchar = true)"


ORDERS = raw("olist_orders_dataset")
ITEMS = raw("olist_order_items_dataset")
PAYMENTS = raw("olist_order_payments_dataset")
REVIEWS = raw("olist_order_reviews_dataset")
CUSTOMERS = raw("olist_customers_dataset")
PRODUCTS = raw("olist_products_dataset")
SELLERS = raw("olist_sellers_dataset")
GEOLOCATION = raw("olist_geolocation_dataset")

# (description, query on the raw files, query on the marts)
SOURCE_VS_MARTS = [
    ("Pedidos", f"select count(*) from {ORDERS}", "select count(*) from fct_orders"),
    ("Itens", f"select count(*) from {ITEMS}", "select count(*) from fct_order_items"),
    ("Pagamentos", f"select count(*) from {PAYMENTS}", "select count(*) from fct_payments"),
    ("Linhas de avaliação (avaliação × pedido)", f"select count(*) from {REVIEWS}",
     "select count(*) from fct_reviews"),
    ("Avaliações distintas", f"select count(distinct review_id) from {REVIEWS}",
     "select count(distinct review_id) from fct_reviews"),
    ("Clientes (customer_unique_id)", f"select count(distinct customer_unique_id) from {CUSTOMERS}",
     "select count(*) from dim_customer"),
    ("Produtos", f"select count(*) from {PRODUCTS}", "select count(*) from dim_product"),
    ("Vendedores", f"select count(*) from {SELLERS}", "select count(*) from dim_seller"),
    ("Soma de preço dos itens (R$)", f"select sum(cast(price as decimal(18, 2))) from {ITEMS}",
     "select sum(price) from fct_order_items"),
    ("Soma de frete dos itens (R$)", f"select sum(cast(freight_value as decimal(18, 2))) from {ITEMS}",
     "select sum(freight_value) from fct_order_items"),
    ("Soma dos pagamentos (R$)", f"select sum(cast(payment_value as decimal(18, 2))) from {PAYMENTS}",
     "select sum(payment_value) from fct_payments"),
    ("Soma dos pagamentos via fct_orders (R$)",
     f"select sum(cast(payment_value as decimal(18, 2))) from {PAYMENTS}",
     "select sum(payment_total) from fct_orders"),
]

# (description, query that must return 0)
KEY_CHECKS = [
    ("Chaves duplicadas em dim_customer", "select count(*) - count(distinct customer_key) from dim_customer"),
    ("Chaves duplicadas em dim_product", "select count(*) - count(distinct product_key) from dim_product"),
    ("Chaves duplicadas em dim_seller", "select count(*) - count(distinct seller_key) from dim_seller"),
    ("Chaves duplicadas em dim_location", "select count(*) - count(distinct location_key) from dim_location"),
    ("Pedidos duplicados em fct_orders", "select count(*) - count(distinct order_id) from fct_orders"),
    ("Itens sem cliente na dimensão",
     "select count(*) from fct_order_items f anti join dim_customer d using (customer_key)"),
    ("Itens sem produto na dimensão",
     "select count(*) from fct_order_items f anti join dim_product d using (product_key)"),
    ("Itens sem vendedor na dimensão",
     "select count(*) from fct_order_items f anti join dim_seller d using (seller_key)"),
    ("Itens sem local de entrega na dimensão",
     "select count(*) from fct_order_items f anti join dim_location d on f.delivery_location_key = d.location_key"),
    ("Pedidos sem data de compra na dimensão",
     "select count(*) from fct_orders f anti join dim_date d on f.purchase_date_key = d.date_key"),
    ("Pagamentos sem cliente na dimensão",
     "select count(*) from fct_payments f anti join dim_customer d using (customer_key)"),
    ("Avaliações sem cliente na dimensão",
     "select count(*) from fct_reviews f anti join dim_customer d using (customer_key)"),
]

# (description, query) — known data issues, kept in the model on purpose.
ATTENTION_POINTS = [
    ("Pedidos sem itens (ficam em fct_orders com total zero)",
     "select count(*) from fct_orders where items_count = 0"),
    ("Pedidos sem nenhum pagamento registrado",
     "select count(*) from fct_orders o anti join fct_payments p using (order_id)"),
    ("Pedidos com pagamentos que somam zero",
     "select count(*) from fct_orders o semi join fct_payments p using (order_id) where o.payment_total = 0"),
    ("Pedidos sem avaliação",
     "select count(*) from fct_orders o anti join fct_reviews r using (order_id)"),
    ("Pedidos com status delivered sem data de entrega",
     "select count(*) from fct_orders where order_status = 'delivered' and not is_delivered"),
    ("Pedidos com data de entrega e outro status",
     "select count(*) from fct_orders where order_status <> 'delivered' and is_delivered"),
    ("Avaliações que cobrem mais de um pedido",
     "select count(*) from (select review_id from fct_reviews group by 1 having count(*) > 1)"),
    ("Produtos sem categoria (rótulo sem_categoria)",
     "select count(*) from dim_product where product_category_name = 'sem_categoria'"),
    ("Pontos de geolocalização fora do Brasil (descartados antes da mediana)",
     f"""select count(*) from {GEOLOCATION}
         where not (cast(geolocation_lat as double)
                        between {BRAZIL['brazil_min_latitude']} and {BRAZIL['brazil_max_latitude']}
                and cast(geolocation_lng as double)
                        between {BRAZIL['brazil_min_longitude']} and {BRAZIL['brazil_max_longitude']})"""),
    ("Endereços de entrega sem coordenada", "select count(*) from dim_location where latitude is null"),
    ("Vendedores sem coordenada", "select count(*) from dim_seller where latitude is null"),
]


def value(con, sql):
    return con.execute(sql).fetchone()[0]


def fmt(number) -> str:
    # Brazilian format: 13.591.643,70
    if isinstance(number, int):
        return f"{number:,}".replace(",", ".")
    text = f"{number:,.2f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def main() -> None:
    con = duckdb.connect(str(DATABASE), read_only=True)

    lines = [
        "# Validação dos marts",
        "",
        "Gerado por `scripts/validate_marts.py` depois do `dbt build`. Não edite à mão.",
        "",
        "Os testes do dbt (`dbt/tests/` e os `.yml`) já fazem o build falhar se algo abaixo quebrar. "
        "Este relatório registra os números por trás desses testes.",
        "",
        "## Origem × marts",
        "",
        "Cada linha e cada real da origem precisa chegar aos marts, sem perda nem duplicação.",
        "",
        "| verificação | origem (CSV) | marts | ok |",
        "|---|---:|---:|:---:|",
    ]
    failures = 0
    for description, source_sql, mart_sql in SOURCE_VS_MARTS:
        source_value, mart_value = value(con, source_sql), value(con, mart_sql)
        ok = source_value == mart_value
        failures += not ok
        lines.append(f"| {description} | {fmt(source_value)} | {fmt(mart_value)} | {'✅' if ok else '❌'} |")

    lines += [
        "",
        "## Chaves",
        "",
        "Nenhuma chave duplicada nas dimensões e nenhuma chave órfã nos fatos (fato apontando para algo que não existe na dimensão).",
        "",
        "| verificação | encontrados | ok |",
        "|---|---:|:---:|",
    ]
    for description, sql in KEY_CHECKS:
        found = value(con, sql)
        failures += found != 0
        lines.append(f"| {description} | {fmt(found)} | {'✅' if found == 0 else '❌'} |")

    lines += [
        "",
        "## Pontos de atenção",
        "",
        "Problemas conhecidos dos dados, mantidos no modelo de propósito. As decisões estão em [decisions.md](decisions.md).",
        "",
        "| ponto | quantidade |",
        "|---|---:|",
    ]
    for description, sql in ATTENTION_POINTS:
        lines.append(f"| {description} | {fmt(value(con, sql))} |")
    lines.append("")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({failures} failing checks)")


if __name__ == "__main__":
    main()
