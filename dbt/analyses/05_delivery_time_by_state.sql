-- Question: how long does delivery take in each state?
-- Delivered orders only (orders with a delivery date). Days from purchase to
-- delivery; the median is shown because a few very late orders inflate the average.

select
    locations.state,
    count(*)                                   as delivered_orders,
    round(avg(orders.days_to_deliver), 1)      as average_days,
    round(median(orders.days_to_deliver), 1)   as median_days

from {{ ref('fct_orders') }} as orders
inner join {{ ref('dim_location') }} as locations
    on orders.delivery_location_key = locations.location_key

where orders.is_delivered
group by locations.state
order by median_days
