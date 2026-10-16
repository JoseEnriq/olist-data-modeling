-- Transactional fact. Grain: one payment of an order.
-- Kept apart from the items: an order with 3 items and one payment would
-- otherwise repeat that payment 3 times.

select
    payments.order_id,
    payments.payment_sequential,
    orders.customer_key,
    {{ date_key('orders.purchased_at') }} as purchase_date_key,
    -- Degenerate dimension: 5 values and no attributes of its own.
    payments.payment_type,
    payments.payment_installments,
    payments.payment_value

from {{ ref('stg_order_payments') }} as payments
inner join {{ ref('int_orders') }} as orders
    on payments.order_id = orders.order_id
