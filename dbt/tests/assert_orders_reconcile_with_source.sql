-- fct_orders must have one row per source order, and its per-order totals must
-- add up to the item and payment sources (the proof that there is no fan-out).

with source_totals as (

    select
        (select count(*) from {{ source('olist', 'orders') }})                     as order_count,
        (select sum(cast(price as decimal(18, 2)))
           from {{ source('olist', 'order_items') }})                              as items_price_total,
        (select sum(cast(payment_value as decimal(18, 2)))
           from {{ source('olist', 'order_payments') }})                           as payment_total

),

fact_totals as (

    select
        count(*)               as order_count,
        sum(items_price_total) as items_price_total,
        sum(payment_total)     as payment_total

    from {{ ref('fct_orders') }}

)

select *
from source_totals, fact_totals
where source_totals.order_count <> fact_totals.order_count
   or source_totals.items_price_total <> fact_totals.items_price_total
   or source_totals.payment_total <> fact_totals.payment_total
