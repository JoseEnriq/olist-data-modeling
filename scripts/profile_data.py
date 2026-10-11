"""Profile every CSV in data/raw/ and write the result to docs/profile.md.

For each file: row count and, per column, the type DuckDB infers, nulls,
distinct values and whether the column alone is unique. The numbers quoted
in docs/exploration.md come from this output or from the checks at the end.

Usage:
    python scripts/profile_data.py
"""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUTPUT = ROOT / "docs" / "profile.md"

# Targeted checks behind the findings in docs/exploration.md.
# Each one is (description, SQL returning a single row).
CHECKS = [
    (
        "orders: distinct customer_id vs distinct customer_unique_id",
        """
        select count(distinct o.customer_id), count(distinct c.customer_unique_id)
        from orders o join customers c using (customer_id)
        """,
    ),
    (
        "customers: customer_unique_id with more than one customer_id",
        """
        select count(*) from (
            select customer_unique_id from customers
            group by 1 having count(*) > 1
        )
        """,
    ),
    (
        "order_items: (order_id, order_item_id) is unique",
        """
        select count(*) = count(distinct (order_id, order_item_id)) from order_items
        """,
    ),
    (
        "order_items: orders whose order_item_id is not 1..n / orders with the same product on several lines",
        """
        select
            (select count(*) from (
                select order_id from order_items group by 1
                having min(order_item_id) <> 1 or max(order_item_id) <> count(*)
            )),
            (select count(*) from (
                select order_id, product_id from order_items group by 1, 2 having count(*) > 1
            ))
        """,
    ),
    (
        "order_items: same product in the same order with different price or freight",
        """
        select count(*) from (
            select order_id, product_id from order_items group by 1, 2
            having count(distinct price) > 1 or count(distinct freight_value) > 1
        )
        """,
    ),
    (
        "order_items: orders with more than one seller",
        """
        select count(*) from (
            select order_id from order_items group by 1 having count(distinct seller_id) > 1
        )
        """,
    ),
    (
        "order_payments: orders whose payment_sequential is not 1..n",
        """
        select count(*) from (
            select order_id from order_payments group by 1
            having min(payment_sequential) <> 1 or max(payment_sequential) <> count(*)
        )
        """,
    ),
    (
        "orders: estimated delivery dates with a time part / reviews created with a time part",
        """
        select
            (select count(*) from orders
             where cast(order_estimated_delivery_date as time) <> time '00:00:00'),
            (select count(*) from order_reviews
             where cast(review_creation_date as time) <> time '00:00:00')
        """,
    ),
    (
        "products: categories missing from the translation table",
        """
        select string_agg(distinct product_category_name, ', ') from products
        where product_category_name not in
              (select product_category_name from product_category_name_translation)
        """,
    ),
    (
        "order_payments: (order_id, payment_sequential) is unique",
        """
        select count(*) = count(distinct (order_id, payment_sequential)) from order_payments
        """,
    ),
    (
        "order_reviews: rows / distinct review_id / distinct (review_id, order_id)",
        """
        select count(*), count(distinct review_id), count(distinct (review_id, order_id))
        from order_reviews
        """,
    ),
    (
        "customers: customer_unique_id with more than one zip prefix / city / state",
        """
        select
            count(*) filter (where zips > 1),
            count(*) filter (where cities > 1),
            count(*) filter (where states > 1)
        from (
            select customer_unique_id,
                   count(distinct customer_zip_code_prefix) as zips,
                   count(distinct customer_city) as cities,
                   count(distinct customer_state) as states
            from customers group by 1
        )
        """,
    ),
    (
        "customers: zip prefixes with more than one city / more than one state",
        """
        select count(*) filter (where cities > 1), count(*) filter (where states > 1)
        from (
            select customer_zip_code_prefix,
                   count(distinct customer_city) as cities,
                   count(distinct customer_state) as states
            from customers group by 1
        )
        """,
    ),
    (
        "geolocation: zip prefixes with more than one city name / more than one state",
        """
        select count(*) filter (where cities > 1), count(*) filter (where states > 1)
        from (
            select geolocation_zip_code_prefix,
                   count(distinct geolocation_city) as cities,
                   count(distinct geolocation_state) as states
            from geolocation group by 1
        )
        """,
    ),
    (
        "order_reviews: review_ids on more than one order / of those, with differing content / of those, from a single customer",
        """
        with shared as (
            select review_id
            from order_reviews group by 1 having count(distinct order_id) > 1
        ), per_review as (
            select r.review_id,
                   count(distinct r.review_score) as scores,
                   count(distinct coalesce(r.review_comment_message, '')) as messages,
                   count(distinct coalesce(r.review_comment_title, '')) as titles,
                   count(distinct r.review_creation_date) as dates,
                   count(distinct r.review_answer_timestamp) as answers,
                   count(distinct c.customer_unique_id) as customers
            from order_reviews r
            join shared using (review_id)
            join orders o using (order_id)
            join customers c using (customer_id)
            group by 1
        )
        select count(*),
               count(*) filter (where scores > 1 or messages > 1 or titles > 1
                                      or dates > 1 or answers > 1),
               count(*) filter (where customers = 1)
        from per_review
        """,
    ),
    (
        "order_reviews: max reviews per order / max orders per review_id",
        """
        select
            (select max(n) from (select order_id, count(*) n from order_reviews group by 1)),
            (select max(n) from (select review_id, count(*) n from order_reviews group by 1))
        """,
    ),
    (
        "order_reviews: orders with more than one review",
        """
        select count(*) from (
            select order_id from order_reviews group by 1 having count(*) > 1
        )
        """,
    ),
    (
        "geolocation: rows / distinct zip code prefixes",
        """
        select count(*), count(distinct geolocation_zip_code_prefix) from geolocation
        """,
    ),
    (
        "geolocation: exact duplicate rows",
        """
        select count(*) - (select count(*) from (select distinct * from geolocation))
        from geolocation
        """,
    ),
    (
        "customers: zip prefixes missing from geolocation",
        """
        select count(distinct customer_zip_code_prefix) from customers
        where customer_zip_code_prefix not in (select geolocation_zip_code_prefix from geolocation)
        """,
    ),
    (
        "sellers: zip prefixes missing from geolocation",
        """
        select count(distinct seller_zip_code_prefix) from sellers
        where seller_zip_code_prefix not in (select geolocation_zip_code_prefix from geolocation)
        """,
    ),
    (
        "orders: orders without items / without payments / without reviews",
        """
        select
            count(*) filter (where order_id not in (select order_id from order_items)),
            count(*) filter (where order_id not in (select order_id from order_payments)),
            count(*) filter (where order_id not in (select order_id from order_reviews))
        from orders
        """,
    ),
    (
        "orders: count by order_status",
        """
        select string_agg(order_status || '=' || n, ', ' order by n desc)
        from (select order_status, count(*) n from orders group by 1)
        """,
    ),
    (
        "orders: delivered orders without delivered_customer_date",
        """
        select count(*) from orders
        where order_status = 'delivered' and order_delivered_customer_date is null
        """,
    ),
    (
        "orders: orders without items, by order_status",
        """
        select string_agg(order_status || '=' || n, ', ' order by n desc)
        from (
            select order_status, count(*) n from orders
            where order_id not in (select order_id from order_items)
            group by 1
        )
        """,
    ),
    (
        "orders: delivered to customer before purchase / handed to carrier before approval",
        """
        select
            count(*) filter (where order_delivered_customer_date < order_purchase_timestamp),
            count(*) filter (where order_delivered_carrier_date < order_approved_at)
        from orders
        """,
    ),
    (
        "orders: orders per month in the first 4 and last 3 months of the range",
        """
        with m as (
            select strftime(order_purchase_timestamp, '%Y-%m') as month, count(*) n
            from orders group by 1
        ), ranked as (
            select *, row_number() over (order by month) r_asc,
                      row_number() over (order by month desc) r_desc
            from m
        )
        select string_agg(month || '=' || n, ', ' order by month)
        from ranked where r_asc <= 4 or r_desc <= 3
        """,
    ),
    (
        "order_payments: payments with 0 installments",
        """
        select count(*) from order_payments where payment_installments = 0
        """,
    ),
    (
        "orders: purchase date range",
        """
        select min(order_purchase_timestamp), max(order_purchase_timestamp) from orders
        """,
    ),
    (
        "products: rows without category / categories missing from translation table",
        """
        select
            count(*) filter (where product_category_name is null),
            (select count(distinct product_category_name) from products
             where product_category_name not in
                   (select product_category_name from product_category_name_translation))
        from products
        """,
    ),
    (
        "products: rows missing category, name, description and photos at the same time",
        """
        select count(*) from products
        where product_category_name is null and product_name_lenght is null
          and product_description_lenght is null and product_photos_qty is null
        """,
    ),
    (
        "customers: rows whose zip prefix starts with 0",
        """
        select count(*) from customers where customer_zip_code_prefix like '0%'
        """,
    ),
    (
        "order_payments: payments with value 0 / count by payment_type",
        """
        select
            (select count(*) from order_payments where payment_value = 0),
            (select string_agg(payment_type || '=' || n, ', ' order by n desc)
             from (select payment_type, count(*) n from order_payments group by 1))
        """,
    ),
    (
        "orders: orders whose item total (price + freight) differs from payments by more than 1 BRL",
        """
        with items as (
            select order_id, sum(price + freight_value) as item_total
            from order_items group by 1
        ), pays as (
            select order_id, sum(payment_value) as paid
            from order_payments group by 1
        )
        select count(*) from items join pays using (order_id)
        where abs(item_total - paid) > 1
        """,
    ),
]


