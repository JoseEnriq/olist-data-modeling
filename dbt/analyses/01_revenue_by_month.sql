-- Question: how did revenue and the number of orders evolve month by month?
-- Revenue = sum of item prices (freight excluded) of valid orders, i.e. not
-- canceled and not unavailable. Months at the edges of the dataset have almost
-- no orders, so the series runs from January 2017 to August 2018.

with valid_items as (

    select items.*
    from {{ ref('fct_order_items') }} as items
    where items.order_status not in ('canceled', 'unavailable')

)

select
    dates.year_month,
    count(distinct valid_items.order_id) as orders,
    sum(valid_items.price)               as revenue

from valid_items
inner join {{ ref('dim_date') }} as dates
    on valid_items.purchase_date_key = dates.date_key

where dates.year_month between '2017-01' and '2018-08'
group by dates.year_month
order by dates.year_month
