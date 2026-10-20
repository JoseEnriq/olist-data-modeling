-- Question: where are deliveries late most often?
-- Late = delivered after the estimated delivery date shown to the customer.
-- States with fewer than 500 delivered orders are left out: their rates swing
-- too much with a handful of orders.

select
    locations.state,
    count(*)                                                     as delivered_orders,
    count(*) filter (where orders.is_late)                       as late_orders,
    round(100 * count(*) filter (where orders.is_late) / count(*), 1)
                                                                 as late_pct,
    round(avg(orders.days_late_vs_estimate)
          filter (where orders.is_late), 1)                      as average_days_late

from {{ ref('fct_orders') }} as orders
inner join {{ ref('dim_location') }} as locations
    on orders.delivery_location_key = locations.location_key

where orders.is_delivered
group by locations.state
having count(*) >= 500
order by late_pct desc, locations.state
