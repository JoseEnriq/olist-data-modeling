-- Orders with the keys every fact needs: the person who bought (customer_key)
-- and the delivery address as typed in the order (delivery_location_key).
-- Keys are hashes of natural keys, so they can be computed here without joining
-- the dimensions; relationship tests on the facts check that they match.

select
    orders.order_id,
    orders.customer_id,
    customers.customer_unique_id,
    {{ dbt_utils.generate_surrogate_key(['customers.customer_unique_id']) }} as customer_key,
    {{ dbt_utils.generate_surrogate_key([
        'customers.customer_zip_code_prefix',
        'customers.customer_city',
        'customers.customer_state'
    ]) }}                                    as delivery_location_key,
    orders.order_status,
    orders.purchased_at,
    orders.approved_at,
    orders.delivered_to_carrier_at,
    orders.delivered_to_customer_at,
    orders.estimated_delivery_date

from {{ ref('stg_orders') }} as orders
inner join {{ ref('stg_customers') }} as customers
    on orders.customer_id = customers.customer_id
