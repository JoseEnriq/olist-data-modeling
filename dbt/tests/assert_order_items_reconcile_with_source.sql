-- fct_order_items must keep every source row and the same money totals.
-- Returns a row (and fails) if counts or sums differ.

with source_totals as (

    select
        count(*)                                     as row_count,
        sum(cast(price as decimal(18, 2)))           as price_total,
        sum(cast(freight_value as decimal(18, 2)))   as freight_total

    from {{ source('olist', 'order_items') }}

),

fact_totals as (

    select
        count(*)           as row_count,
        sum(price)         as price_total,
        sum(freight_value) as freight_total

    from {{ ref('fct_order_items') }}

)

select *
from source_totals, fact_totals
where source_totals.row_count <> fact_totals.row_count
   or source_totals.price_total <> fact_totals.price_total
   or source_totals.freight_total <> fact_totals.freight_total
