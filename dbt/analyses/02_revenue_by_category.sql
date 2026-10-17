-- Question: which product categories bring the most revenue?
-- Same revenue definition as 01 (valid orders, item price only). Categories
-- keep their Portuguese names.

with category_revenue as (

    select
        products.product_category_name,
        count(*)                       as units_sold,
        sum(items.price)               as revenue

    from {{ ref('fct_order_items') }} as items
    inner join {{ ref('dim_product') }} as products
        on items.product_key = products.product_key
    where items.order_status not in ('canceled', 'unavailable')
    group by products.product_category_name

),

ranked as (

    select
        product_category_name,
        units_sold,
        revenue,
        -- Share of the total revenue, in percent (computed before keeping the top 10).
        round(100 * revenue / sum(revenue) over (), 1) as revenue_share_pct,
        row_number() over (order by revenue desc)      as revenue_rank

    from category_revenue

)

select *
from ranked
where revenue_rank <= 10
order by revenue_rank
