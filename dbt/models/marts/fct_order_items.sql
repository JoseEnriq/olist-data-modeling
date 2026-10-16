-- Transactional fact. Grain: one unit of product sold in an order.
-- order_id and order_status are degenerate dimensions: they identify and filter
-- the order without a dimension table of their own.

select
    items.order_id,
    items.order_item_id,
    orders.customer_key,
    orders.delivery_location_key,
    {{ dbt_utils.generate_surrogate_key(['items.product_id']) }} as product_key,
    {{ dbt_utils.generate_surrogate_key(['items.seller_id']) }}  as seller_key,
    {{ date_key('orders.purchased_at') }}                         as purchase_date_key,
    orders.order_status,
    -- No date key: 4 items have a shipping limit in 2020, outside dim_date.
    items.shipping_limit_at,
    items.price,
    items.freight_value

from {{ ref('stg_order_items') }} as items
inner join {{ ref('int_orders') }} as orders
    on items.order_id = orders.order_id
