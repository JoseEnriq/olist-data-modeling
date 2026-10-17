-- Question: how many orders are lost to cancellation or unavailability, and
-- how does that change over time?
-- "Lost" = status canceled or unavailable. Quarterly, to smooth the monthly noise,
-- from January 2017 to August 2018 (the edges of the dataset have almost no
-- orders), so 2018 Q3 covers July and August only.

select
    dates.year,
    dates.quarter,
    count(*)                                                             as orders,
    count(*) filter (where orders.order_status = 'canceled')             as canceled,
    count(*) filter (where orders.order_status = 'unavailable')          as unavailable,
    round(100 * count(*) filter (
        where orders.order_status in ('canceled', 'unavailable')
    ) / count(*), 2)                                                     as lost_pct

from {{ ref('fct_orders') }} as orders
inner join {{ ref('dim_date') }} as dates
    on orders.purchase_date_key = dates.date_key

where dates.year_month between '2017-01' and '2018-08'
group by dates.year, dates.quarter
order by dates.year, dates.quarter
