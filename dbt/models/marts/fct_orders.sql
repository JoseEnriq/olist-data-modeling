-- Accumulating snapshot. Grain: one order, with one date per milestone.
-- A null date means the order never reached that milestone.
-- Item and payment totals are summed per order before joining, so the join
-- happens at the order grain and nothing is counted twice (no fan-out).

with items as (

    select
        order_id,
        count(*)           as items_count,
        sum(price)         as items_price_total,
        sum(freight_value) as freight_total

    from {{ ref('stg_order_items') }}
    group by order_id

),

payments as (

    select
        order_id,
        sum(payment_value) as payment_total

    from {{ ref('stg_order_payments') }}
    group by order_id

)

select
    orders.order_id,
    orders.customer_key,
    orders.delivery_location_key,

    {{ date_key('orders.purchased_at') }}             as purchase_date_key,
    {{ date_key('orders.approved_at') }}              as approved_date_key,
    {{ date_key('orders.delivered_to_carrier_at') }}  as delivered_to_carrier_date_key,
    {{ date_key('orders.delivered_to_customer_at') }} as delivered_to_customer_date_key,
    {{ date_key('orders.estimated_delivery_date') }}  as estimated_delivery_date_key,

    orders.order_status,
    orders.purchased_at,
    orders.approved_at,
    orders.delivered_to_carrier_at,
    orders.delivered_to_customer_at,
    orders.estimated_delivery_date,

    -- Orders without items or payments stay in the fact with zero totals.
    coalesce(items.items_count, 0)                           as items_count,
    coalesce(items.items_price_total, 0)                     as items_price_total,
    coalesce(items.freight_total, 0)                         as freight_total,
    coalesce(payments.payment_total, 0)                      as payment_total,

    cast(date_diff('second', orders.purchased_at, orders.approved_at) / 3600
         as decimal(10, 2))                                  as hours_to_approve,
    cast(date_diff('second', orders.purchased_at, orders.delivered_to_customer_at) / 86400
         as decimal(10, 2))                                  as days_to_deliver,
    -- Whole days between the estimate and the actual delivery; positive = late.
    date_diff('day', orders.estimated_delivery_date,
              cast(orders.delivered_to_customer_at as date)) as days_late_vs_estimate,

    -- Delivered means there is a delivery date, not the status: 8 orders are
    -- "delivered" without a date and 6 have a date with another status.
    orders.delivered_to_customer_at is not null              as is_delivered,
    case
        when orders.delivered_to_customer_at is null then null
        else cast(orders.delivered_to_customer_at as date) > orders.estimated_delivery_date
    end                                                      as is_late

from {{ ref('int_orders') }} as orders
left join items
    on orders.order_id = items.order_id
left join payments
    on orders.order_id = payments.order_id
