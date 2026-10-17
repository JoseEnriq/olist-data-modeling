-- Question: how much does a customer pay per order, and did it change by year?
-- Ticket = what was actually paid for the order (payment_total, freight and
-- installment interest included), for valid orders with a payment above zero.
-- Median next to the average: a few very expensive orders pull the average up.

select
    dates.year,
    count(*)                                         as orders,
    round(avg(orders.payment_total), 2)              as average_ticket,
    round(median(orders.payment_total), 2)           as median_ticket,
    round(avg(orders.items_count), 2)                as average_items_per_order

from {{ ref('fct_orders') }} as orders
inner join {{ ref('dim_date') }} as dates
    on orders.purchase_date_key = dates.date_key

where orders.order_status not in ('canceled', 'unavailable')
  and orders.payment_total > 0
group by dates.year
order by dates.year
