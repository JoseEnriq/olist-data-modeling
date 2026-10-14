-- One row per order. Timestamps renamed to the *_at convention (docs/decisions.md).

with source as (

    select * from {{ source('olist', 'orders') }}

),

renamed as (

    select
        order_id,
        customer_id,
        order_status,
        cast(order_purchase_timestamp as timestamp)      as purchased_at,
        cast(order_approved_at as timestamp)             as approved_at,
        cast(order_delivered_carrier_date as timestamp)  as delivered_to_carrier_at,
        cast(order_delivered_customer_date as timestamp) as delivered_to_customer_at,
        -- No row has a time part, so this is a plain date.
        cast(order_estimated_delivery_date as date)      as estimated_delivery_date

    from source

)

select * from renamed
