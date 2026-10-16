-- One row per person (customer_unique_id), not per customer_id: the source
-- creates a new customer_id for every order. The address is not here because it
-- changes from order to order; it lives in dim_location.
-- SCD type 1: the source has no history of customer attributes.

with orders as (

    select
        customers.customer_unique_id,
        orders.purchased_at

    from {{ ref('stg_orders') }} as orders
    inner join {{ ref('stg_customers') }} as customers
        on orders.customer_id = customers.customer_id

)

select
    {{ dbt_utils.generate_surrogate_key(['customer_unique_id']) }} as customer_key,
    customer_unique_id,
    min(purchased_at)                      as first_purchased_at,
    -- Month of the first purchase, the base for retention analysis.
    strftime(min(purchased_at), '%Y-%m')   as cohort_month

from orders
group by customer_unique_id