def table_name(csv: Path) -> str:
    # olist_order_items_dataset.csv -> order_items
    return csv.stem.removeprefix("olist_").removesuffix("_dataset")


def main() -> None:
    con = duckdb.connect()
    csvs = sorted(RAW_DIR.glob("*.csv"))
    for csv in csvs:
        con.execute(
            f"create view {table_name(csv)} as select * from read_csv_auto('{csv.as_posix()}')"
        )

    lines = [
        "# Data profile",
        "",
        "Generated by `scripts/profile_data.py`. Do not edit by hand.",
        "",
    ]

    for csv in csvs:
        name = table_name(csv)
        rows = con.execute(f"select count(*) from {name}").fetchone()[0]
        lines += [f"## {name}", "", f"File: `{csv.name}` · {rows:,} rows", ""]
        lines += ["| column | type | nulls | distinct | unique |", "|---|---|---:|---:|:---:|"]
        for col, col_type, *_ in con.execute(f"describe {name}").fetchall():
            nulls, distinct = con.execute(
                f'select count(*) - count("{col}"), count(distinct "{col}") from {name}'
            ).fetchone()
            unique = "yes" if distinct == rows and nulls == 0 else ""
            lines.append(f"| {col} | {col_type} | {nulls:,} | {distinct:,} | {unique} |")
        lines.append("")

    lines += ["## Checks", "", "| check | result |", "|---|---|"]
    for description, sql in CHECKS:
        result = con.execute(sql).fetchone()
        value = " / ".join(str(v) for v in result)
        lines.append(f"| {description} | {value} |")
    lines.append("")

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
